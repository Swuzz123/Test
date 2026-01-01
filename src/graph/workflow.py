from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.graph.state import SRSState
from src.utils.tracing import logger
from src.agents.srs.nodes import research_node, planning_node, worker_node, synthesis_node

def should_continue(state: SRSState) -> str:
  phase = state.get("current_phase", "")

  if phase == "research_complete":
    return "planning"
  elif phase == "planning_complete":
    return "workers"
  elif phase == "workers_complete":
    return "synthesis"
  elif phase == "complete":
    return END
  return "research"

def create_srs_graph():
  """ Decide next step based on current phase. 
  This is where LangGraph shines - conditional routing! 
  """
  workflow = StateGraph(SRSState)

  # Add nodes
  workflow.add_node("research", research_node)
  workflow.add_node("planning", planning_node)   
  workflow.add_node("workers", worker_node)       
  workflow.add_node("synthesis", synthesis_node)

  workflow.set_entry_point("research")

  # Routing research → planning
  workflow.add_conditional_edges(
    "research",
    should_continue,
    {
      "planning": "planning",  
      "research": "research",
    }
  )

  # planning → workers
  workflow.add_conditional_edges(
    "planning",
    should_continue,
    {
      "workers": "workers",
    }
  )

  # workers → synthesis
  workflow.add_conditional_edges(
    "workers",
    should_continue,
    {
      "synthesis": "synthesis",
    }
  )

  # synthesis → END
  workflow.add_conditional_edges(
    "synthesis",
    should_continue,
    {
      END: END,
    }
  )

  memory = MemorySaver()
  app = workflow.compile(checkpointer=memory)
  return app

async def generate_srs_langgraph(project_query: str) -> str:
  """
  Generate SRS using LangGraph
  """
  logger.start_session(project_query)
  
  print("\n" + "="*80)
  print("SRS MULTI-AGENT SYSTEM - LANGGRAPH VERSION")
  print("="*80 + "\n")
  
  # Create graph
  app = create_srs_graph()
  
  # Initial state
  initial_state = {
    "project_query": project_query,
    "research_results": [],
    "agent_plan": [],
    "worker_outputs": [],
    "final_srs": "",
    "current_phase": "start",
    "messages": []
  }
  
  # Run the graph
  config = {"configurable": {"thread_id": "srs_session_1"}}
  
  logger.log("GRAPH_START", "Executing LangGraph workflow", level="INFO")
  
  final_state = None
  for output in app.stream(initial_state, config):
    # Each iteration gives us the state after a node execution
    node_name = list(output.keys())[0]
    node_state = output[node_name]
    logger.log("GRAPH_STEP", f"Completed node: {node_name}", level="INFO")
    final_state = node_state
  
  logger.log("GRAPH_COMPLETE", "LangGraph workflow finished", level="SUCCESS")
  
  return final_state["final_srs"]