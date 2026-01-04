from src.utils.tracing import logger
from src.utils.langfuse_tracer import trace_node
from src.memory.singleton import get_memory_manager
from src.agents.assistant.state import AssistantState
from src.agents.assistant.prompts import CONTINUE_CHAT_SYSTEM, CONTINUE_CHAT_PROMPT
from src.agents.assistant.utils import get_next_category_to_ask, get_optional_categories, _detect_user_language

@trace_node("continue_chat_node")
def continue_chat_node(state: AssistantState) -> AssistantState:
  """
  Continue Chat Node: Ask user for more information
  """
  logger.log("NODE_START", "Continue Chat Node", level="AGENT")
  
  # Get client from memory manager
  client = get_memory_manager().get_client()

  # Detect user language
  user_language = _detect_user_language(state["messages"])
  logger.log("LANGUAGE_DETECT", f"Detected language: {user_language}", level="INFO")
    
  missing_cat = get_next_category_to_ask(state["missing_categories"])
  
  # Format requirements summary
  req_summary = "\n".join([
    f"- {cat}: {len(items)} items"
    for cat, items in state["requirements"].items()
    if items
  ])
  
  # Add info about optional categories
  optional_cats = get_optional_categories()
  optional_info = f"\n\nOptional categories (user can say 'you decide'): {', '.join(optional_cats)}"
  
  # Generate prompt
  prompt = CONTINUE_CHAT_PROMPT.format(
    completeness_percent=int(state["validation_score"] * 100),
    missing_category=missing_cat.replace("_", " ").title(),
    requirements_summary=req_summary if req_summary else "Nothing gathered yet"
  )
  
  logger.log("CHAT_GENERATION", f"Generating response for missing: {missing_cat}", level="INFO")
  
  # Generate response
  system_prompt = CONTINUE_CHAT_SYSTEM + f"""
    IMPORTANT: 
    - User is speaking in {user_language}
    - YOU MUST respond in {user_language}
    - Keep the same language throughout the conversation

    Optional categories: {', '.join(optional_cats)}
    If user says "you decide" or "tự quyết định đi" for these categories, that's OK.
    Just acknowledge and move to the next required category.
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
    assistant_message = response.choices[0].message.content
    
  except Exception as e:
    logger.log("CHAT_ERROR", f"Error generating response: {e}", level="ERROR")
    assistant_message = "I'm having trouble connecting to my brain right now. Could you repeat that?"

  # Add to messages
  state["messages"].append({
    "role": "assistant",
    "content": assistant_message
  })
  
  state["current_phase"] = "continue_chat"
  
  logger.log("NODE_COMPLETE", 
            f"Continue Chat Node complete - Response: {assistant_message[:100]}...",
            level="SUCCESS")
  
  return state