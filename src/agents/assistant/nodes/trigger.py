from src.agents.assistant.state import AssistantState
from src.agents.srs.graph import create_srs_graph
from src.agents.srs.state import SRSState
from src.utils.tracing import logger

def trigger_node(state: AssistantState) -> AssistantState:
  """
  Trigger Node: Call SRS Agent and generate document
  
  ** THIS IS WHERE ASSISTANT CALLS SRS AGENT **
  """
  logger.log("NODE_START", "Trigger Node - Calling SRS Agent", level="AGENT")
  logger.log("AGENT_COMMUNICATION", "Assistant → SRS Agent", level="INFO")
  
  # ========================================================================
  # STEP 1: Format requirements for SRS Agent
  # ========================================================================
  logger.log("FORMAT_INPUT", "Formatting requirements for SRS Agent", level="INFO")
  
  project_description = _format_requirements_for_srs(state["requirements"])
  
  logger.log("FORMAT_COMPLETE", 
            f"Formatted input: {project_description[:200]}...",
            level="SUCCESS")
  
  # ========================================================================
  # STEP 2: Prepare SRS Agent initial state
  # ========================================================================
  srs_initial_state: SRSState = {
    "project_query": project_description,
    "research_results": [],
    "agent_plan": [],
    "worker_outputs": [],
    "final_srs": "",
    "current_phase": "start",
    "messages": []
  }
  
  logger.log("SRS_STATE_INIT", "Initialized SRS Agent state", 
            data={"project_query_length": len(project_description)},
            level="INFO")
  
  # ========================================================================
  # STEP 3: Create SRS Agent graph
  # ========================================================================
  logger.log("SRS_GRAPH_CREATE", "Creating SRS Agent graph", level="INFO")
  
  srs_app = create_srs_graph()
  
  logger.log("SRS_GRAPH_READY", "SRS Agent graph ready", level="SUCCESS")
  
  # ========================================================================
  # STEP 4: Run SRS Agent (Execute graph)
  # ========================================================================
  logger.log("SRS_EXECUTION_START", "Executing SRS Agent workflow", level="INFO")
  
  try:
    # Run synchronously (LangGraph stream)
    config = {"configurable": {"thread_id": f"srs_{state['session_id']}"}}
    
    final_srs_state = None
    for output in srs_app.stream(srs_initial_state, config):
      node_name = list(output.keys())[0]
      node_state = output[node_name]
      
      logger.log("SRS_NODE_COMPLETE", 
                f"SRS Agent node completed: {node_name}",
                level="INFO")
      
      final_srs_state = node_state
    
    # ====================================================================
    # STEP 5: Extract SRS result
    # ====================================================================
    if final_srs_state and final_srs_state.get("final_srs"):
      srs_document = final_srs_state["final_srs"]
      
      logger.log("SRS_SUCCESS", 
                f"SRS generated successfully - {len(srs_document)} characters",
                data={"word_count": len(srs_document.split())},
                level="SUCCESS")
      
      # Update Assistant state
      state["srs_document"] = srs_document
      state["srs_metadata"] = {
        "word_count": len(srs_document.split()),
        "generated_at": "now",
        "requirements_used": state["requirements"]
      }
      
      # Generate success message
      success_msg = f"""
        **SRS Document Generated Successfully!**

        **Statistics:**
        - Words: {len(srs_document.split())}
        - Sections: {srs_document.count('##')}

        The complete SRS document is ready! Would you like to:
        - Export it to Markdown
        - Make modifications
        - Generate a new version
      """
                    
      state["messages"].append({
        "role": "assistant",
        "content": success_msg
      })
        
    else:
      logger.log("SRS_ERROR", "SRS Agent returned no document", level="ERROR")
      
      state["messages"].append({
        "role": "assistant",
        "content": "Sorry, there was an error generating the SRS. Please try again."
      })
  
  except Exception as e:
      logger.log("SRS_EXCEPTION", f"Error calling SRS Agent: {str(e)}", level="ERROR")
      
      state["messages"].append({
        "role": "assistant",
        "content": f"Error generating SRS: {str(e)}"
      })
  
  # Update phase
  state["current_phase"] = "complete"
  
  logger.log("NODE_COMPLETE", "Trigger Node complete", level="SUCCESS")
  logger.log("AGENT_COMMUNICATION", "Assistant ← SRS Agent (complete)", level="INFO")
  
  return state


def _format_requirements_for_srs(requirements: dict) -> str:
  """
  Format requirements dict into text for SRS input
  """
  parts = []
  
  if requirements.get("project_type"):
    parts.append(f"Project Type: {', '.join(requirements['project_type'])}")
  
  if requirements.get("core_features"):
    parts.append("\nCore Features:")
    for feature in requirements["core_features"]:
      parts.append(f"- {feature}")
  
  if requirements.get("tech_stack"):
    parts.append(f"\nTechnology Stack: {', '.join(requirements['tech_stack'])}")
  
  if requirements.get("user_roles"):
    parts.append(f"\nUser Roles: {', '.join(requirements['user_roles'])}")
  
  if requirements.get("business_goals"):
    parts.append("\nBusiness Goals:")
    for goal in requirements["business_goals"]:
      parts.append(f"- {goal}")
  
  if requirements.get("non_functional"):
    parts.append("\nNon-Functional Requirements:")
    for nfr in requirements["non_functional"]:
      parts.append(f"- {nfr}")
  
  return "\n".join(parts)