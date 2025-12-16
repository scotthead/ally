import logging
import os
from pathlib import Path
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class ProductRecommendationService:
    """Service for managing product recommendations with in-memory cache and file-based persistence."""

    def __init__(self, recommendations_dir: str = None):
        """
        Initialize the ProductRecommendationService.

        Args:
            recommendations_dir: Directory to store recommendation files (default: BASE_DIR/recommendations)
        """
        if recommendations_dir is None:
            recommendations_dir = os.path.join(settings.BASE_DIR, 'recommendations')

        self.recommendations_dir = Path(recommendations_dir)
        self._recommendations_cache: dict[str, str] = {}

        # Ensure recommendations directory exists
        self.recommendations_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f'ProductRecommendationService initialized with recommendations directory: {self.recommendations_dir}')

    def _get_recommendation_file_path(self, product_id: str) -> Path:
        """
        Get the file path for a product's recommendations.

        Args:
            product_id: The product ID

        Returns:
            Path object for the recommendation file
        """
        filename = f'recommendations_{product_id}.md'
        return self.recommendations_dir / filename

    def save_recommendations(self, product_id: str, recommendations: str) -> None:
        """
        Save product recommendations both in memory and to disk.

        Args:
            product_id: The product ID
            recommendations: The product recommendations content

        Raises:
            ValueError: If product_id or recommendations is empty
            IOError: If file write fails
        """
        if not product_id:
            raise ValueError("product_id cannot be empty")

        if not recommendations:
            raise ValueError("recommendations cannot be empty")

        # Save to memory cache
        self._recommendations_cache[product_id] = recommendations
        logger.debug(f'Cached recommendations for product: {product_id}')

        # Save to disk (overwrite if exists)
        file_path = self._get_recommendation_file_path(product_id)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(recommendations)
            logger.info(f'Saved recommendations to: {file_path}')
        except Exception as e:
            logger.error(f'Failed to save recommendations to disk: {str(e)}', exc_info=True)
            raise IOError(f'Failed to save recommendations to {file_path}: {str(e)}')

    def get_recommendations(self, product_id: str) -> Optional[str]:
        """
        Retrieve product recommendations, checking memory cache first, then disk.

        Args:
            product_id: The product ID

        Returns:
            The product recommendations content if found, None otherwise
        """
        if not product_id:
            logger.warning("get_recommendations called with empty product_id")
            return None

        # Check in-memory cache first
        if product_id in self._recommendations_cache:
            logger.debug(f'Retrieved recommendations from cache for product: {product_id}')
            return self._recommendations_cache[product_id]

        # Check file system
        file_path = self._get_recommendation_file_path(product_id)

        if not file_path.exists():
            logger.debug(f'No recommendations found for product: {product_id}')
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                recommendations = f.read()

            # Cache it for future requests
            self._recommendations_cache[product_id] = recommendations
            logger.info(f'Loaded recommendations from disk for product: {product_id}')
            return recommendations

        except Exception as e:
            logger.error(f'Failed to load recommendations from disk: {str(e)}', exc_info=True)
            return None

    def has_recommendations(self, product_id: str) -> bool:
        """
        Check if recommendations exist for a product.

        Args:
            product_id: The product ID

        Returns:
            True if recommendations exist, False otherwise
        """
        if not product_id:
            return False

        # Check cache first
        if product_id in self._recommendations_cache:
            return True

        # Check file system
        file_path = self._get_recommendation_file_path(product_id)
        return file_path.exists()

    def delete_recommendations(self, product_id: str) -> bool:
        """
        Delete product recommendations from both memory and disk.

        Args:
            product_id: The product ID

        Returns:
            True if recommendations were deleted, False if no recommendations existed
        """
        if not product_id:
            return False

        deleted = False

        # Remove from cache
        if product_id in self._recommendations_cache:
            del self._recommendations_cache[product_id]
            deleted = True
            logger.debug(f'Removed recommendations from cache for product: {product_id}')

        # Remove from disk
        file_path = self._get_recommendation_file_path(product_id)
        if file_path.exists():
            try:
                file_path.unlink()
                deleted = True
                logger.info(f'Deleted recommendations file: {file_path}')
            except Exception as e:
                logger.error(f'Failed to delete recommendations file: {str(e)}', exc_info=True)

        return deleted

    def clear_cache(self) -> None:
        """Clear the in-memory cache of recommendations."""
        self._recommendations_cache.clear()
        logger.info('Cleared recommendations cache')

    def get_all_product_ids_with_recommendations(self) -> list[str]:
        """
        Get all product IDs that have recommendations on disk.

        Returns:
            List of product IDs that have recommendations
        """
        product_ids = []

        try:
            for file_path in self.recommendations_dir.glob('recommendations_*.md'):
                # Extract product_id from filename
                filename = file_path.stem  # e.g., 'recommendations_B0ABC123'
                if filename.startswith('recommendations_'):
                    product_id = filename[len('recommendations_'):]
                    product_ids.append(product_id)
        except Exception as e:
            logger.error(f'Failed to list recommendations: {str(e)}', exc_info=True)

        return product_ids


# Initialize the global product recommendation service instance
product_recommendation_service = ProductRecommendationService()
