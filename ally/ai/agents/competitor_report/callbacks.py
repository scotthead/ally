import logging
from typing import Dict, Any, List, Tuple, cast
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.genai import types

logger = logging.getLogger(__name__)


async def save_llm_request_callback(callback_context: CallbackContext, llm_request: LlmRequest):
    """
    Save the LLM request to the InteractionSaver if available.
    """
    # Check if interaction saving is enabled and InteractionSaver is available
    try:
        # Extract data from session state (set by the caller)
        request_log = _build_request_log(llm_request)
        logger.info(f"LLM request: {request_log}")
    except Exception as e:
        logger.error(f"Error logging LLM request: {e}", exc_info=True)


def _build_function_declaration_log(
    func_decl: types.FunctionDeclaration,
) -> str:
  """Builds a function declaration log.

  Args:
    func_decl: The function declaration to convert.

  Returns:
    The function declaration log.
  """

  param_str = "{}"
  if func_decl.parameters and func_decl.parameters.properties:
    param_str = str({
        k: v.model_dump(exclude_none=True)
        for k, v in func_decl.parameters.properties.items()
    })
  return_str = "None"
  if func_decl.response:
    return_str = str(func_decl.response.model_dump(exclude_none=True))
  return f"{func_decl.name}: {param_str} -> {return_str}"

_EXCLUDED_PART_FIELD = {"inline_data": {"data"}}
_NEW_LINE = "\n"
def _build_request_log(req: LlmRequest) -> str:
  """Builds a request log.

  Args:
    req: The request to convert.

  Returns:
    The request log.
  """

  function_decls: list[types.FunctionDeclaration] = cast(
      list[types.FunctionDeclaration],
      req.config.tools[0].function_declarations if req.config.tools else [],
  )
  function_logs = (
      [
          _build_function_declaration_log(func_decl)
          for func_decl in function_decls
      ]
      if function_decls
      else []
  )
  contents_logs = [
      content.model_dump_json(
          exclude_none=True,
          exclude={
              "parts": {
                  i: _EXCLUDED_PART_FIELD for i in range(len(content.parts))
              }
          },
      )
      for content in req.contents
  ]

  return f"""
LLM Request:
-----------------------------------------------------------
System Instruction:
{req.config.system_instruction}
-----------------------------------------------------------
Contents:
{_NEW_LINE.join(contents_logs)}
-----------------------------------------------------------
Functions:
{_NEW_LINE.join(function_logs)}
-----------------------------------------------------------
"""

def before_agent_callback(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Callback function that runs before the agent starts processing.

    This callback extracts the product_id from the state and injects it
    into the agent's instructions to provide context for the analysis.

    Args:
        state: The agent state dictionary containing product_id and other context

    Returns:
        Modified state with updated instructions
    """
    product_id = state.get('product_id')

    if not product_id:
        logger.warning('No product_id found in state for competitor report agent')
        return state

    # Get the current instructions
    current_instructions = state.get('instruction', '')

    # Inject the product_id into the instructions
    injected_context = f"""
## Context for This Analysis:

You are analyzing the product with ID: **{product_id}**

Use the function tools available to you to:
1. First, lookup the source product details using `lookup_product` with product_id: {product_id}
2. Then, lookup all competitor products using `lookup_competitors` with product_id: {product_id}
3. Analyze and generate the comprehensive comparison report

---

"""

    # Prepend the context to the existing instructions
    updated_instructions = injected_context + current_instructions
    state['instruction'] = updated_instructions

    logger.info(f'Injected product_id {product_id} into agent instructions')

    return state
