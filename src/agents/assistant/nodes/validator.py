from src.utils.tracing import logger
from src.utils.langfuse_tracer import trace_node
from src.agents.assistant.state import AssistantState
from src.agents.assistant.utils import calculate_completeness, is_ready_for_srs

@trace_node("validator_node")
def validator_node(state: AssistantState) -> AssistantState:
  """
  Validator Node: Calculate completeness and check 80% rule
  """
  logger.log("NODE_START", "Validator Node", level="AGENT")
  
  # Calculate completeness
  score, missing = calculate_completeness(state["requirements"])
  is_ready = is_ready_for_srs(score)
  
  logger.log("VALIDATION_RESULT",
            f"Completeness: {int(score * 100)}% | Ready: {is_ready}",
            data={
                "score": score,
                "missing_categories": missing,
                "is_ready": is_ready
            },
            level="SUCCESS")
  
  # Update state
  state["validation_score"] = score
  state["missing_categories"] = missing
  state["is_ready_for_srs"] = is_ready
  state["current_phase"] = "validation"
  
  logger.log("NODE_COMPLETE", "Validator Node complete", level="SUCCESS")
  
  return state