import logging
from typing import Dict, Any
from pathlib import Path

from django.conf import settings
from ally.product_service import product_service
from ally.services import competitor_report_service
from ally.services.pdf_extractor import PDFExtractor
from ally.services.competitor_report_service import competitor_report_service

logger = logging.getLogger(__name__)


def get_aws_guidelines() -> Dict[str, Any]:
    """
    Extract and return the AWS Product Guidelines from the PDF file.

    Returns:
        Dictionary containing:
        - guidelines_text: Full text content of AWS guidelines
        - source: Path to the guidelines file
        - status: Success or error status
    """
    logger.info('Extracting AWS Product Guidelines from PDF')

    try:
        # Path to AWS guidelines PDF
        guidelines_path = Path(settings.BASE_DIR) / 'ally' / 'data' / 'AWS-Guidelines.pdf'

        if not guidelines_path.exists():
            logger.error(f'AWS Guidelines PDF not found at: {guidelines_path}')
            return {
                'error': f'AWS Guidelines file not found at {guidelines_path}',
                'status': 'error'
            }

        # Extract content with markdown tables
        guidelines_content = PDFExtractor.extract_with_markdown_tables(str(guidelines_path))

        logger.info(f'Successfully extracted AWS Guidelines ({len(guidelines_content)} characters)')

        return {
            'guidelines_text': guidelines_content,
            'source': str(guidelines_path),
            'length': len(guidelines_content),
            'status': 'success'
        }

    except Exception as e:
        logger.error(f'Error extracting AWS Guidelines: {str(e)}', exc_info=True)
        return {
            'error': f'Failed to extract guidelines: {str(e)}',
            'status': 'error'
        }


def get_competitor_report(product_id: str) -> Dict[str, Any]:
    """
    Retrieve the competitor analysis report for a product.

    Args:
        product_id: The product ID to get the competitor report for

    Returns:
        Dictionary containing:
        - report: The competitor analysis report text
        - product_id: The product ID
        - status: Success or error status
    """
    logger.info(f'Retrieving competitor report for product: {product_id}')


    competitor_report_text = competitor_report_service.get_report(product_id)
    if competitor_report_text:
        return {
            'report': competitor_report_text,
            'product_id': product_id,
            'length': len(competitor_report_text),
            'status': 'success'
        }

    return {
        'report': '',
        'product_id': product_id,
        'status': 'info',
        'message': 'No competitor report available. Recommendations will be based solely on AWS guidelines.'
    }


def get_product_details(product_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a product.

    Args:
        product_id: The product ID (ASIN) to lookup

    Returns:
        Dictionary containing product information and computed metrics
    """
    logger.info(f'Looking up product details: {product_id}')

    product = product_service.get_product_by_id(product_id)

    if not product:
        logger.warning(f'Product not found: {product_id}')
        return {
            'error': f'Product with ID {product_id} not found',
            'product_id': product_id,
            'status': 'error'
        }

    # Convert product to dictionary for the agent
    product_dict = product.model_dump()

    # Add computed fields for analysis
    product_dict['title_length'] = len(product.title) if product.title else 0
    product_dict['num_bullet_points'] = len(product.bullet_points) if product.bullet_points else 0

    if product.bullet_points:
        bullet_lengths = [len(bp) for bp in product.bullet_points]
        product_dict['avg_bullet_length'] = sum(bullet_lengths) / len(bullet_lengths)
        product_dict['total_bullet_chars'] = sum(bullet_lengths)
        product_dict['bullet_point_lengths'] = bullet_lengths
    else:
        product_dict['avg_bullet_length'] = 0
        product_dict['total_bullet_chars'] = 0
        product_dict['bullet_point_lengths'] = []

    product_dict['description_length'] = len(product.description_filled) if product.description_filled else 0
    product_dict['has_image'] = bool(product.image_url and len(product.image_url) > 0)
    product_dict['num_images'] = len(product.image_url) if product.image_url else 0

    logger.info(f'Successfully retrieved product details: {product_id}')
    return product_dict
