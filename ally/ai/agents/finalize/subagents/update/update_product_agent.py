"""
Update Product Agent

This agent is responsible for applying a single recommendation to a product.
"""

from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm
from django.conf import settings

from ally.ai.agents.consts import DEFAULT_MODEL
from ally.ai.agents.finalize.subagents.update.prompt import UPDATE_PRODUCT_PROMPT
from ally.ai.agents.finalize.subagents.update.tools import (
    get_product_recommendations,
    update_product_title,
    update_product_description,
    update_product_category,
    update_product_brand,
    add_bullet_point,
    remove_bullet_point
)
from ally.ai.agents.competitor_report.callbacks import save_llm_request_callback


def update_product_agent(product_id: str, recommendation_number: int) -> Agent:
    """
    Create an agent that updates a product based on a specific recommendation.

    Args:
        product_id: The product ID to update
        recommendation_number: The recommendation number to apply (1, 2, or 3)

    Returns:
        An Agent configured to update the product
    """

    # Format the prompt with the product_id and recommendation_number
    prompt = UPDATE_PRODUCT_PROMPT.format(
        product_id=product_id,
        recommendation_number=recommendation_number
    )

    return Agent(
        model=LiteLlm(
            model=DEFAULT_MODEL,
            api_key=settings.GOOGLE_API_KEY
        ),
        instruction=prompt.strip(),
        name=f"update_product_agent_{recommendation_number}",
        description=f"Agent that applies recommendation #{recommendation_number} to product {product_id}",
        tools=[
            get_product_recommendations,
            update_product_title,
            update_product_description,
            update_product_category,
            update_product_brand,
            add_bullet_point,
            remove_bullet_point
        ],
        output_key=f"update_recommendation_{recommendation_number}_status",
        before_model_callback=save_llm_request_callback,
    )
