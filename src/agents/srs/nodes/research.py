from src.tools import tavily_search
from src.utils.tracing import logger
from src.agents.srs.state import SRSState

# ================================ RESERCH NODE ================================
def research_node(state: SRSState) -> SRSState:
  """
  Node 1: Research phase - gather information before planning
  """
  logger.log("NODE_START", "Research Node", level="AGENT")
  
  project_query = state["project_query"]
  
  # Define research queries (MAX 3 as per requirement)
  research_queries = [
    f"modern software architecture for {project_query}",
    f"best practices {project_query} 2025",
    f"tech stack recommendations {project_query}"
  ]
  
  research_results = []
  search_count = 0
  max_searches = 3
  
  for query in research_queries[:max_searches]:
    search_count += 1
    short_q = query[:350] 
    
    logger.log("RESEARCH_SEARCH", f"Search {search_count}/{max_searches}: {short_q[:50]}...", level="TOOL")
    
    result = tavily_search.invoke({"query": short_q, "search_depth": "advanced"})
    research_results.append(result)
  
  logger.log("NODE_COMPLETE", "Research Node - gathered info", 
          data={"num_searches": search_count, "max_allowed": max_searches}, level="SUCCESS")
  
  return {
    **state,  
    "research_results": research_results,
    "current_phase": "research_complete"
  }