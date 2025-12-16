import logging

from django.conf import settings
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from ally.ai.agents.consts import DEFAULT_MODEL
from ally.ai.agents.recommendations.prompt import instructions
from ally.ai.agents.recommendations.tools import (
    get_aws_guidelines,
    get_competitor_report,
    get_product_details
)
from ally.ai.agents.recommendations.callbacks import save_llm_request_callback

logger = logging.getLogger(__name__)


def recommendations_agent(product_id: str, competitor_report: str = None):
    """
    Create and return a recommendations agent configured for a specific product.

    Args:
        product_id: The product ID to generate recommendations for
        competitor_report: Optional competitor analysis report

    Returns:
        Configured Agent instance
    """
    logger.info(f'Creating recommendations agent for product: {product_id}')

    # Inject product_id and competitor report context into instructions
    contextualized_instructions = f"""
## Context for This Analysis:

You are generating optimization recommendations for product ID: **{product_id}**

"""

    if competitor_report:
        contextualized_instructions += f"""
**Competitor Analysis Available:**
A competitor analysis report is available and should be used as SECONDARY justification.

Use the function tools available to you in this order:
1. Call `get_aws_guidelines` to retrieve AWS product listing guidelines (PRIMARY source - MANDATORY)
2. Call `get_product_details` with product_id: {product_id} to get current product information
3. Call `get_competitor_report` with product_id: {product_id} to get the competitor analysis (SECONDARY source)
4. Generate exactly 3 specific, actionable recommendations

"""
    else:
        contextualized_instructions += f"""
**Note:** No competitor analysis is available yet. Focus recommendations primarily on AWS guidelines compliance.

Use the function tools available to you:
1. Call `get_aws_guidelines` to retrieve AWS product listing guidelines (PRIMARY source - MANDATORY)
2. Call `get_product_details` with product_id: {product_id} to get current product information
3. Generate exactly 3 specific, actionable recommendations based on AWS guidelines

"""

    contextualized_instructions += f"""
---

{instructions}
"""

    # Create the agent with callable function tools
    agent = Agent(
        model=LiteLlm(
            model=DEFAULT_MODEL,
            api_key=settings.GOOGLE_API_KEY
        ),
        name="recommendations_agent",
        instruction=contextualized_instructions,
        description="An expert e-commerce product optimization consultant that generates actionable recommendations based on AWS guidelines and competitive analysis.",
        tools=[get_aws_guidelines, get_product_details, get_competitor_report],
        before_model_callback=save_llm_request_callback,
    )

    logger.info('Recommendations agent created successfully')
    return agent
