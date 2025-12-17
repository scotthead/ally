"""
Update Product Agent

This agent is responsible for applying a single recommendation to a product.
"""

from google.adk import Agent


def update_product_agent(product_id: str, recommendation_number: int) -> Agent:
    """
    Create an agent that updates a product based on a specific recommendation.

    Args:
        product_id: The product ID to update
        recommendation_number: The recommendation number to apply (1, 2, or 3)

    Returns:
        An Agent configured to update the product
    """

    # Simple prompt for now - will be filled in with more details later
    prompt = f"""
You are a product update agent responsible for implementing recommendation #{recommendation_number} for product {product_id}.

Your task:
1. Analyze the recommendation
2. Determine the specific changes needed
3. Apply the changes to the product
4. Verify the changes were successful
5. Report on what was updated

Product ID: {product_id}
Recommendation Number: {recommendation_number}

Please pretend implementing this recommendation and return a successful response saying 'done'.
"""

    return Agent(
        model="gemini-2.0-flash-exp",
        instruction=prompt.strip(),
        name=f"update_product_agent_{recommendation_number}",
        description=f"Agent that applies recommendation #{recommendation_number} to product {product_id}"
    )
