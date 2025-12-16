import logging
import os
from pathlib import Path
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class CompetitorReportService:
    """Service for managing competitor reports with in-memory cache and file-based persistence."""

    def __init__(self, reports_dir: str = None):
        """
        Initialize the CompetitorReportService.

        Args:
            reports_dir: Directory to store report files (default: BASE_DIR/reports)
        """
        if reports_dir is None:
            reports_dir = os.path.join(settings.BASE_DIR, 'reports')

        self.reports_dir = Path(reports_dir)
        self._reports_cache: dict[str, str] = {}

        # Ensure reports directory exists
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f'CompetitorReportService initialized with reports directory: {self.reports_dir}')

    def _get_report_file_path(self, product_id: str) -> Path:
        """
        Get the file path for a product's competitor report.

        Args:
            product_id: The product ID

        Returns:
            Path object for the report file
        """
        filename = f'competitive_report_{product_id}.md'
        return self.reports_dir / filename

    def save_report(self, product_id: str, report: str) -> None:
        """
        Save a competitor report both in memory and to disk.

        Args:
            product_id: The product ID
            report: The competitor report content

        Raises:
            ValueError: If product_id or report is empty
            IOError: If file write fails
        """
        if not product_id:
            raise ValueError("product_id cannot be empty")

        if not report:
            raise ValueError("report cannot be empty")

        # Save to memory cache
        self._reports_cache[product_id] = report
        logger.debug(f'Cached competitor report for product: {product_id}')

        # Save to disk (overwrite if exists)
        file_path = self._get_report_file_path(product_id)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f'Saved competitor report to: {file_path}')
        except Exception as e:
            logger.error(f'Failed to save competitor report to disk: {str(e)}', exc_info=True)
            raise IOError(f'Failed to save report to {file_path}: {str(e)}')

    def get_report(self, product_id: str) -> Optional[str]:
        """
        Retrieve a competitor report, checking memory cache first, then disk.

        Args:
            product_id: The product ID

        Returns:
            The competitor report content if found, None otherwise
        """
        if not product_id:
            logger.warning("get_report called with empty product_id")
            return None

        # Check in-memory cache first
        if product_id in self._reports_cache:
            logger.debug(f'Retrieved competitor report from cache for product: {product_id}')
            return self._reports_cache[product_id]

        # Check file system
        file_path = self._get_report_file_path(product_id)

        if not file_path.exists():
            logger.debug(f'No competitor report found for product: {product_id}')
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                report = f.read()

            # Cache it for future requests
            self._reports_cache[product_id] = report
            logger.info(f'Loaded competitor report from disk for product: {product_id}')
            return report

        except Exception as e:
            logger.error(f'Failed to load competitor report from disk: {str(e)}', exc_info=True)
            return None

    def has_report(self, product_id: str) -> bool:
        """
        Check if a competitor report exists for a product.

        Args:
            product_id: The product ID

        Returns:
            True if a report exists, False otherwise
        """
        if not product_id:
            return False

        # Check cache first
        if product_id in self._reports_cache:
            return True

        # Check file system
        file_path = self._get_report_file_path(product_id)
        return file_path.exists()

    def delete_report(self, product_id: str) -> bool:
        """
        Delete a competitor report from both memory and disk.

        Args:
            product_id: The product ID

        Returns:
            True if a report was deleted, False if no report existed
        """
        if not product_id:
            return False

        deleted = False

        # Remove from cache
        if product_id in self._reports_cache:
            del self._reports_cache[product_id]
            deleted = True
            logger.debug(f'Removed competitor report from cache for product: {product_id}')

        # Remove from disk
        file_path = self._get_report_file_path(product_id)
        if file_path.exists():
            try:
                file_path.unlink()
                deleted = True
                logger.info(f'Deleted competitor report file: {file_path}')
            except Exception as e:
                logger.error(f'Failed to delete competitor report file: {str(e)}', exc_info=True)

        return deleted

    def clear_cache(self) -> None:
        """Clear the in-memory cache of reports."""
        self._reports_cache.clear()
        logger.info('Cleared competitor report cache')

    def get_all_product_ids_with_reports(self) -> list[str]:
        """
        Get all product IDs that have competitor reports on disk.

        Returns:
            List of product IDs that have reports
        """
        product_ids = []

        try:
            for file_path in self.reports_dir.glob('competitive_report_*.md'):
                # Extract product_id from filename
                filename = file_path.stem  # e.g., 'competitive_report_B0ABC123'
                if filename.startswith('competitive_report_'):
                    product_id = filename[len('competitive_report_'):]
                    product_ids.append(product_id)
        except Exception as e:
            logger.error(f'Failed to list reports: {str(e)}', exc_info=True)

        return product_ids


# Initialize the global competitor report service instance
competitor_report_service = CompetitorReportService()
