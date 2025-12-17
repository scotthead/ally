"""
Summarization Agent

This agent is responsible for creating a comprehensive summary of all product updates
and the competitive analysis process.
"""

from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm
from django.conf import settings

from ally.ai.agents.consts import DEFAULT_MODEL
from ally.ai.agents.finalize.subagents.summarize.prompt import SUMMARIZATION_PROMPT
from ally.ai.agents.finalize.subagents.summarize.tools import (
    get_product_info,
    get_competitor_report,
    get_product_recommendations
)
from ally.ai.agents.competitor_report.callbacks import save_llm_request_callback


def summarization_agent(product_id: str) -> Agent:
    """
    Create an agent that summarizes the entire product update process.

    Args:
        product_id: The product ID that was updated

    Returns:
        An Agent configured to create a comprehensive summary
    """

    # Format the prompt with the product_id
    # The update results from previous agents will be available in the conversation history
    prompt = SUMMARIZATION_PROMPT.format(
        product_id=product_id
    )

    return Agent(
        model=LiteLlm(
            model=DEFAULT_MODEL,
            api_key=settings.GOOGLE_API_KEY
        ),
        instruction=prompt.strip(),
        name="summarization_agent",
        description=f"Agent that creates a comprehensive summary for product {product_id}",
        tools=[
            get_product_info,
            get_competitor_report,
            get_product_recommendations
        ],
        before_model_callback=save_llm_request_callback,
    )
