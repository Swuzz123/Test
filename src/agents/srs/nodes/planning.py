import json
from src.utils.tracing import logger, observe
from src.agents.srs.state import SRSState
from src.tools import tavily_search
from src.agents.srs.prompts import PLANNER_PROMPT
from src.memory.singleton import get_memory_manager

# ================================ PLANNING NODE ===============================
@observe()
def planning_node(state: SRSState) -> SRSState:
  """
  Node 2: Planning phase - create agent execution plan
  """
  logger.log("NODE_START", "Planning Node", level="AGENT")
  
  client = get_memory_manager().get_client()
  project_query = state["project_query"]
  research_summary = "\n\n".join(state["research_results"])
  
  # Prepare Prompt
  # Note: In native client, we construct messages directly
  # Escape curly braces for JSON examples in prompt
  safe_prompt = PLANNER_PROMPT.replace("{", "{{").replace("}", "}}")
  safe_prompt = safe_prompt.replace("{{project_query}}", "{project_query}")
  safe_prompt = safe_prompt.replace("{{research_summary}}", "{research_summary}")
  
  prompt = safe_prompt.format(
    project_query=project_query,
    research_summary=research_summary
  )
  
  messages = [
      {"role": "system", "content": "You are a Lead Software Architect planning a multi-agent workflow."},
      {"role": "user", "content": prompt}
  ]
  
  # Define tools for OpenAI Native Client
  tools_schema = [
      {
          "type": "function",
          "function": {
              "name": "tavily_search",
              "description": "Search the web for technical information using Tavily.",
              "parameters": {
                  "type": "object",
                  "properties": {
                      "query": {"type": "string", "description": "Search query"},
                      "search_depth": {"type": "string", "enum": ["basic", "advanced"], "default": "advanced"}
                  },
                  "required": ["query"]
              }
          }
      }
  ]
  
  max_iterations = 3
  
  try:
    for i in range(max_iterations):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            tools=tools_schema,
            tool_choice="auto", 
            response_format={"type": "json_object"}
        )
        
        response_msg = response.choices[0].message
        
        # Check for tool calls
        if response_msg.tool_calls:
            messages.append(response_msg) # Add assistant message with tool calls
            
            for tool_call in response_msg.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                
                if func_name == "tavily_search":
                    logger.log("PLANNER_SEARCH", f"Executing search: {func_args.get('query')}", level="TOOL")
                    # Execute tool (LangChain tool invoke)
                    tool_result = tavily_search.invoke(func_args)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(tool_result)
                    })
            # Continue loop to get next response
            continue
        
        # If no tool calls, this is the final response (the JSON plan)
        plan_content = response_msg.content
        break
    else:
        # If loop finishes without break, use the last content
        plan_content = response_msg.content

    print(f"PLAN CONTENT: {plan_content}") # Debug print
    
    # Parse plan
    agent_plan = json.loads(plan_content)
    
    # If the LLM returned a wrapper key like "agents": [...], extract the list
    if isinstance(agent_plan, dict):
        if "agents" in agent_plan:
            agent_plan = agent_plan["agents"]
        elif "plan" in agent_plan:
             agent_plan = agent_plan["plan"]
        else:
            # Try to find a list value
            for key, val in agent_plan.items():
                if isinstance(val, list):
                    agent_plan = val
                    break
    
    # Validate plan structure
    if not isinstance(agent_plan, list):
       # Last ditch effort if it's still a dict but we expected a list
       logger.log("PLAN_STRUCTURE_WARNING", f"Expected list, got {type(agent_plan)}. Attempting recovery.", level="WARNING")
       # If it's a dict that looks like a single agent, wrap it
       if "agent_role" in agent_plan:
           agent_plan = [agent_plan]
       else:
           raise ValueError("Plan must be a list of agent definitions")
    
    # Limit to 3-5 agents
    if len(agent_plan) > 5:
      logger.log("PLAN_LIMIT", f"Plan has {len(agent_plan)} agents. Limiting to 5.", level="WARNING")
      agent_plan = agent_plan[:5]
        
    logger.log("NODE_COMPLETE", f"Planning Node - created {len(agent_plan)} agents", 
              data={"num_agents": len(agent_plan)}, level="SUCCESS")

  except Exception as e:
    logger.log("PLAN_PARSE_ERROR", f"Failed to generate/parse plan: {str(e)}", level="ERROR")
    
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