import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage

from src.agents.srs.prompts import PLANNER_PROMPT
from src.utils.tracing import logger
from src.agents.srs.state import SRSState
from src.tools import tools, tavily_search

# =============================== CONFIGURATION ================================
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
llm_with_tools = llm.bind_tools(tools)

# ================================ PLANNING NODE ===============================
def planning_node(state: SRSState) -> SRSState:
  """
  Node 2: Planning phase - create agent execution plan
  """
  logger.log("NODE_START", "Planning Node", level="AGENT")
  
  project_query = state["project_query"]
  research_summary = "\n\n".join(state["research_results"])
  
  safe_prompt = PLANNER_PROMPT.replace("{", "{{").replace("}", "}}")
  safe_prompt = safe_prompt.replace("{{project_query}}", "{project_query}")
  safe_prompt = safe_prompt.replace("{{research_summary}}", "{research_summary}")

  planning_prompt = [HumanMessage(content=safe_prompt.format(
    project_query=project_query,
    research_summary=research_summary
  ))]
  
  response = llm_with_tools.invoke(planning_prompt)
  
  if response.tool_calls:
    max_tool_calls = 3
        
    if len(response.tool_calls) > max_tool_calls:
      logger.log("LIMIT_REACHED", f"LLM requested {len(response.tool_calls)} tools. Truncating to {max_tool_calls}.", level="WARNING")
      response.tool_calls = response.tool_calls[:max_tool_calls]
      
    tool_outputs = []
    for idx, tool_call in enumerate(response.tool_calls, 1):
      logger.log("PLANNER_SEARCH", f"Additional search {idx}/{len(response.tool_calls)}", level="TOOL")
      
      result = tavily_search.invoke(tool_call["args"])
      tool_outputs.append(ToolMessage(
          content=str(result), 
          tool_call_id=tool_call["id"]
      ))
    
    final_response = llm.invoke(planning_prompt + [response] + tool_outputs)
    plan_content = final_response.content
  else:
    plan_content = response.content
  
  # Parse plan
  try:
    if "```json" in plan_content:
      plan_content = plan_content.split("```json")[1].split("```")[0]
    elif "```" in plan_content:
      plan_content = plan_content.split("```")[1].split("```")[0]
    
    agent_plan = json.loads(plan_content.strip())
    
    # Validate plan structure
    if not isinstance(agent_plan, list):
      raise ValueError("Plan must be a list")
    
    # Limit to 3-5 agents
    if len(agent_plan) > 5:
      logger.log("PLAN_LIMIT", f"Plan has {len(agent_plan)} agents. Limiting to 5.", level="WARNING")
      agent_plan = agent_plan[:5]
        
    logger.log("NODE_COMPLETE", f"Planning Node - created {len(agent_plan)} agents", 
              data={"num_agents": len(agent_plan)}, level="SUCCESS")
  except Exception as e:
    logger.log("PLAN_PARSE_ERROR", f"Failed to parse plan: {str(e)}", level="ERROR")
    
    # Fallback plan
    agent_plan = [
      {
        "agent_role": "Database Architect",
        "specialty": "Data modeling and schema design",
        "task": {
          "objective": f"Design database architecture for {project_query}",
          "requirements": "Create comprehensive database schema, ER diagrams, indexing strategy",
          "context": research_summary[:1000],
          "deliverables": "Database schema, ER diagrams, indexing strategy"
        }
      },
      {
        "agent_role": "Backend Engineer",
        "specialty": "API and business logic design",
        "task": {
          "objective": f"Design backend architecture for {project_query}",
          "requirements": "API endpoints, business logic, authentication",
          "context": research_summary[:1000],
          "deliverables": "API specifications, architecture diagrams"
        }
      },
      {
        "agent_role": "Frontend Engineer",
        "specialty": "UI/UX and component architecture",
        "task": {
          "objective": f"Design frontend architecture for {project_query}",
          "requirements": "Component hierarchy, state management, user flows",
          "context": research_summary[:1000],
          "deliverables": "UI specifications, component diagrams"
        }
      }
    ]
    logger.log("NODE_WARNING", "Using fallback plan with 3 agents", level="WARNING")
  
  return {
    **state,
    "agent_plan": agent_plan,
    "current_phase": "planning_complete"
  }