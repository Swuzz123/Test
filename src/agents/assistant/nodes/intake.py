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
  
  # Check if user says "you decide" for optional categories
  user_msg_lower = state["current_message"].lower()
    
  auto_decide_keywords = [
    "you decide", "tự bạn quyết định", "bạn quyết định", 
    "tùy bạn", "up to you", "bạn chọn", "tự chọn",
    "không biết", "don't know", "không quan tâm"
  ]
  
  if any(keyword in user_msg_lower for keyword in auto_decide_keywords):
    logger.log("AUTO_DECIDE_DETECTED", 
              "User wants AI to decide on some requirements",
              level="INFO")
    
    # Mark optional categories as "AI_DECIDE"
    _mark_optional_as_auto_decide(state)
        
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

def _mark_optional_as_auto_decide(state: AssistantState):
  """
  Mark optional categories as "AI_DECIDE"
  
  When user says "you decide", we add a placeholder to optional categories
  so validator knows we have "enough" info (AI will decide later)
  """
  from src.agents.assistant.utils.scorer import get_optional_categories
  
  optional_cats = get_optional_categories()
  
  for cat in optional_cats:
    if cat not in state["requirements"] or not state["requirements"][cat]:
      # Add placeholder
      state["requirements"][cat] = ["[AI_DECIDE]"]
      
      logger.log("AUTO_DECIDE_MARKED",
                f"Marked {cat} as AI_DECIDE",
                level="INFO")
  
  logger.log("AUTO_DECIDE_COMPLETE",
            f"Marked {len(optional_cats)} optional categories for AI decision",
            data={"categories": optional_cats},
            level="SUCCESS")