from typing import TypedDict, List, Dict, Optional, Literal

class AssistantState(TypedDict):
  """
  State for Assistant Agent LangGraph
  Uses TypedDict for native LangGraph support
  """
  # User context
  user_id: str
  session_id: str
  
  # Current interaction
  current_message: str
  messages: List[Dict[str, str]]  # [{"role": "user", "content": "..."}]
  
  # Requirements tracking
  requirements: Dict[str, List[str]]  # {"project_type": ["Web App"], "core_features": [...]}
  
  # Validation
  validation_score: float 
  missing_categories: List[str]
  is_ready_for_srs: bool  
  
  # Flow control
  current_phase: Literal[
    "intake",
    "extraction", 
    "memory_save",
    "validation",
    "continue_chat",
    "ready_for_srs",
    "trigger_srs",
    "srs_generation",
    "complete"
  ]
  
  # Flags
  should_trigger_srs: bool
  user_confirmed_generation: bool
  
  # SRS output (when generated)
  srs_document: Optional[str]  # Final SRS content
  srs_metadata: Optional[Dict]  # Additional info
  
  # Memory context
  relevant_history: List[Dict]
  user_preferences: List[Dict]