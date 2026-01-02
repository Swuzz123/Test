import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from prompts import SYNTHESIS_PROMPT
from src.utils.tracing import logger
from src.agents.srs.state import SRSState

# =============================== CONFIGURATION ================================
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

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