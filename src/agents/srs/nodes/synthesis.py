import os
import json
from src.agents.srs.prompts import SYNTHESIS_PROMPT
from src.utils.tracing import logger, observe
from src.agents.srs.state import SRSState
from src.memory.singleton import get_memory_manager

# =============================== SYNTHESIZE NODE ==============================
@observe()
def synthesis_node(state: SRSState) -> SRSState:
  """
  Node 4: Synthesis - create final SRS document
  """
  logger.log("NODE_START", "Synthesis Node", level="AGENT")
  
  client = get_memory_manager().get_client()
  project_query = state["project_query"]
  worker_outputs = state["worker_outputs"]
  
  # Format worker prompt
  worker_outputs_format = json.dumps(worker_outputs, indent=2, ensure_ascii=False)
  
  synthesis_prompt = SYNTHESIS_PROMPT.format(
    project_query=project_query, 
    worker_outputs=worker_outputs_format
  )
  
  messages = [
      {"role": "system", "content": "You are a Lead Technical Architect & Documentation Specialist."},
      {"role": "user", "content": synthesis_prompt}
  ]
  
  response = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=messages,
      temperature=0.7
  )
  
  final_srs = response.choices[0].message.content
  
  logger.log("NODE_COMPLETE", "Synthesis Node - SRS generated", 
            data={"doc_length": len(final_srs)}, level="SUCCESS")
  
  return {
    **state,
    "final_srs": final_srs,
    "current_phase": "complete"
  }