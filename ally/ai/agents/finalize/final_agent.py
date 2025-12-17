"""
Final Agent

This is a Sequential Agent that orchestrates the complete product finalization process.
It runs three update agents (one for each recommendation) followed by a summarization agent.
"""

from google.adk.agents.sequential_agent import SequentialAgent
from ally.ai.agents.finalize.subagents.update.update_product_agent import update_product_agent
from ally.ai.agents.finalize.subagents.summarize.summarization_agent import summarization_agent


def final_agent(product_id: str) -> SequentialAgent:
    """
    Create a sequential agent that finalizes product updates and creates a summary.

    This agent orchestrates:
    1. Update agent for recommendation #1
    2. Update agent for recommendation #2
    3. Update agent for recommendation #3
    4. Summarization agent to create final report

    Args:
        product_id: The product ID to finalize

    Returns:
        A SequentialAgent configured to run the complete finalization workflow
    """

    # Create three update agents (one for each recommendation)
    update_agent_1 = update_product_agent(product_id, recommendation_number=1)
    update_agent_2 = update_product_agent(product_id, recommendation_number=2)
    update_agent_3 = update_product_agent(product_id, recommendation_number=3)

    # Create the summarization agent
    summary_agent = summarization_agent(product_id)

    # Create the sequential agent with all four agents
    return SequentialAgent(
        sub_agents=[
            update_agent_1,
            update_agent_2,
            update_agent_3,
            summary_agent
        ],
        name="final_agent",
        description=f"Sequential agent that applies all recommendations and creates a summary for product {product_id}"
    )
