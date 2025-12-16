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


# Initialize the global product service instance
from django.conf import settings
product_service = ProductService(settings.PRODUCTS_FILE)
