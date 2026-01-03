from typing import List, Dict, TypedDict

class SRSState(TypedDict):
  """
  Shared state that flows through the entire graph.
  All nodes read from and write to this state.
  """
  # Input
  project_query: str
  
  # Planning phase
  research_results: List[str]
  agent_plan: List[Dict]
  
  # Execution phase
  worker_outputs: List[Dict]
  
  # Synthesis phase
  final_srs: str
  
  # Metadata
  current_phase: str
  messages: List[Dict]