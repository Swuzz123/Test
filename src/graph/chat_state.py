from typing import List, Dict, TypedDict, Any, Optional

class ChatState(TypedDict):
    """
    State for the Chat Graph.
    """
    # Messages history (LangChain format or dict)
    messages: List[Dict[str, Any]]
    
    # User Context
    user_id: str
    conversation_id: str
    
    # Logic capabilities
    current_project: Optional[str]
    mode: str  # "chat" or "srs"
    
    # SRS Artifact Output (for the right panel)
    srs_result: Optional[str]
