import logging
import os
from pathlib import Path
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class SummarizationService:
    """Service for managing product summarizations with in-memory cache and file-based persistence."""

    def __init__(self, summarization_dir: str = None):
        """
        Initialize the SummarizationService.

        Args:
            summarization_dir: Directory to store summarization files (default: BASE_DIR/summarization)
        """
        if summarization_dir is None:
            summarization_dir = os.path.join(settings.BASE_DIR, 'summarization')

        self.summarization_dir = Path(summarization_dir)
        self._summarization_cache: dict[str, str] = {}

        # Ensure summarization directory exists
        self.summarization_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f'SummarizationService initialized with summarization directory: {self.summarization_dir}')

    def _get_summarization_file_path(self, product_id: str) -> Path:
        """
        Get the file path for a product's summarization.

        Args:
            product_id: The product ID

        Returns:
            Path object for the summarization file
        """
        filename = f'summarization_{product_id}.md'
        return self.summarization_dir / filename

    def save_summarization(self, product_id: str, summarization: str) -> None:
        """
        Save product summarization both in memory and to disk.

        Args:
            product_id: The product ID
            summarization: The product summarization content

        Raises:
            ValueError: If product_id or summarization is empty
            IOError: If file write fails
        """
        if not product_id:
            raise ValueError("product_id cannot be empty")

        if not summarization:
            raise ValueError("summarization cannot be empty")

        # Save to memory cache
        self._summarization_cache[product_id] = summarization
        logger.debug(f'Cached summarization for product: {product_id}')

        # Save to disk (overwrite if exists)
        file_path = self._get_summarization_file_path(product_id)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(summarization)
            logger.info(f'Saved summarization to: {file_path}')
        except Exception as e:
            logger.error(f'Failed to save summarization to disk: {str(e)}', exc_info=True)
            raise IOError(f'Failed to save summarization to {file_path}: {str(e)}')

    def get_summarization(self, product_id: str) -> Optional[str]:
        """
        Retrieve product summarization, checking memory cache first, then disk.

        Args:
            product_id: The product ID

        Returns:
            The product summarization content if found, None otherwise
        """
        if not product_id:
            logger.warning("get_summarization called with empty product_id")
            return None

        # Check in-memory cache first
        if product_id in self._summarization_cache:
            logger.debug(f'Retrieved summarization from cache for product: {product_id}')
            return self._summarization_cache[product_id]

        # Check file system
        file_path = self._get_summarization_file_path(product_id)

        if not file_path.exists():
            logger.debug(f'No summarization found for product: {product_id}')
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                summarization = f.read()

            # Cache it for future requests
            self._summarization_cache[product_id] = summarization
            logger.info(f'Loaded summarization from disk for product: {product_id}')
            return summarization

        except Exception as e:
            logger.error(f'Failed to load summarization from disk: {str(e)}', exc_info=True)
            return None

    def has_summarization(self, product_id: str) -> bool:
        """
        Check if summarization exists for a product.

        Args:
            product_id: The product ID

        Returns:
            True if summarization exists, False otherwise
        """
        if not product_id:
            return False

        # Check cache first
        if product_id in self._summarization_cache:
            return True

        # Check file system
        file_path = self._get_summarization_file_path(product_id)
        return file_path.exists()

    def delete_summarization(self, product_id: str) -> bool:
        """
        Delete product summarization from both memory and disk.

        Args:
            product_id: The product ID

        Returns:
            True if summarization was deleted, False if no summarization existed
        """
        if not product_id:
            return False

        deleted = False

        # Remove from cache
        if product_id in self._summarization_cache:
            del self._summarization_cache[product_id]
            deleted = True
            logger.debug(f'Removed summarization from cache for product: {product_id}')

        # Remove from disk
        file_path = self._get_summarization_file_path(product_id)
        if file_path.exists():
            try:
                file_path.unlink()
                deleted = True
                logger.info(f'Deleted summarization file: {file_path}')
            except Exception as e:
                logger.error(f'Failed to delete summarization file: {str(e)}', exc_info=True)

        return deleted

    def clear_cache(self) -> None:
        """Clear the in-memory cache of summarizations."""
        self._summarization_cache.clear()
        logger.info('Cleared summarization cache')

    def get_all_product_ids_with_summarization(self) -> list[str]:
        """
        Get all product IDs that have summarizations on disk.

        Returns:
            List of product IDs that have summarizations
        """
        product_ids = []

        try:
            for file_path in self.summarization_dir.glob('summarization_*.md'):
                # Extract product_id from filename
                filename = file_path.stem  # e.g., 'summarization_B0ABC123'
                if filename.startswith('summarization_'):
                    product_id = filename[len('summarization_'):]
                    product_ids.append(product_id)
        except Exception as e:
            logger.error(f'Failed to list summarizations: {str(e)}', exc_info=True)

        return product_ids


# Initialize the global summarization service instance
summarization_service = SummarizationService()
