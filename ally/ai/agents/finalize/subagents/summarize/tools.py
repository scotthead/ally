"""Tools for the Summarization Agent."""

import json
from typing import Any
from ally.product_service import product_service
from ally.services.competitor_report_service import competitor_report_service
from ally.services.product_recommendation_service import product_recommendation_service


def get_product_info(product_id: str) -> str:
    """
    Retrieve detailed product information.

    Args:
        product_id: The product ID to get information for

    Returns:
        JSON string containing the product information or error
    """
    try:
        product = product_service.get_product_by_id(product_id)

        if not product:
            return json.dumps({
                "result": "failure",
                "error": f"Product {product_id} not found"
            })

        # Convert product to dictionary for JSON serialization
        product_data = {
            "product_id": product.product_id,
            "title": product.title,
            "universe": product.universe,
            "brand": product.retailer_brand_name,
            "category": product.retailer_category_node,
            "description": product.description_filled,
            "bullet_points": product.bullet_points,
            "image_url": product.image_url[0] if product.image_url else None,
            "min_rank_search": product.min_rank_search,
            "avg_rank_search": product.avg_rank_search,
            "min_rank_category": product.min_rank_category,
            "avg_rank_category": product.avg_rank_category
        }

        return json.dumps({
            "result": "success",
            "product": product_data
        })
    except Exception as e:
        return json.dumps({
            "result": "failure",
            "error": f"Error retrieving product information: {str(e)}"
        })


def get_competitor_report(product_id: str) -> str:
    """
    Retrieve the competitor analysis report for a product.

    Args:
        product_id: The product ID to get the competitor report for

    Returns:
        JSON string containing the competitor report or error
    """
    try:
        report = competitor_report_service.get_report(product_id)

        if report:
            return json.dumps({
                "result": "success",
                "report": report
            })
        else:
            return json.dumps({
                "result": "failure",
                "error": f"No competitor report found for product {product_id}"
            })
    except Exception as e:
        return json.dumps({
            "result": "failure",
            "error": f"Error retrieving competitor report: {str(e)}"
        })


def get_product_recommendations(product_id: str) -> str:
    """
    Retrieve the product recommendations report.

    Args:
        product_id: The product ID to get recommendations for

    Returns:
        JSON string containing the recommendations report or error
    """
    try:
        recommendations = product_recommendation_service.get_recommendations(product_id)

        if recommendations:
            return json.dumps({
                "result": "success",
                "recommendations": recommendations
            })
        else:
            return json.dumps({
                "result": "failure",
                "error": f"No recommendations found for product {product_id}"
            })
    except Exception as e:
        return json.dumps({
            "result": "failure",
            "error": f"Error retrieving recommendations: {str(e)}"
        })
