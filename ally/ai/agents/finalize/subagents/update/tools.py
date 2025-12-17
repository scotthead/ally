"""Tools for the Update Product Agent."""

import json
from ally.product_service import product_service
from ally.services.product_recommendation_service import product_recommendation_service


def get_product_recommendations(product_id: str) -> str:
    """
    Retrieve the product recommendations report for a given product.

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


def update_product_title(product_id: str, new_title: str) -> str:
    """
    Update the title of a product.

    Args:
        product_id: The product ID to update
        new_title: The new title for the product

    Returns:
        JSON string with result status
    """
    try:
        product = product_service.get_product_by_id(product_id)

        if not product:
            return json.dumps({
                "result": "failure",
                "error": f"Product {product_id} not found"
            })

        if not new_title or not new_title.strip():
            return json.dumps({
                "result": "failure",
                "error": "New title cannot be empty"
            })

        # Update the product title
        product.title = new_title.strip()

        return json.dumps({
            "result": "success",
            "message": f"Successfully updated product title to: {new_title}"
        })
    except Exception as e:
        return json.dumps({
            "result": "failure",
            "error": f"Error updating title: {str(e)}"
        })


def update_product_description(product_id: str, new_description: str) -> str:
    """
    Update the description of a product.

    Args:
        product_id: The product ID to update
        new_description: The new description for the product

    Returns:
        JSON string with result status
    """
    try:
        product = product_service.get_product_by_id(product_id)

        if not product:
            return json.dumps({
                "result": "failure",
                "error": f"Product {product_id} not found"
            })

        if not new_description or not new_description.strip():
            return json.dumps({
                "result": "failure",
                "error": "New description cannot be empty"
            })

        # Update the product description
        product.description_filled = new_description.strip()

        return json.dumps({
            "result": "success",
            "message": f"Successfully updated product description"
        })
    except Exception as e:
        return json.dumps({
            "result": "failure",
            "error": f"Error updating description: {str(e)}"
        })


def update_product_category(product_id: str, new_category: str) -> str:
    """
    Update the category of a product.

    Args:
        product_id: The product ID to update
        new_category: The new category for the product

    Returns:
        JSON string with result status
    """
    try:
        product = product_service.get_product_by_id(product_id)

        if not product:
            return json.dumps({
                "result": "failure",
                "error": f"Product {product_id} not found"
            })

        if not new_category or not new_category.strip():
            return json.dumps({
                "result": "failure",
                "error": "New category cannot be empty"
            })

        # Update the product category
        product.retailer_category_node = new_category.strip()

        return json.dumps({
            "result": "success",
            "message": f"Successfully updated product category to: {new_category}"
        })
    except Exception as e:
        return json.dumps({
            "result": "failure",
            "error": f"Error updating category: {str(e)}"
        })


def update_product_brand(product_id: str, new_brand: str) -> str:
    """
    Update the brand name of a product.

    Args:
        product_id: The product ID to update
        new_brand: The new brand name for the product

    Returns:
        JSON string with result status
    """
    try:
        product = product_service.get_product_by_id(product_id)

        if not product:
            return json.dumps({
                "result": "failure",
                "error": f"Product {product_id} not found"
            })

        if not new_brand or not new_brand.strip():
            return json.dumps({
                "result": "failure",
                "error": "New brand name cannot be empty"
            })

        # Update the product brand
        product.retailer_brand_name = new_brand.strip()

        return json.dumps({
            "result": "success",
            "message": f"Successfully updated product brand to: {new_brand}"
        })
    except Exception as e:
        return json.dumps({
            "result": "failure",
            "error": f"Error updating brand: {str(e)}"
        })


def add_bullet_point(product_id: str, bullet_point: str) -> str:
    """
    Add a new bullet point to a product.

    Args:
        product_id: The product ID to update
        bullet_point: The bullet point text to add

    Returns:
        JSON string with result status
    """
    try:
        product = product_service.get_product_by_id(product_id)

        if not product:
            return json.dumps({
                "result": "failure",
                "error": f"Product {product_id} not found"
            })

        if not bullet_point or not bullet_point.strip():
            return json.dumps({
                "result": "failure",
                "error": "Bullet point cannot be empty"
            })

        # Initialize bullet_points if None
        if product.bullet_points is None:
            product.bullet_points = []

        # Add the new bullet point
        product.bullet_points.append(bullet_point.strip())

        return json.dumps({
            "result": "success",
            "message": f"Successfully added bullet point: {bullet_point}"
        })
    except Exception as e:
        return json.dumps({
            "result": "failure",
            "error": f"Error adding bullet point: {str(e)}"
        })


def remove_bullet_point(product_id: str, bullet_point: str) -> str:
    """
    Remove an existing bullet point from a product (requires exact match).

    Args:
        product_id: The product ID to update
        bullet_point: The exact bullet point text to remove

    Returns:
        JSON string with result status
    """
    try:
        product = product_service.get_product_by_id(product_id)

        if not product:
            return json.dumps({
                "result": "failure",
                "error": f"Product {product_id} not found"
            })

        if not bullet_point or not bullet_point.strip():
            return json.dumps({
                "result": "failure",
                "error": "Bullet point cannot be empty"
            })

        # Check if product has bullet points
        if not product.bullet_points:
            return json.dumps({
                "result": "failure",
                "error": "Product has no bullet points to remove"
            })

        # Try to find and remove the exact bullet point
        bullet_to_remove = bullet_point.strip()

        if bullet_to_remove in product.bullet_points:
            product.bullet_points.remove(bullet_to_remove)
            return json.dumps({
                "result": "success",
                "message": f"Successfully removed bullet point: {bullet_point}"
            })
        else:
            return json.dumps({
                "result": "failure",
                "error": f"Cannot remove bullet point. Bullet point not found. Provided: '{bullet_to_remove}'"
            })
    except Exception as e:
        return json.dumps({
            "result": "failure",
            "error": f"Error removing bullet point: {str(e)}"
        })
