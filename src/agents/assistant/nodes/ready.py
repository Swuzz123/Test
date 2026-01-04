from src.utils.tracing import logger
from src.utils.langfuse_tracer import trace_node
from src.memory.singleton import get_memory_manager
from src.agents.assistant.state import AssistantState
from src.agents.assistant.utils import _detect_user_language
from src.agents.assistant.prompts import READY_FOR_SRS_SYSTEM, READY_FOR_SRS_PROMPT

@trace_node("ready_node")
def ready_node(state: AssistantState) -> AssistantState:
  """
  Ready Node: Inform user they can generate SRS
  """
  logger.log("NODE_START", "Ready Node - Offering SRS generation", level="AGENT")
  
  # Get client from memory manager
  client = get_memory_manager().get_client()
  
  # Detect user language
  user_language = _detect_user_language(state["messages"])
  logger.log("LANGUAGE_DETECT", f"Detected language: {user_language}", level="INFO")
    
  # Format requirements summary
  req_summary = []
  for cat, items in state["requirements"].items():
    if items:
      req_summary.append(f"- {cat.replace('_', ' ').title()}: {', '.join(items[:3])}")
  
  req_text = "\n".join(req_summary) if req_summary else "All requirements gathered"
  
  # Generate prompt
  prompt = READY_FOR_SRS_PROMPT.format(
    completeness_percent=int(state["validation_score"] * 100),
    requirements_summary=req_text
  )
  
  logger.log("READY_MESSAGE", "Generating ready-for-SRS message", level="INFO")
  
  # Generate message
  system_prompt = READY_FOR_SRS_SYSTEM + f"""
      CRITICAL: 
    - User is speaking in {user_language}
    - YOU MUST respond in {user_language}
    - Be enthusiastic and clear
  """
  try:
    response = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
      ],
      temperature=0.7
    )
    ready_message = response.choices[0].message.content
    
  except Exception as e:
    logger.log("READY_ERROR", f"Error generating message: {e}", level="ERROR")
    ready_message = "We have gathered enough requirements. Shall we proceed to generate the SRS?"

  # Add to messages
  state["messages"].append({
    "role": "assistant",
    "content": ready_message
  })
  
  # Set flags
  state["should_trigger_srs"] = True
  state["current_phase"] = "ready_for_srs"
  
  logger.log("NODE_COMPLETE", "Ready Node complete - Awaiting user confirmation", level="SUCCESS")
  
  return state