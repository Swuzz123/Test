import json
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from src.utils.tracing import logger
from src.agents.srs.state import SRSState
from prompts import WORKER_PROMPT_TEMPLATE

# =============================== CONFIGURATION ================================
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

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