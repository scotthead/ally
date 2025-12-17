"""
Summarization Agent

This agent is responsible for creating a comprehensive summary of all product updates
and the competitive analysis process.
"""

from google.adk import Agent


def summarization_agent(product_id: str) -> Agent:
    """
    Create an agent that summarizes the entire product update process.

    Args:
        product_id: The product ID that was updated

    Returns:
        An Agent configured to create a comprehensive summary
    """

    # Simple prompt for now - will be filled in with more details later
    prompt = f"""
You are a summarization agent responsible for creating a comprehensive summary
of the product update process for product {product_id}.

Your task:
1. Review the product that was updated
2. Review the competitive analysis that was performed
3. Review all recommendations that were made
4. Review all actions that were taken on each recommendation
5. Create a comprehensive markdown report summarizing:
   - The product details
   - Key findings from competitive analysis
   - Each recommendation and the actions taken
   - Overall impact and outcomes
   - Next steps or additional considerations

Product ID: {product_id}

Please create fake markdown summary report that just says 'Report Completed'
"""

    return Agent(
        model="gemini-2.0-flash-exp",
        instruction=prompt.strip(),
        name="summarization_agent",
        description=f"Agent that creates a comprehensive summary for product {product_id}"
    )
