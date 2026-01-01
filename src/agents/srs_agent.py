import os
import re
import glob
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Dict

from openai import OpenAI
from tavily import TavilyClient

from .tools import tavily_tools
from src.utils.tracing import logger
from src.utils.prompt_manager import PLANNER_PROMPT, SYNTHESIS_PROMPT, WORKER_PROMPT_TEMPLATE

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# ============================================================================
# TAVILY SEARCH INTEGRATION
# ============================================================================
def search_with_tavily(query: str, search_depth: str = "advanced") -> str:
  """
  Real search using Tavily API
  
  Args:
    query: Search query
    search_depth: 'basic' or 'advanced'
  """
  logger.log("TOOL_CALL", f"Tavily Search: {query}", 
            data={"search_depth": search_depth}, level="TOOL")
  
  try:
      response = tavily_client.search(
        query=query,
        search_depth=search_depth,
        max_results=5
      )
      
      # Extract relevant information
      results = []
      for result in response.get('results', []):
          results.append({
            "title": result.get('title', ''),
            "url": result.get('url', ''),
            "content": result.get('content', '')[:500] 
          })
      
      formatted_results = "\n\n".join([
        f"**{r['title']}**\nURL: {r['url']}\n{r['content']}"
        for r in results
      ])
      
      logger.log("TOOL_RESPONSE", f"Tavily returned {len(results)} results", 
                data={"num_results": len(results)}, level="TOOL")
      
      return formatted_results if formatted_results else "No results found."
      
  except Exception as e:
    logger.log("TOOL_ERROR", f"Tavily search failed: {str(e)}", 
              data={"error": str(e)}, level="ERROR")
    return f"Search error: {str(e)}"
      
# ============================================================================
# LLM CALL WITH TOOL HANDLING
# ============================================================================
async def call_llm_with_tools(
    prompt: str,
    system_prompt: str,
    agent_name: str,
    use_tools: bool = True,
    max_iterations: int = 10
) -> str:
    """
    Call OpenAI with proper tool handling and logging
    """
    logger.log("LLM_CALL", f"Agent '{agent_name}' processing request", 
              data={"use_tools": use_tools}, level="AGENT")
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    iterations = 0
    tool_calls_made = []
    
    while iterations < max_iterations:
        iterations += 1
        
        api_params = {
            "model": "gpt-4o-mini",
            "max_tokens": 4000,
            "messages": messages,
            "temperature": 0.7
        }
        
        if use_tools:
            api_params["tools"] = tavily_tools
            api_params["tool_choice"] = "auto"
        
        try:
            response = client.chat.completions.create(**api_params)
            message = response.choices[0].message
            
            # Handle tool calls
            if message.tool_calls:
                logger.log("TOOL_DECISION", 
                          f"Agent '{agent_name}' decided to use {len(message.tool_calls)} tool(s)", 
                          level="TOOL")
                
                # Add assistant message
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in message.tool_calls
                    ]
                })
                
                # Execute tools
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    tool_calls_made.append({
                        "function": function_name,
                        "arguments": function_args
                    })
                    
                    # Execute Tavily search
                    if function_name == "tavily_search":
                        query = function_args.get("query", "")
                        search_depth = function_args.get("search_depth", "advanced")
                        tool_result = search_with_tavily(query, search_depth)
                    else:
                        tool_result = "Unknown tool"
                    
                    # Add tool result
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                
                continue  # Get next response
            
            # No more tool calls, return final response
            logger.log("LLM_COMPLETE", 
                      f"Agent '{agent_name}' completed after {iterations} iteration(s)", 
                      data={
                          "iterations": iterations,
                          "tools_used": len(tool_calls_made),
                          "tool_calls": tool_calls_made
                      }, 
                      level="SUCCESS")
            
            return message.content if message.content else ""
            
        except Exception as e:
            logger.log("LLM_ERROR", f"Error in agent '{agent_name}': {str(e)}", 
                      data={"error": str(e)}, level="ERROR")
            return f"Error: {str(e)}"
    
    return "Max iterations reached. Unable to complete."

# ============================================================================
# AGENT IMPLEMENTATIONS
# ============================================================================
async def planner_agent(user_query: str) -> List[Dict]:
    """
    Phase 1: Planning Agent with research capabilities
    """
    logger.start_phase("PLANNING")
    logger.log("PLANNER_START", f"Planning for: {user_query}", level="AGENT")
    
    planning_prompt = f"""
      Project Request: {user_query}

      STEP 1: Research the project requirements
      - Search for relevant architecture patterns
      - Find best practices for the domain
      - Look for similar systems and case studies
      - Gather technical recommendations

      STEP 2: After research, create a detailed execution plan
      - Design 3-5 specialized agents
      - Assign specific, actionable tasks
      - Provide full context to each agent

      Return ONLY the JSON array of agent tasks.
    """
    
    response = await call_llm_with_tools(
        prompt=planning_prompt,
        system_prompt=PLANNER_PROMPT,
        agent_name="Planner",
        use_tools=True,
        max_iterations=15
    )
    
    # Parse JSON response
    try:
        json_str = response.strip()
        
        # Remove markdown code blocks
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]
        
        json_str = json_str.strip()
        
        plan = json.loads(json_str)
        logger.log("PLANNER_SUCCESS", f"Created {len(plan)} agent tasks", 
                  data={"num_agents": len(plan)}, level="SUCCESS")
        logger.end_phase("PLANNING")
        return plan
        
    except Exception as e:
        logger.log("PLANNER_ERROR", f"Failed to parse plan: {str(e)}", 
                  data={"raw_response": response[:500]}, level="ERROR")
        
        # Fallback plan
        fallback_plan = [
            {
                "agent_role": "Full Stack Architect",
                "specialty": "End-to-end system design",
                "task": {
                    "objective": f"Design complete system for: {user_query}",
                    "requirements": "Create comprehensive architecture covering all aspects",
                    "context": user_query,
                    "deliverables": "Complete system specification"
                }
            }
        ]
        
        logger.log("PLANNER_FALLBACK", "Using fallback plan", level="WARNING")
        logger.end_phase("PLANNING")
        return fallback_plan

async def worker_agent(agent_config: Dict, agent_index: int) -> Dict:
    """
    Phase 2: Specialized worker agent
    """
    role = agent_config.get("agent_role", "Generic Engineer")
    specialty = agent_config.get("specialty", "General")
    task = agent_config.get("task", {})
    
    logger.log("WORKER_START", f"Agent #{agent_index} ({role}) starting work", level="AGENT")
    
    task_details = json.dumps(task, indent=2)
    
    worker_prompt = WORKER_PROMPT_TEMPLATE.format(
        role=role,
        specialty=specialty,
        task_details=task_details
    )
    
    result = await call_llm_with_tools(
        prompt=f"Execute your assigned task:\n\n{task_details}",
        system_prompt=worker_prompt,
        agent_name=f"{role} (#{agent_index})",
        use_tools=True,
        max_iterations=10
    )
    
    logger.log("WORKER_COMPLETE", f"Agent #{agent_index} ({role}) completed work", 
              data={"output_length": len(result)}, level="SUCCESS")
    
    return {
        "agent_index": agent_index,
        "role": role,
        "specialty": specialty,
        "task": task,
        "output": result
    }

async def synthesizer_agent(project_query: str, agent_results: List[Dict]) -> str:
    """
    Phase 3: Synthesize all results into final SRS
    """
    logger.start_phase("SYNTHESIS")
    logger.log("SYNTHESIZER_START", "Synthesizing final SRS document", level="AGENT")
    
    synthesis_input = f"""
      PROJECT: {project_query}

      AGENT OUTPUTS TO SYNTHESIZE:
      {json.dumps(agent_results, indent=2)}

      Create a comprehensive, professional SRS document that integrates all agent outputs.
    """
    
    final_srs = await call_llm_with_tools(
        prompt=synthesis_input,
        system_prompt=SYNTHESIS_PROMPT,
        agent_name="Synthesizer",
        use_tools=False,
        max_iterations=3
    )
    
    logger.log("SYNTHESIZER_COMPLETE", "Final SRS document generated", 
              data={"document_length": len(final_srs)}, level="SUCCESS")
    logger.end_phase("SYNTHESIS")
    
    return final_srs
  
# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================
async def generate_srs(project_query: str) -> str:
    """
    Main orchestration function
    """
    logger.start_session(project_query)
    
    print("\n" + "="*80)
    print("SRS MULTI-AGENT SYSTEM - EXECUTION LOG")
    print("="*80 + "\n")
    
    # Phase 1: Planning
    plan = await planner_agent(project_query)
    
    # Phase 2: Parallel Worker Execution
    logger.start_phase("WORKER_EXECUTION")
    logger.log("WORKERS_START", f"Spawning {len(plan)} worker agents in parallel", level="INFO")
    
    worker_tasks = [
        worker_agent(agent_config, idx)
        for idx, agent_config in enumerate(plan, 1)
    ]
    
    agent_results = await asyncio.gather(*worker_tasks)
    
    logger.log("WORKERS_COMPLETE", f"All {len(agent_results)} workers completed", level="SUCCESS")
    logger.end_phase("WORKER_EXECUTION")
    
    # Phase 3: Synthesis
    final_srs = await synthesizer_agent(project_query, agent_results)
    
    return final_srs
  
# ============================================================================
# MARKDOWN EXPORT
# ============================================================================
def export_to_markdown(srs_content: str) -> str:
    """
    Export SRS to markdown file with auto versioning (short filename)
    """
    # Tìm tất cả file đã có dạng SRS_version_X.md
    existing_files = glob.glob("SRS_version_*.md")

    # Lấy số version lớn nhất hiện tại
    max_ver = 0
    for file in existing_files:
        match = re.search(r"SRS_version_(\d+)\.md", file)
        if match:
            max_ver = max(max_ver, int(match.group(1)))

    # Version tiếp theo
    next_ver = max_ver + 1
    filename = f"SRS_version_{next_ver}.md"

    # Add metadata header
    markdown_content = f"""---
      title: Software Requirements Specification
      generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
      generator: SRS Multi-Agent System
      ---

      {srs_content}

      ---
      *Generated by SRS Multi-Agent System with AI-powered research and analysis*
    """

    with open(filename, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    logger.log("EXPORT_SUCCESS", f"SRS exported to {filename}", level="SUCCESS")
    print(f"\nSRS Document exported to: {filename}")

    return filename