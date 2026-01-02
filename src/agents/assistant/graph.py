from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.utils.tracing import logger
from src.agents.assistant.state import AssistantState
from src.agents.assistant.nodes import (
  intake_node,
  validator_node,
  continue_chat_node,
  ready_node,
  trigger_node
)

# ============================================================================
# ROUTING FUNCTIONS
# ============================================================================

def after_intake(state: AssistantState) -> Literal["validator"]:
  """After intake, always validate"""
  logger.log("ROUTING", "intake → validator", level="INFO")
  return "validator"

def after_validator(state: AssistantState) -> Literal["ready", "continue", "trigger"]:
  """
  After validation, decide next step:
  
  Decision tree:
  1. If >= 80% AND user confirmed → trigger SRS
  2. If >= 80% but NOT confirmed → ready (offer generation)
  3. If < 80% → continue (ask more questions)
  """
  score = state["validation_score"]
  is_ready = state["is_ready_for_srs"]
  user_confirmed = state["user_confirmed_generation"]
  should_trigger = state["should_trigger_srs"]
  
  logger.log("ROUTING_DECISION", 
            f"Score: {int(score*100)}% | Ready: {is_ready} | Confirmed: {user_confirmed}",
            level="INFO")
  
  # Check if user confirmed AND we're ready
  if should_trigger and user_confirmed and is_ready:
      logger.log("ROUTING", "Conditions met → trigger SRS generation", level="SUCCESS")
      return "trigger"
  
  # Check if ready but not confirmed yet
  if is_ready and not user_confirmed:
      logger.log("ROUTING", "Ready but awaiting confirmation → ready node", level="INFO")
      return "ready"
  
  # Not ready yet, continue gathering
  logger.log("ROUTING", f"Not ready ({int(score*100)}%) → continue gathering", level="INFO")
  return "continue"

def after_ready(state: AssistantState) -> Literal[END]:
  """After ready node, end and wait for user confirmation"""
  logger.log("ROUTING", "ready → END (waiting for user)", level="INFO")
  return END

def after_continue(state: AssistantState) -> Literal[END]:
  """After continue node, end and wait for more user input"""
  logger.log("ROUTING", "continue → END (waiting for user)", level="INFO")
  return END

def after_trigger(state: AssistantState) -> Literal[END]:
  """After trigger node, end (SRS generated)"""
  logger.log("ROUTING", "trigger → END (SRS complete)", level="SUCCESS")
  return END

# ============================================================================
# CREATE ASSISTANT GRAPH
# ============================================================================

def create_assistant_graph():
  """
  Build the Assistant Agent LangGraph workflow
  
  Flow:
  START → intake → validator → [ready | continue | trigger] → END
  
  Nodes:
  - intake: Extract requirements from user message
  - validator: Check 80% completeness rule
  - ready: Offer SRS generation (when >= 80%)
  - continue: Ask more questions (when < 80%)
  - trigger: Call SRS Agent (when user confirms)
  """
  
  logger.log("GRAPH_BUILD", "Building Assistant Agent graph", level="INFO")
  
  # Create graph with AssistantState (TypedDict)
  workflow = StateGraph(AssistantState)
  
  # Add nodes
  logger.log("GRAPH_BUILD", "Adding nodes: intake, validator, ready, continue, trigger", level="INFO")
  
  workflow.add_node("intake", intake_node)
  workflow.add_node("validator", validator_node)
  workflow.add_node("ready", ready_node)
  workflow.add_node("continue", continue_chat_node)
  workflow.add_node("trigger", trigger_node)
  
  # Set entry point
  workflow.set_entry_point("intake")
  logger.log("GRAPH_BUILD", "Entry point: intake", level="INFO")
  
  # ========================================================================
  # ROUTING: intake → validator
  # ========================================================================
  workflow.add_conditional_edges(
    "intake",
    after_intake,
    {
      "validator": "validator"
    }
  )
  
  # ========================================================================
  # ROUTING: validator → [ready | continue | trigger]
  # ========================================================================
  workflow.add_conditional_edges(
      "validator",
      after_validator,
      {
        "ready": "ready",
        "continue": "continue",
        "trigger": "trigger"
      }
  )
  
  # ========================================================================
  # ROUTING: ready → END
  # ========================================================================
  workflow.add_conditional_edges(
      "ready",
      after_ready,
      {
        END: END
      }
  )
  
  # ========================================================================
  # ROUTING: continue → END
  # ========================================================================
  workflow.add_conditional_edges(
      "continue",
      after_continue,
      {
        END: END
      }
  )
  
  # ========================================================================
  # ROUTING: trigger → END
  # ========================================================================
  workflow.add_conditional_edges(
      "trigger",
      after_trigger,
      {
        END: END
      }
  )
  
  # Add memory/checkpointing
  memory = MemorySaver()
  app = workflow.compile(checkpointer=memory)
  
  logger.log("GRAPH_BUILD", "Assistant Agent graph compiled successfully", level="SUCCESS")
  
  return app

# ============================================================================
# PUBLIC API: Run Assistant
# ============================================================================

def run_assistant(
  user_message: str,
  user_id: str,
  session_id: str,
  existing_state: AssistantState = None
) -> tuple[str, AssistantState]:
    """
    Run Assistant Agent and return response
    
    Args:
      user_message: User's input message
      user_id: User identifier
      session_id: Session identifier
      existing_state: Previous state (for continuing conversation)
        
    Returns:
      (assistant_response, updated_state)
    """
    logger.log("ASSISTANT_START", 
              f"Processing message from user {user_id}",
              data={"message_preview": user_message[:100]},
              level="INFO")
    
    # ========================================================================
    # STEP 1: Prepare state
    # ========================================================================
    if existing_state:
      logger.log("STATE_LOAD", "Loading existing state", level="INFO")
      state = existing_state
      state["current_message"] = user_message
    else:
      logger.log("STATE_INIT", "Initializing new state", level="INFO")
      state: AssistantState = {
        "user_id": user_id,
        "session_id": session_id,
        "current_message": user_message,
        "messages": [],
        "requirements": {},
        "validation_score": 0.0,
        "missing_categories": [],
        "is_ready_for_srs": False,
        "current_phase": "intake",
        "should_trigger_srs": False,
        "user_confirmed_generation": False,
        "srs_document": None,
        "srs_metadata": None,
        "relevant_history": [],
        "user_preferences": []
      }
    
    # ========================================================================
    # STEP 2: Check if user is confirming SRS generation
    # ========================================================================
    confirm_keywords = ["yes", "generate", "create", "proceed", "go ahead", "ok", "okay", "sure"]
    user_lower = user_message.lower()
    
    if any(keyword in user_lower for keyword in confirm_keywords):
      if state["should_trigger_srs"]:
        logger.log("USER_CONFIRMATION", "User confirmed SRS generation", level="INFO")
        state["user_confirmed_generation"] = True
    
    # ========================================================================
    # STEP 3: Create and run graph
    # ========================================================================
    logger.log("GRAPH_EXECUTION", "Creating Assistant graph", level="INFO")
    app = create_assistant_graph()
    
    config = {"configurable": {"thread_id": session_id}}
    
    logger.log("GRAPH_EXECUTION", "Starting graph execution", level="INFO")
    
    final_state = None
    for output in app.stream(state, config):
      node_name = list(output.keys())[0]
      node_state = output[node_name]
      
      logger.log("GRAPH_STEP", 
                f"Completed node: {node_name} (phase: {node_state.get('current_phase', 'unknown')})",
                level="INFO")
      
      final_state = node_state
    
    # ========================================================================
    # STEP 4: Extract response
    # ========================================================================
    if final_state and final_state.get("messages"):
      # Get last assistant message
      assistant_messages = [m for m in final_state["messages"] if m["role"] == "assistant"]
      if assistant_messages:
        response_message = assistant_messages[-1]["content"]
      else:
        response_message = "I'm ready to help! Tell me about your project."
    else:
        response_message = "I'm ready to help! Tell me about your project."
    
    logger.log("ASSISTANT_COMPLETE", 
              f"Response generated: {response_message[:100]}...",
              data={
                  "completeness": final_state.get("validation_score", 0) if final_state else 0,
                  "is_ready": final_state.get("is_ready_for_srs", False) if final_state else False
              },
              level="SUCCESS")
    
    return response_message, final_state