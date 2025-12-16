import logging
from typing import Dict, Any
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest

logger = logging.getLogger(__name__)


def before_agent_callback(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Callback function that runs before the agent starts processing.

    This callback extracts the product_id and competitor_report from the state
    and injects them into the agent's instructions.

    Args:
        state: The agent state dictionary containing product_id and competitor_report

    Returns:
        Modified state with updated instructions
    """
    product_id = state.get('product_id')
    competitor_report = state.get('competitor_report')

    if not product_id:
        logger.warning('No product_id found in state for recommendations agent')
        return state

    # Get the current instructions
    current_instructions = state.get('instruction', '')

    # Inject the product_id and competitor report context
    injected_context = f"""
## Context for This Analysis:

You are generating recommendations for product ID: **{product_id}**

"""

    if competitor_report:
        injected_context += f"""
**Competitor Analysis Report Available:**
The competitor analysis report has been generated and is available via the `get_competitor_report` tool.
Report preview (first 500 chars):
{competitor_report[:500]}...

"""
    else:
        injected_context += """
**Note:** No competitor analysis report was found in the session. You should still generate recommendations based on AWS guidelines.

"""

    injected_context += """
**Important Instructions:**
1. FIRST call `get_aws_guidelines` to retrieve the AWS product listing guidelines (MANDATORY)
2. THEN call `get_product_details` to get the current product information
3. THEN call `get_competitor_report` to get competitive context (if available)
4. Generate exactly 3 recommendations that primarily reference AWS guidelines
5. Use competitor analysis as secondary supporting evidence

---

"""

    # Prepend the context to the existing instructions
    updated_instructions = injected_context + current_instructions
    state['instruction'] = updated_instructions

    logger.info(f'Injected product_id {product_id} into recommendations agent instructions')

    return state


async def save_llm_request_callback(callback_context: CallbackContext, llm_request: LlmRequest):
    """
    Save the LLM request for debugging purposes.
    """
    try:
        logger.debug(f"LLM request for recommendations agent")
    except Exception as e:
        logger.error(f"Error logging LLM request: {e}", exc_info=True)
