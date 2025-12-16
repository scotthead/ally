import logging
import asyncio
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from ally.product_service import product_service
from ally.services.agent_service import AgentService
from ally.services.competitor_report_service import competitor_report_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate product optimization recommendations using the recommendations agent'

    def add_arguments(self, parser):
        parser.add_argument(
            'product_id',
            type=str,
            help='The product ID (ASIN) to generate recommendations for'
        )
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='Optional output file path to save the recommendations'
        )
        parser.add_argument(
            '--user-id',
            type=str,
            default='default_user',
            help='User ID for the session (default: default_user)'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=300,
            help='Timeout in seconds (default: 300 / 5 minutes)'
        )

    def handle(self, *args, **options):
        product_id = options['product_id']
        output_file = options['output']
        user_id = options['user_id']
        timeout = options['timeout']

        logger.info(f'Generating recommendations for product: {product_id}')
        self.stdout.write(self.style.SUCCESS(
            f'Generating recommendations for product: {product_id}'
        ))

        # Verify the product exists
        product = product_service.get_product_by_id(product_id)
        if not product:
            self.stderr.write(
                self.style.ERROR(f'Product {product_id} not found in product service')
            )
            return

        self.stdout.write(f'Found product: {product.title}')

        # Check if a competitor report exists
        if not competitor_report_service.has_report(product_id):
            self.stdout.write('No competitor report found. Generating one first...')
            try:
                asyncio.run(
                    AgentService.run_competitor_report(
                        product_id=product_id,
                        user_id=user_id,
                        timeout_seconds=timeout
                    )
                )
                self.stdout.write(self.style.SUCCESS('Competitor report generated and saved'))
            except Exception as e:
                self.stderr.write(
                    self.style.WARNING(f'Failed to generate competitor report: {str(e)}')
                )
                self.stdout.write('Continuing with recommendations without competitor report...')
        else:
            self.stdout.write('Using existing competitor report from service')

        # Run the recommendations agent
        self.stdout.write('Running recommendations agent...')

        try:
            recommendations = asyncio.run(
                AgentService.run_recommendations(
                    product_id=product_id,
                    user_id=user_id,
                    timeout_seconds=timeout
                )
            )

            # Output the recommendations
            if not output_file:
                output_file = os.path.join(settings.BASE_DIR, 'reports', f'recommendations_{product_id}.md')
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(recommendations)
            self.stdout.write(
                self.style.SUCCESS(f'Recommendations saved to {output_file}')
            )
            logger.info(f'Recommendations saved to {output_file}')
            
            self.stdout.write('\n' + '='*80)
            self.stdout.write('PRODUCT OPTIMIZATION RECOMMENDATIONS')
            self.stdout.write('='*80 + '\n')
            self.stdout.write(recommendations)
            self.stdout.write('\n' + '='*80 + '\n')

            logger.info('Recommendations generated successfully')
            self.stdout.write(self.style.SUCCESS('Recommendations generated successfully'))

        except Exception as e:
            logger.error(f'Error generating recommendations: {str(e)}', exc_info=True)
            self.stderr.write(
                self.style.ERROR(f'Error generating recommendations: {str(e)}')
            )
            raise
