from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.utils.tracing import logger
from src.agents.assistant.state import AssistantState
from src.agents.assistant.utils import get_next_category_to_ask
from prompts import CONTINUE_CHAT_SYSTEM, CONTINUE_CHAT_PROMPT

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

def continue_chat_node(state: AssistantState) -> AssistantState:
  """
  Continue Chat Node: Ask user for more information
  """
  logger.log("NODE_START", "Continue Chat Node", level="AGENT")
  
  # Get missing category
  missing_cat = get_next_category_to_ask(state["missing_categories"])
  
  # Format requirements summary
  req_summary = "\n".join([
    f"- {cat}: {len(items)} items"
    for cat, items in state["requirements"].items()
    if items
  ])
  
  # Generate prompt
  prompt = CONTINUE_CHAT_PROMPT.format(
    completeness_percent=int(state["validation_score"] * 100),
    missing_category=missing_cat.replace("_", " ").title(),
    requirements_summary=req_summary if req_summary else "Nothing gathered yet"
  )
  
  logger.log("CHAT_GENERATION", f"Generating response for missing: {missing_cat}", level="INFO")
  
  # Generate response
  response = llm.invoke([
    SystemMessage(content=CONTINUE_CHAT_SYSTEM),
    HumanMessage(content=prompt)
  ])
  
  assistant_message = response.content
  
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