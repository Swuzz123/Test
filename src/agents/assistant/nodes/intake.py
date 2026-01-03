from src.utils.tracing import logger
from src.agents.assistant.state import AssistantState
from src.agents.assistant.utils import extract_requirements, merge_requirements

def intake_node(state: AssistantState) -> AssistantState:
  """
  Intake Node: Receive message and extract requirements
  """
  logger.log("NODE_START", "Intake Node", level="AGENT")
  logger.log("INTAKE_INPUT", f"User message: {state['current_message'][:100]}...", level="INFO")
  
  # Add user message to history
  state["messages"].append({
    "role": "user",
    "content": state["current_message"]
  })
  
  # Extract requirements using LLM
  logger.log("EXTRACTION_START", "Extracting requirements from message", level="INFO")
  
  extracted = extract_requirements(
    state["current_message"],
    state["requirements"]
  )
  
  logger.log("EXTRACTION_RESULT", 
            f"Extracted {sum(len(items) for items in extracted.values())} new items",
            data={"extracted": extracted},
            level="SUCCESS")
  
  # Merge with existing requirements
  state["requirements"] = merge_requirements(state["requirements"], extracted)
  
  # Update phase
  state["current_phase"] = "extraction"
  
  logger.log("NODE_COMPLETE", "Intake Node complete", 
            data={"total_requirements": sum(len(items) for items in state["requirements"].values())},
            level="SUCCESS")
  
  return state
