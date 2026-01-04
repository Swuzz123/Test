import json
from typing import Dict
from src.utils.tracing import logger, observe
from src.agents.srs.state import SRSState
from src.agents.srs.prompts import WORKER_PROMPT_TEMPLATE
from src.memory.singleton import get_memory_manager

# ================================ WORKER NODE =================================
@observe()
def worker_node(state: SRSState) -> SRSState:
  """
  Node 3: Worker execution - run all sub-agents
  This node handles parallel execution internally
  """
  logger.log("NODE_START", "Worker Node - parallel execution", level="AGENT")
  
  agent_plan = state["agent_plan"]
  client = get_memory_manager().get_client()
  
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
    
    messages = [
        {"role": "system", "content": f"You are a specialized agent: {role}. {specialty}"},
        {"role": "user", "content": worker_prompt}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7
    )
    
    output_text = response.choices[0].message.content
    
    logger.log("WORKER_COMPLETE", f"Agent #{index}: {role} done", level="SUCCESS")
    
    return {
      "agent_index": index,
      "role": role,
      "output": output_text
    }
  
  # Note: To keep it simple and safe, we run sequentially or use a ThreadPool if concurrency is needed.
  # The original code ran in a loop which is effectively sequential unless async features were used (they weren't explicitly shown as async in the snippet)
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