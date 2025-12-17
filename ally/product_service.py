import os
import json
from typing import List, Optional, Union
import pandas as pd
from pydantic import BaseModel, Field, field_validator


class Product(BaseModel):
    """Pydantic model representing a product."""
    product_id: str
    title: str
    universe: Optional[str] = None
    image_url: Optional[List[str]] = None
    bullet_points: Optional[List[str]] = None
    min_rank_search: Optional[float] = None
    avg_rank_search: Optional[float] = None
    min_rank_category: Optional[float] = None
    avg_rank_category: Optional[float] = None
    retailer_category_node: Optional[str] = None
    retailer_brand_name: Optional[str] = None
    description_filled: Optional[str] = None
    source_product_id: Optional[str] = None

    @field_validator('image_url', mode='before')
    @classmethod
    def parse_image_url(cls, v):
        """Parse image_url from JSON string to list if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else [parsed]
            except (json.JSONDecodeError, TypeError):
                return [v]
        return v

    @field_validator('bullet_points', mode='before')
    @classmethod
    def parse_bullet_points(cls, v):
        """Parse bullet_points from JSON string to list if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else [parsed]
            except (json.JSONDecodeError, TypeError):
                return [v]
        return v

    class Config:
        frozen = False


class ProductService:
    """In-memory service for managing products loaded from CSV."""

    def __init__(self, csv_file_path: str):
        """
        Initialize the ProductService with a CSV file.

        Args:
            csv_file_path: Path to the CSV file containing product data
        """
        self.csv_file_path = csv_file_path
        self.products: List[Product] = []
        self._products_by_id: dict[str, Product] = {}

        if os.path.exists(csv_file_path):
            self.load_from_csv(csv_file_path)

    def load_from_csv(self, csv_file_path: str) -> None:
        """
        Load products from a CSV file.

        Args:
            csv_file_path: Path to the CSV file containing product data
        """
        df = pd.read_csv(csv_file_path)
        self.products = self._dataframe_to_products(df)
        self._products_by_id = {product.product_id: product for product in self.products}

    def _dataframe_to_products(self, df: pd.DataFrame) -> List[Product]:
        """
        Convert a pandas DataFrame to a list of Product objects.

        Args:
            df: DataFrame containing product data

        Returns:
            List of Product objects
        """
        products = []
        for _, row in df.iterrows():
            product_data = self._row_to_dict(row)
            product = Product(**product_data)
            products.append(product)
        return products

    def _row_to_dict(self, row: pd.Series) -> dict:
        """
        Convert a pandas Series (row) to a dictionary suitable for Product creation.
        Handles NaN values by converting them to None.

        Args:
            row: Pandas Series representing a row of data

        Returns:
            Dictionary with product data
        """
        data = row.to_dict()
        # Convert NaN values to None
        for key, value in data.items():
            if pd.isna(value):
                data[key] = None
        return data

    def get_all_products(self) -> List[Product]:
        """
        Get all products.

        Returns:
            List of all products
        """
        return self.products

    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """
        Get a product by its ID.

        Args:
            product_id: The product ID to search for

        Returns:
            Product if found, None otherwise
        """
        return self._products_by_id.get(product_id)

    def count(self) -> int:
        """
        Get the total number of products.

        Returns:
            Number of products
        """
        return len(self.products)

    def search_by_title(self, query: str) -> List[Product]:
        """
        Search products by title (case-insensitive).

        Args:
            query: Search query string

        Returns:
            List of products matching the query
        """
        query_lower = query.lower()
        return [p for p in self.products if query_lower in p.title.lower()]

    def update_product(self, product: Product) -> None:
        """
        Update a product in the service's internal data structures.
        Replaces the product in both the products list and _products_by_id dictionary.

        Args:
            product: The updated Product object

        Raises:
            ValueError: If the product doesn't exist in the service
        """
        if product.product_id not in self._products_by_id:
            raise ValueError(f"Product {product.product_id} not found in service")

        # Update in dictionary
        self._products_by_id[product.product_id] = product

        # Find and replace in products list
        for i, p in enumerate(self.products):
            if p.product_id == product.product_id:
                self.products[i] = product
                break

    def save_to_csv(self, csv_file_path: str = None) -> None:
        """
        Save all products to a CSV file.

        Args:
            csv_file_path: Path to save the CSV file (defaults to the original path)

        Raises:
            IOError: If the file cannot be written
        """
        if csv_file_path is None:
            csv_file_path = self.csv_file_path

        try:
            # Convert products to DataFrame
            products_data = []
            for product in self.products:
                product_dict = {
                    'product_id': product.product_id,
                    'title': product.title,
                    'universe': product.universe,
                    'image_url': json.dumps(product.image_url) if product.image_url else None,
                    'bullet_points': json.dumps(product.bullet_points) if product.bullet_points else None,
                    'min_rank_search': product.min_rank_search,
                    'avg_rank_search': product.avg_rank_search,
                    'min_rank_category': product.min_rank_category,
                    'avg_rank_category': product.avg_rank_category,
                    'retailer_category_node': product.retailer_category_node,
                    'retailer_brand_name': product.retailer_brand_name,
                    'description_filled': product.description_filled,
                    'source_product_id': product.source_product_id
                }
                products_data.append(product_dict)

            # Create DataFrame and save to CSV
            df = pd.DataFrame(products_data)
            df.to_csv(csv_file_path, index=False)

        except Exception as e:
            raise IOError(f"Failed to save products to CSV: {str(e)}")

    def save_and_reload(self, csv_file_path: str = None) -> None:
        """
        Save all products to CSV and then reload from the file to ensure consistency.

        Args:
            csv_file_path: Path to save the CSV file (defaults to the original path)

        Raises:
            IOError: If the file cannot be written or read
        """
        if csv_file_path is None:
            csv_file_path = self.csv_file_path

        # Save to CSV
        self.save_to_csv(csv_file_path)

        # Reload from CSV to ensure data consistency
        self.load_from_csv(csv_file_path)


class CompetitorProductService:
    """In-memory service for managing competitor products loaded from CSV."""

    def __init__(self, csv_file_path: str):
        """
        Initialize the CompetitorProductService with a CSV file.

        Args:
            csv_file_path: Path to the CSV file containing competitor product data
        """
        self.csv_file_path = csv_file_path
        self.competitors: List[Product] = []
        self._competitors_by_id: dict[str, Product] = {}
        self._competitors_by_source: dict[str, List[Product]] = {}

        if os.path.exists(csv_file_path):
            self.load_from_csv(csv_file_path)

    def load_from_csv(self, csv_file_path: str) -> None:
        """
        Load competitor products from a CSV file.

        Args:
            csv_file_path: Path to the CSV file containing competitor product data
        """
        df = pd.read_csv(csv_file_path)
        self.competitors = self._dataframe_to_products(df)
        self._competitors_by_id = {product.product_id: product for product in self.competitors}

        # Build index by source_product_id for efficient lookups
        self._competitors_by_source = {}
        for competitor in self.competitors:
            if competitor.source_product_id:
                if competitor.source_product_id not in self._competitors_by_source:
                    self._competitors_by_source[competitor.source_product_id] = []
                self._competitors_by_source[competitor.source_product_id].append(competitor)

    def _dataframe_to_products(self, df: pd.DataFrame) -> List[Product]:
        """
        Convert a pandas DataFrame to a list of Product objects.

        Args:
            df: DataFrame containing competitor product data

        Returns:
            List of Product objects
        """
        products = []
        for _, row in df.iterrows():
            product_data = self._row_to_dict(row)
            product = Product(**product_data)
            products.append(product)
        return products

    def _row_to_dict(self, row: pd.Series) -> dict:
        """
        Convert a pandas Series (row) to a dictionary suitable for Product creation.
        Handles NaN values by converting them to None.

        Args:
            row: Pandas Series representing a row of data

        Returns:
            Dictionary with product data
        """
        data = row.to_dict()
        # Convert NaN values to None
        for key, value in data.items():
            if pd.isna(value):
                data[key] = None
        return data

    def get_all_competitors(self) -> List[Product]:
        """
        Get all competitor products.

        Returns:
            List of all competitor products
        """
        return self.competitors

    def get_competitor_by_id(self, product_id: str) -> Optional[Product]:
        """
        Get a competitor product by its ID.

        Args:
            product_id: The product ID to search for

        Returns:
            Product if found, None otherwise
        """
        return self._competitors_by_id.get(product_id)

    def get_competitors_for_product(self, source_product_id: str) -> List[Product]:
        """
        Get all competitor products generated from a specific source product.

        Args:
            source_product_id: The source product ID to search for

        Returns:
            List of competitor products linked to the source product
        """
        return self._competitors_by_source.get(source_product_id, [])

    def count(self) -> int:
        """
        Get the total number of competitor products.

        Returns:
            Number of competitor products
        """
        return len(self.competitors)

    def count_by_source(self, source_product_id: str) -> int:
        """
        Get the number of competitor products for a specific source product.

        Args:
            source_product_id: The source product ID

        Returns:
            Number of competitors for the source product
        """
        return len(self._competitors_by_source.get(source_product_id, []))

    def get_all_source_product_ids(self) -> List[str]:
        """
        Get all unique source product IDs that have competitors.

        Returns:
            List of source product IDs
        """
        return list(self._competitors_by_source.keys())

    def search_by_title(self, query: str) -> List[Product]:
        """
        Search competitor products by title (case-insensitive).

        Args:
            query: Search query string

        Returns:
            List of competitor products matching the query
        """
        query_lower = query.lower()
        return [p for p in self.competitors if query_lower in p.title.lower()]

    def search_competitors_for_product(self, source_product_id: str, query: str) -> List[Product]:
        """
        Search competitor products by title for a specific source product.

        Args:
            source_product_id: The source product ID
            query: Search query string

        Returns:
            List of competitor products matching the query for the source product
        """
        competitors = self.get_competitors_for_product(source_product_id)
        query_lower = query.lower()
        return [p for p in competitors if query_lower in p.title.lower()]


# Initialize the global product service instances
from django.conf import settings
product_service = ProductService(settings.PRODUCTS_FILE)
competitor_service = CompetitorProductService(settings.COMPETITORS_FILE)
