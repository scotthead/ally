import os
import json
import time
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any

from django.core.management.base import BaseCommand
from django.conf import settings
from litellm import completion
from tqdm import tqdm

from ally.product_service import product_service, Product
from ally.ai.agents.consts import MODEL_GEMINI_2_5_FLASH_LITE


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate synthetic competitor product data using Gemini API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delay',
            type=float,
            default=2.0,
            help='Delay in seconds between API requests (default: 2.0)'
        )
        parser.add_argument(
            '--competitors-per-product',
            type=int,
            default=2,
            help='Number of competitor products to generate per original product (default: 2)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of products to process (useful for testing)'
        )

    def handle(self, *args, **options):
        delay = options['delay']
        competitors_per_product = options['competitors_per_product']
        limit = options['limit']

        logger.info(f'Starting competitor data generation with {competitors_per_product} competitors per product')
        self.stdout.write(self.style.SUCCESS(
            f'Starting competitor data generation with {competitors_per_product} competitors per product...'
        ))

        # Load all products
        products = product_service.get_all_products()
        logger.info(f'Loaded {len(products)} products from CSV')

        # Limit products if specified
        if limit is not None:
            products = products[:limit]
            logger.info(f'Limited to {limit} products for processing')
            self.stdout.write(f'Limited to {limit} products for processing')

        self.stdout.write(f'Loaded {len(products)} products from CSV')

        # Generate competitors for each product
        all_competitors = []

        for product in tqdm(products, desc="Generating competitors"):
            try:
                logger.info(f'Generating competitors for product {product.product_id}: {product.title}')
                competitors = self.generate_competitors(product, competitors_per_product)
                all_competitors.extend(competitors)
                logger.info(f'Successfully generated {len(competitors)} competitors for {product.product_id}')

                # Space out requests to respect API throttling
                time.sleep(delay)

            except Exception as e:
                logger.error(f'Error generating competitors for {product.product_id}: {str(e)}', exc_info=True)
                self.stderr.write(
                    self.style.ERROR(f'Error generating competitors for {product.product_id}: {str(e)}')
                )
                continue

        # Save to CSV
        output_path = self.get_output_path()
        logger.info(f'Saving {len(all_competitors)} competitors to {output_path}')
        self.save_to_csv(all_competitors, output_path)

        logger.info(f'Successfully completed competitor generation: {len(all_competitors)} competitors saved')
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated {len(all_competitors)} competitor products and saved to {output_path}'
            )
        )

    def generate_competitors(self, product: Product, num_competitors: int) -> List[Product]:
        """Generate synthetic competitor products using Gemini API."""

        # Create a prompt for the LLM
        prompt = self.create_prompt(product, num_competitors)

        # Call Gemini through LiteLLM
        logger.debug(f'Calling Gemini API with model {MODEL_GEMINI_2_5_FLASH_LITE}')
        response = completion(
            model=MODEL_GEMINI_2_5_FLASH_LITE,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            api_key=settings.GOOGLE_API_KEY,
            temperature=0.8,
        )
        logger.debug('Received response from Gemini API')

        # Parse the response
        response_text = response.choices[0].message.content
        logger.debug(f'Response text length: {len(response_text)} characters')
        competitors_data = self.parse_response(response_text, num_competitors)
        logger.debug(f'Parsed {len(competitors_data)} competitor data entries')

        # Create Product objects
        competitors = []
        for comp_data in competitors_data:
            try:
                # Add source_product_id to link back to original product
                comp_data['source_product_id'] = product.product_id
                competitor = Product(**comp_data)
                competitors.append(competitor)
            except Exception as e:
                self.stderr.write(
                    self.style.WARNING(f'Failed to create competitor product: {str(e)}')
                )
                continue

        return competitors

    def create_prompt(self, product: Product, num_competitors: int) -> str:
        """Create a prompt for generating competitor products."""

        # Convert product to dict for display
        product_info = {
            "product_id": product.product_id,
            "title": product.title,
            "universe": product.universe,
            "bullet_points": product.bullet_points,
            "min_rank_search": product.min_rank_search,
            "avg_rank_search": product.avg_rank_search,
            "min_rank_category": product.min_rank_category,
            "avg_rank_category": product.avg_rank_category,
            "retailer_category_node": product.retailer_category_node,
            "retailer_brand_name": product.retailer_brand_name,
            "description_filled": product.description_filled
        }

        prompt = f"""Generate {num_competitors} synthetic competitor products based on the following original product. The competitors should be realistic alternatives in the same category with similar features but different brands, titles, and specifications.

Original Product:
{json.dumps(product_info, indent=2)}

Requirements:
1. Generate {num_competitors} competitor products as a JSON array
2. Each competitor must have ALL of the following fields:
   - product_id: Generate a unique ASIN-like ID (format: B0XXXXXXXXX)
   - title: A realistic product title (different brand/variant)
   - universe: Same category as the original (or leave null if original is null)
   - image_url: An empty list [] (we won't generate actual image URLs)
   - bullet_points: A list of 3-7 realistic bullet points describing features
   - min_rank_search: A number between 1-100 (can be null)
   - avg_rank_search: A number between 1-100 (can be null)
   - min_rank_category: A number between 1-50 (can be null)
   - avg_rank_category: A number between 1-50 (can be null)
   - retailer_category_node: Same or similar category as original
   - retailer_brand_name: A different, realistic brand name
   - description_filled: A 1-2 sentence product description

3. Make the competitors realistic competitors - similar product type but differentiated
4. Vary the rankings slightly to make them competitive
5. Return ONLY the JSON array, no additional text

Return format:
[
  {{
    "product_id": "B0ABC123DEF",
    "title": "...",
    "universe": "...",
    ...
  }},
  ...
]
"""
        return prompt

    def parse_response(self, response_text: str, expected_count: int) -> List[Dict[str, Any]]:
        """Parse the LLM response into a list of product dictionaries."""

        # Try to extract JSON from the response
        try:
            # Remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith('```'):
                # Remove ```json or ``` at the start and ``` at the end
                lines = text.split('\n')
                text = '\n'.join(lines[1:-1]) if len(lines) > 2 else text

            # Parse JSON
            competitors_data = json.loads(text)

            if not isinstance(competitors_data, list):
                raise ValueError("Response is not a JSON array")

            return competitors_data

        except json.JSONDecodeError as e:
            logger.error(f'Failed to parse JSON response: {str(e)}')
            logger.error(f'Response text: {response_text[:500]}...')
            self.stderr.write(
                self.style.ERROR(f'Failed to parse JSON response: {str(e)}')
            )
            self.stderr.write(f'Response: {response_text[:500]}...')
            return []

    def get_output_path(self) -> Path:
        """Get the output path for the synthetic competitors CSV."""
        # Place it in the same directory as the original CSV
        data_dir = Path(settings.PRODUCTS_FILE).parent
        return data_dir / 'synthetic_competitor_products.csv'

    def save_to_csv(self, competitors: List[Product], output_path: Path) -> None:
        """Save competitor products to CSV file."""

        if not competitors:
            self.stderr.write(self.style.WARNING('No competitors to save'))
            return

        # Define field names based on Product model
        fieldnames = [
            'product_id',
            'title',
            'universe',
            'image_url',
            'bullet_points',
            'min_rank_search',
            'avg_rank_search',
            'min_rank_category',
            'avg_rank_category',
            'retailer_category_node',
            'retailer_brand_name',
            'description_filled',
            'source_product_id'
        ]

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for competitor in competitors:
                row = competitor.model_dump()

                # Convert lists to JSON strings for CSV storage
                if row.get('image_url') and isinstance(row['image_url'], list):
                    row['image_url'] = json.dumps(row['image_url'])
                if row.get('bullet_points') and isinstance(row['bullet_points'], list):
                    row['bullet_points'] = json.dumps(row['bullet_points'])

                writer.writerow(row)

        self.stdout.write(f'Saved {len(competitors)} competitors to {output_path}')
