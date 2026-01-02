import json
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.graph.chat_state import ChatState
from src.memory.memory_manager import MemoryManager
from src.graph.workflow import generate_srs_langgraph

# Initialize Memory Manager (Global or Singleton pattern often used in this scope)
# In a real app, this might be dependency injected or initialized per request context if lightweight
# For this demo, we can initialize it once or lazily.
memory_manager = MemoryManager()

def chat_node(state: ChatState) -> Dict[str, Any]:
    """
    Standard chat interactions with Memori auto-recall.
    """
    print("--- CHAT NODE ---")
    user_id = state["user_id"]
    process_id = "chat-agent"
    conversation_id = state.get("conversation_id", "default_session")
    
    # 1. Setup Memory Context
    memory_manager.set_context(user_id=user_id, process_id=process_id)
    memory_manager.set_session(conversation_id)
    
    # 2. Prepare Messages
    # Convert dict messages to LangChain messages if needed, or use as is if Client supports it.
    # Memori's wrapped client expects standard OpenAI format usually, or we can use the format it supports.
    # Here we assume state["messages"] is a list of {"role": "...", "content": "..."}
    messages = state["messages"]
    
    # 3. Call LLM (Memori Auto-Recall happens here)
    client = memory_manager.get_client()
    
    # Simple system prompt to guide the chat agent
    system_prompt = {
        "role": "system", 
        "content": "You are a helpful AI Assistant for Software Requirements. You help users define their project requirements. If the user asks clearly to create or generate an SRS, acknowledge it."
    }
    
    # Ensure system prompt is present
    if not messages or messages[0].get("role") != "system":
        messages = [system_prompt] + messages
        
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7
    )
    
    ai_message_content = response.choices[0].message.content
    
    # Update messages
    new_message = {"role": "assistant", "content": ai_message_content}
    
    return {"messages": messages + [new_message]}

def detect_srs_node(state: ChatState) -> Dict[str, Any]:
    """
    Analyze the last user message to see if they want to generate/update SRS.
    Uses LLM for smarter classification.
    """
    print("--- DETECT SRS NODE (LLM) ---")
    messages = state["messages"]
    if not messages:
        return {"mode": "chat"}
        
    last_message = messages[-1]
    
    # Only check if user spoke last
    if last_message.get("role") != "user":
        return {"mode": "chat"}
        
    client = memory_manager.get_client()
    
    # Construct prompt
    # We include some context if possible, but for efficiency just the last message 
    # and maybe the one before it if it was assistant asking a question.
    
    classification_prompt = [
        {"role": "system", "content": (
            "You are an intent classifier. Your job is to determine if the user wants to CREATE, GENERATE, or UPDATE a Software Requirements Specification (SRS) document/artifact.\n"
            "Analyze the user's input.\n"
            "- If the user explicitly asks to create/write/generate/update an SRS, PRD, or requirements document, return 'SRS'.\n"
            "- If the user is agreeing to a suggestion to create an SRS (e.g. 'Yes, please do'), return 'SRS'.\n"
            "- Otherwise, return 'CHAT'.\n"
            "Output ONLY the class label: 'SRS' or 'CHAT'."
        )},
        {"role": "user", "content": f"User Input: {last_message.get('content')}"}
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=classification_prompt,
            temperature=0
        )
        result = response.choices[0].message.content.strip().upper()
        
        if "SRS" in result:
            return {"mode": "srs"}
            
    except Exception as e:
        print(f"Error in detect_srs_node: {e}")
        # Fallback to keyword if LLM fails
        content = last_message.get("content", "").lower()
        if "create srs" in content or "generate srs" in content:
            return {"mode": "srs"}
            
    return {"mode": "chat"}

async def srs_node(state: ChatState) -> Dict[str, Any]:
    """
    Generate or update SRS using the SRS Graph.
    """
    print("--- SRS NODE ---")
    user_id = state["user_id"]
    # We might want a separate process_id for SRS or share it
    process_id = "srs-agent" 
    
    # 1. Setup Memory Context for SRS
    memory_manager.set_context(user_id=user_id, process_id=process_id)
    
    # 2. Extract Project Query from context or chat
    # In a real app, we might ask the LLM to extract the structured query.
    # For now, we use the last user message or a summarized intention.
    # Also, we can perform Manual Recall here to enrich the query.
    
    messages = state["messages"]
    last_user_input = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "General Project")
    
    # Manual Recall
    print(f"Recalling facts for query: {last_user_input}")
    try:
        facts_list = memory_manager.memori.recall(last_user_input)
        # facts_list is likely a list of objects or strings depending on memori version.
        # Assuming list of objects with 'content' or just strings.
        # Let's stringify it safely.
        facts_str = "\n".join([str(f) for f in facts_list])
        print(f"Recalled Facts: {facts_str}")
    except Exception as e:
        print(f"Recall failed: {e}")
        facts_str = ""
    
    # Enrich Query
    enhanced_query = f"{last_user_input}\nContext from Memory:\n{facts_str}"
    
    # 3. Call SRS Graph
    # We pass the user input as the project query
    srs_content = await generate_srs_langgraph(project_query=enhanced_query)
    
    # 4. Update State
    # Generate a concise summary of what was done using the LLM
    client = memory_manager.get_client()
    
    summary_prompt = [
        {"role": "system", "content": "You are a helpful assistant. You have just generated a Software Requirements Specification (SRS) artifact. based on the user's request. Summarize the generated SRS briefly (1-2 sentences) and invite the user to check the artifacts panel."},
        {"role": "user", "content": f"Original Request: {last_user_input}\n\nGenerated SRS Content (First 2000 chars):\n{srs_content[:2000]}..."}
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=summary_prompt,
            temperature=0.7
        )
        summary_msg = response.choices[0].message.content
    except Exception as e:
        print(f"Failed to generate summary: {e}")
        summary_msg = f"I have generated the SRS for '{last_user_input}'. You can view it in the panel to the right."

    system_msg = {
        "role": "assistant",
        "content": summary_msg
    }
    
    return {
        "srs_result": srs_content,
        "mode": "chat", # Reset mode
        "messages": messages + [system_msg]
    }

def route_logic(state: ChatState) -> str:
    return state["mode"]

def create_chat_graph():
    workflow = StateGraph(ChatState)
    
    workflow.add_node("chat", chat_node)
    workflow.add_node("detect", detect_srs_node)
    workflow.add_node("srs", srs_node)
    
    workflow.set_entry_point("detect")
    
    workflow.add_conditional_edges(
        "detect",
        route_logic,
        {
            "chat": "chat",
            "srs": "srs"
        }
    )
    
    # Modified: SRS node ends the flow to avoid redundant chat generation
    workflow.add_edge("srs", END) 
    workflow.add_edge("chat", END)
    
    app = workflow.compile()
    return app
