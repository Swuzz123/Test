import os
from typing import Dict, Any
from dotenv import load_dotenv
from contextlib import contextmanager

from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context

load_dotenv()

# =========================== LANGFUSE CLIENT SETUP ============================
langfuse_client = None

def init_langfuse():
  """
  Initialize Langfuse client
  Call this once at app startup
  """
  global langfuse_client
  
  public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
  secret_key = os.getenv("LANGFUSE_SECRET_KEY")
  host = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
  
  if public_key and secret_key:
    langfuse_client = Langfuse(
      public_key=public_key,
      secret_key=secret_key,
      host=host
    )
    print("Langfuse initialized")
    return langfuse_client
  else:
    print("Langfuse keys not found - tracing disabled")
    return None

def get_langfuse():
  """Get Langfuse client (lazy init)"""
  global langfuse_client
  if langfuse_client is None:
    langfuse_client = init_langfuse()
  return langfuse_client

# ============================== TRACE DECORATORS ==============================
def trace_agent(name: str, agent_type: str = "agent"):
  """
  Decorator for agent-level tracing
  
  Usage:
    @trace_agent("Assistant Agent", agent_type="assistant")
    def run_assistant(...):
      ...
  
  Creates a trace in Langfuse with:
  - Agent name
  - Input/output
  - Duration
  - Cost
  """
  def decorator(func):
    @observe(name=name, as_type="generation")
    def wrapper(*args, **kwargs):
        # Add metadata
        langfuse_context.update_current_observation(
            metadata={
              "agent_type": agent_type,
              "function": func.__name__
            }
        )
        
        # Execute function
        result = func(*args, **kwargs)
        
        return result
    
    return wrapper
  return decorator

def trace_node(node_name: str):
  """
  Decorator for LangGraph node tracing
  
  Usage:
    @trace_node("intake_node")
    def intake_node(state):
      ...
  
  Tracks:
  - Node execution
  - State changes
  - Duration
  """
  def decorator(func):
    @observe(name=node_name, as_type="span")
    def wrapper(state, *args, **kwargs):
      # Log input state (safe extraction)
      input_summary = {
        "current_phase": state.get("current_phase", "unknown"),
        "validation_score": state.get("validation_score", 0),
      }
      
      langfuse_context.update_current_observation(
        input=input_summary
      )
      
      # Execute node
      result = func(state, *args, **kwargs)
      
      # Log output state
      output_summary = {
        "current_phase": result.get("current_phase", "unknown"),
        "validation_score": result.get("validation_score", 0),
      }
      
      langfuse_context.update_current_observation(
        output=output_summary
      )
      
      return result
    
    return wrapper
  return decorator

def trace_llm_call(call_name: str, model: str = "gpt-4o-mini"):
  """
  Decorator for LLM call tracing
  
  Usage:
    @trace_llm_call("extract_requirements", model="gpt-4o-mini")
    def extract_requirements(...):
      response = llm.invoke(...)
      return response
  
  Tracks:
  - Prompt
  - Response
  - Tokens
  - Cost
  """
  def decorator(func):
    @observe(
      name=call_name,
      as_type="generation"
    )
    def wrapper(*args, **kwargs):
      # Add model metadata
      langfuse_context.update_current_observation(
        model=model,
        metadata={"call_type": "llm"}
      )
      
      # Execute LLM call
      result = func(*args, **kwargs)
      
      # Try to extract token usage (if available)
      if hasattr(result, 'response_metadata'):
        usage = result.response_metadata.get('token_usage', {})
        if usage:
          langfuse_context.update_current_observation(
              usage={
                "input": usage.get('prompt_tokens', 0),
                "output": usage.get('completion_tokens', 0),
                "total": usage.get('total_tokens', 0)
              }
            )
      
      return result
    
    return wrapper
  return decorator

# ============================== CONTEXT MANAGERS ==============================
@contextmanager
def trace_graph_execution(graph_name: str, initial_state: Dict[str, Any]):
  """
  Context manager for tracing entire graph execution
  
  Usage:
    with trace_graph_execution("Assistant Agent", initial_state):
      for output in app.stream(state):
        ...
  """
  client = get_langfuse()
  
  if client:
    trace = client.trace(
      name=graph_name,
      input={"initial_state": _safe_state_summary(initial_state)},
      metadata={"graph_type": "langgraph"}
    )
    
    try:
      yield trace
    finally:
      # Flush to send data
      client.flush()
  else:
    yield None

def _safe_state_summary(state: Dict[str, Any]) -> Dict[str, Any]:
  """
  Create safe summary of state for logging
  (avoid logging huge data)
  """
  return {
    "user_id": state.get("user_id", "unknown"),
    "session_id": state.get("session_id", "unknown"),
    "current_phase": state.get("current_phase", "unknown"),
    "validation_score": state.get("validation_score", 0),
    "requirements_count": len(state.get("requirements", {}))
  }

# ====================== MANUAL TRACING (for more control) =====================
class LangfuseTracer:
  """
  Manual tracer for fine-grained control
  
  Usage:
    tracer = LangfuseTracer("Assistant Agent")
    tracer.start()
    
    span = tracer.start_span("intake_node")
    # ... node execution
    tracer.end_span(span, output=result)
    
    tracer.end()
  """
  
  def __init__(self, trace_name: str):
    self.client = get_langfuse()
    self.trace_name = trace_name
    self.trace = None
    self.spans = {}
  
  def start(self, input_data: Dict = None):
    """Start a new trace"""
    if self.client:
      self.trace = self.client.trace(
        name=self.trace_name,
        input=input_data or {}
      )
  
  def start_span(self, span_name: str, input_data: Dict = None):
    """Start a new span within trace"""
    if self.trace:
      span = self.trace.span(
        name=span_name,
        input=input_data or {}
      )
      self.spans[span_name] = span
      return span
    return None
  
  def end_span(self, span_name: str, output_data: Dict = None):
    """End a span"""
    if span_name in self.spans:
      span = self.spans[span_name]
      span.end(output=output_data or {})
  
  def log_event(self, event_name: str, data: Dict = None):
    """Log an event in the trace"""
    if self.trace:
      self.trace.event(
        name=event_name,
        input=data or {}
      )
  
  def end(self, output_data: Dict = None):
    """End the trace"""
    if self.trace:
      self.trace.update(output=output_data or {})
    
    if self.client:
      self.client.flush()

# ============================== UTILITY FUNCTIONS =============================
def log_agent_decision(decision: str, reasoning: str, metadata: Dict = None):
  """
  Log an agent decision point
  Useful for debugging routing logic
  """
  if langfuse_context:
    langfuse_context.update_current_observation(
      output={
        "decision": decision,
        "reasoning": reasoning
      },
      metadata=metadata or {}
    )

def flush_langfuse():
  """
  Flush Langfuse to send all pending data
  Call this at end of request/session
  """
  client = get_langfuse()
  if client:
    client.flush()