import logging

from django.conf import settings
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from ally.ai.agents.consts import DEFAULT_MODEL
from ally.ai.agents.competior_report.prompt import instructions
from ally.ai.agents.competior_report.tools import lookup_product, lookup_competitors
from ally.ai.agents.competior_report.callbacks import save_llm_request_callback

logger = logging.getLogger(__name__)


def competitor_report_agent(product_id: str):
    """
    Create and return a competitor report agent configured for a specific product.

    Args:
        product_id: The product ID to generate a competitor report for

    Returns:
        Configured Agent instance
    """
    logger.info(f'Creating competitor report agent for product: {product_id}')

    # Inject product_id context into instructions
    contextualized_instructions = f"""
## Context for This Analysis:

You are analyzing the product with ID: **{product_id}**

Use the function tools available to you to:
1. First, lookup the source product details using `lookup_product` with product_id: {product_id}
2. Then, lookup all competitor products using `lookup_competitors` with product_id: {product_id}
3. Analyze and generate the comprehensive comparison report

---

{instructions}
"""

    # Create the agent with callable function tools
    # Google ADK expects tools to be callable functions directly
    agent = Agent(
        model=LiteLlm(
            model=DEFAULT_MODEL,
            api_key=settings.GOOGLE_API_KEY
        ),
        name="competitor_report_agent",
        instruction=contextualized_instructions,
        description="An expert e-commerce product analyst that generates comprehensive competitor reports.",
        tools=[lookup_product, lookup_competitors],
        before_model_callback=save_llm_request_callback,
    )

    logger.info('Competitor report agent created successfully')
    return agent
