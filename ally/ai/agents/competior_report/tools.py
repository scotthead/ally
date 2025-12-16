import logging
from typing import Optional, List, Dict, Any

from ally.product_service import product_service, competitor_service, Product

logger = logging.getLogger(__name__)


def lookup_product(product_id: str) -> Dict[str, Any]:
    """
    Lookup a product by its product ID (ASIN) from the product service.

    Returns detailed product information including title, bullet points, description,
    rankings, and computed metrics such as title length, number of bullet points,
    average bullet point length, and description length.

    Args:
        product_id: The product ID (ASIN) to lookup, e.g., 'B0BGR4FTZS'

    Returns:
        Dictionary containing product information with all fields and computed metrics,
        or an error message if the product is not found
    """
    logger.info(f'Looking up product: {product_id}')

    product = product_service.get_product_by_id(product_id)

    if not product:
        logger.warning(f'Product not found: {product_id}')
        return {
            'error': f'Product with ID {product_id} not found',
            'product_id': product_id
        }

    # Convert product to dictionary for the agent
    product_dict = product.model_dump()

    # Add some computed fields for analysis
    product_dict['title_length'] = len(product.title) if product.title else 0
    product_dict['num_bullet_points'] = len(product.bullet_points) if product.bullet_points else 0

    if product.bullet_points:
        bullet_lengths = [len(bp) for bp in product.bullet_points]
        product_dict['avg_bullet_length'] = sum(bullet_lengths) / len(bullet_lengths)
        product_dict['total_bullet_chars'] = sum(bullet_lengths)
    else:
        product_dict['avg_bullet_length'] = 0
        product_dict['total_bullet_chars'] = 0

    product_dict['description_length'] = len(product.description_filled) if product.description_filled else 0

    logger.info(f'Successfully retrieved product: {product_id}')
    return product_dict


def lookup_competitors(product_id: str) -> Dict[str, Any]:
    """
    Lookup all competitor products for a given source product ID.

    Returns a list of competitor products with their details and computed metrics
    for comparison. Each competitor includes the same fields as the source product
    plus computed analysis metrics.

    Args:
        product_id: The source product ID (ASIN) to find competitors for, e.g., 'B0BGR4FTZS'

    Returns:
        Dictionary containing:
        - source_product_id: The source product ID
        - num_competitors: Total number of competitors found
        - competitors: List of competitor product dictionaries with all details and metrics
        - message: Information message if no competitors are found
    """
    logger.info(f'Looking up competitors for product: {product_id}')

    competitors = competitor_service.get_competitors_for_product(product_id)

    if not competitors:
        logger.warning(f'No competitors found for product: {product_id}')
        return {
            'source_product_id': product_id,
            'num_competitors': 0,
            'competitors': [],
            'message': f'No competitors found for product {product_id}'
        }

    # Convert competitors to dictionaries with computed fields
    competitors_data = []
    for competitor in competitors:
        comp_dict = competitor.model_dump()

        # Add computed fields for analysis
        comp_dict['title_length'] = len(competitor.title) if competitor.title else 0
        comp_dict['num_bullet_points'] = len(competitor.bullet_points) if competitor.bullet_points else 0

        if competitor.bullet_points:
            bullet_lengths = [len(bp) for bp in competitor.bullet_points]
            comp_dict['avg_bullet_length'] = sum(bullet_lengths) / len(bullet_lengths)
            comp_dict['total_bullet_chars'] = sum(bullet_lengths)
        else:
            comp_dict['avg_bullet_length'] = 0
            comp_dict['total_bullet_chars'] = 0

        comp_dict['description_length'] = len(competitor.description_filled) if competitor.description_filled else 0

        competitors_data.append(comp_dict)

    result = {
        'source_product_id': product_id,
        'num_competitors': len(competitors),
        'competitors': competitors_data
    }

    logger.info(f'Successfully retrieved {len(competitors)} competitors for product: {product_id}')
    return result
