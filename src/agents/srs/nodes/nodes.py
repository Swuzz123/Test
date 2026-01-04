import os
import json
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage

from src.utils.tracing import logger
from agents.srs.state import SRSState
from src.agents.srs.prompts import (
  PLANNER_PROMPT, 
  WORKER_PROMPT_TEMPLATE, 
  SYNTHESIS_PROMPT
)
from tools import tools, tavily_search

# =============================== CONFIGURATION ================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
llm_with_tools = llm.bind_tools(tools)

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

# ================================ WORKER NODE =================================
def worker_node(state: SRSState) -> SRSState:
  """
  Node 3: Worker execution - run all sub-agents
  This node handles parallel execution internally
  """
  logger.log("NODE_START", "Worker Node - parallel execution", level="AGENT")
  
  agent_plan = state["agent_plan"]
  
  def run_single_worker(agent_config: Dict, index: int) -> Dict:
    role = agent_config.get("agent_role", "Generic Agent")
    specialty = agent_config.get("specialty", "")
    task = agent_config.get("task", {})
    
    logger.log("WORKER_START", f"Agent #{index}: {role}", level="AGENT")
    
    # Format worker prompt
    task_format = json.dumps(task, indent=2) if isinstance(task, dict) else str(task)
    
    worker_prompt = WORKER_PROMPT_TEMPLATE.format(
      role=role,
      specialty=specialty,
      task=task_format
    )
    
    response = llm.invoke([HumanMessage(content=worker_prompt)])
    output_text = response.content
    
    logger.log("WORKER_COMPLETE", f"Agent #{index}: {role} done", level="SUCCESS")
    
    return {
      "agent_index": index,
      "role": role,
      "output": output_text
    }
  
  worker_outputs = []
  for idx, agent in enumerate(agent_plan, 1):
    output = run_single_worker(agent, idx)
    worker_outputs.append(output)
    
  logger.log("NODE_COMPLETE", f"Worker Node - {len(worker_outputs)} agents completed", 
            data={"num_workers": len(worker_outputs)}, level="SUCCESS")
  
  return {
    **state,
    "worker_outputs": worker_outputs,
    "current_phase": "workers_complete"
  }

# =============================== SYNTHESIZE NODE ==============================
def synthesis_node(state: SRSState) -> SRSState:
  """
  Node 4: Synthesis - create final SRS document
  """
  logger.log("NODE_START", "Synthesis Node", level="AGENT")
  
  project_query = state["project_query"]
  worker_outputs = state["worker_outputs"]
  
  # Format worker prompt
  worker_outputs_format = json.dumps(worker_outputs, indent=2, ensure_ascii=False)
  
  synthesis_prompt = SYNTHESIS_PROMPT.format(
    project_query=project_query, 
    worker_outputs=worker_outputs_format
  )
  
  response = llm.invoke([HumanMessage(content=synthesis_prompt)])
  final_srs = response.content
  
  logger.log("NODE_COMPLETE", "Synthesis Node - SRS generated", 
            data={"doc_length": len(final_srs)}, level="SUCCESS")
  
  return {
    **state,
    "final_srs": final_srs,
    "current_phase": "complete"
  }