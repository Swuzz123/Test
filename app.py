import streamlit as st
import asyncio
import re
from streamlit_mermaid import st_mermaid
import uuid
import nest_asyncio

# Apply nest_asyncio to allow nested event loops (crucial for Streamlit + LangGraph/Asyncio)
nest_asyncio.apply()

from src.graph.chat_workflow import create_chat_graph

# Configure Page
st.set_page_config(layout="wide", page_title="AI Architect & SRS Agent")

# CSS Styling
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stChatInput {
        position: fixed;
        bottom: 30px;
        z-index: 1000;
        width: 45% !important;
    }
    /* Simple fix for chat input positioning */
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "srs_content" not in st.session_state:
    st.session_state.srs_content = "### SRS Artifact\n\nNo SRS generated yet. Ask the agent to create one!"
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user-{uuid.uuid4().hex[:8]}"
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = f"conv-{uuid.uuid4().hex[:8]}"

# Load Graph once (cache resource implies global, but session_state is fine for single user local app)
if "graph" not in st.session_state:
    st.session_state.graph = create_chat_graph()

# Sidebar for Metadata
with st.sidebar:
    st.title("Settings")
    st.write(f"**User:** `{st.session_state.user_id}`")
    st.write(f"**Session:** `{st.session_state.conversation_id}`")
    
    st.divider()
    if st.button("New Session"):
        st.session_state.conversation_id = f"conv-{uuid.uuid4().hex[:8]}"
        st.session_state.messages = []
        st.session_state.srs_content = "### SRS Artifact\n\nNo SRS generated yet."
        st.rerun()

# Layout: Artifact (Left) - Chat (Right)
col_artifact, col_chat = st.columns([7, 3], gap="medium")

# Custom CSS for "Premium UI"
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #333;
    }
    
    /* Background */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* LEFT PANEL: Artifact Editor Look */
    .artifact-container {
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        padding: 20px;
        height: 80vh;
        overflow-y: auto;
        border: 1px solid #EAEAEA;
    }
    
    /* RIGHT PANEL: Chat Assistant Card */
    .chat-card {
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        border: 1px solid #EAEAEA;
        height: 80vh;
        display: flex;
        flex-direction: column;
    }
    
    /* Headers */
    h3 {
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 0px;
    }
    
    /* Custom Buttons in Toolbar */
    .stButton button {
        background-color: #ffffff;
        color: #333;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 500;
        padding: 0.25rem 0.75rem;
        box-shadow: none;
    }
    .stButton button:hover {
        background-color: #f5f5f5;
        border-color: #ccc;
        color: #000;
    }
    /* Primary Action Button */
    .primary-btn button {
        background-color: #7B68EE !important; /* Purple-ish like visual */
        color: white !important;
        border: none !important;
    }
    
    /* Chat Bubbles */
    .stChatMessage {
        padding: 1rem;
    }
    .stChatMessage[data-testid="stChatMessageUser"] {
        background-color: white;
        border: 1px solid #eee;
        border-radius: 12px 12px 0 12px;
    }
    .stChatMessage[data-testid="stChatMessageAssistant"] {
        background-color: #F4F6FB;
        border-radius: 12px 12px 12px 0;
    }
    
    /* Assistant Header Status */
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: #2ECC71;
        border-radius: 50%;
        margin-right: 5px;
    }
    .status-text {
        color: #2ECC71;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #EAEAEA;
    }
    
    /* Hide Default Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* header {visibility: hidden;} */
    
    /* Reduce Top Whitespace */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: SESSION MANAGEMENT ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=64)
    st.title("Innotech AI")
    st.caption("SRS Generator Workspace")
    
    st.markdown("---")
    
    # New Project Button
    if st.button("＋ New Project", use_container_width=True, type="primary"):
        # Reset Session
        st.session_state.conversation_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.srs_content = "### SRS Artifact\n\nNo SRS generated yet."
        # Update memory manager session if possible
        # Assuming memory_manager is defined elsewhere or will be.
        # For now, commenting out to avoid NameError if not present.
        # if hasattr(memory_manager, 'set_session'):
        #      memory_manager.set_session(st.session_state.conversation_id)
        st.rerun()
        
    st.markdown("### 🗂️ Active Session")
    st.info(f"**ID:** `{st.session_state.conversation_id[:8]}...`")
    
    st.markdown("### 🕒 Recent History")
    # Placeholder for history (mockup for UI/UX)
    st.markdown("""
    - Project Alpha
    - E-Commerce Req
    - Student Mgmt
    """, help="History feature coming soon")
    
    st.markdown("---")
    with st.expander("⚙️ Settings"):
        st.checkbox("Auto-Save", value=True)
        st.checkbox("Dark Mode", value=False)

# --- MAIN HEADER ---
# Reduced bottom margin
st.markdown("""
<div style="margin-bottom: 15px;">
    <h1 style="font-size: 28px; margin-bottom: 5px;">🚀 Enterprise SRS Architect</h1>
    <p style="color: #666; font-size: 16px; margin-top: 0;">Intelligent requirements engineering powered by Graph AI</p>
</div>
""", unsafe_allow_html=True)

# Layout: Artifact (Left) - Chat (Right)
col_artifact, col_chat = st.columns([7, 3], gap="medium")

# --- LEFT PANEL: ARTIFACT EDITOR ---
with col_artifact:
    # Toolbar removed as requested
    
    # Document Area (Styled Container with Border)
    # The border=True creates the explicit frame user requested
    # Matched height with Chat Panel (800px)
    # Document Area (Styled Container with Border)
    # The border=True creates the explicit frame user requested
    # Matched height with Chat Panel (800px)
    with st.container(height=800, border=True):
        content = st.session_state.srs_content
        
        # Regex to split content by mermaid code blocks
        # Captures the block including backticks so we can identify it
        parts = re.split(r'(```mermaid\n.*?\n```)', content, flags=re.DOTALL)
        
        for part in parts:
            if part.startswith("```mermaid"):
                # Clean up the code block to get just the mermaid code
                code = part.replace("```mermaid\n", "").replace("\n```", "").strip()
                if code:
                    try:
                        st_mermaid(code, height=400)
                    except Exception as e:
                        st.error(f"Mermaid rendering error: {e}")
                        st.code(code, language="mermaid")
            else:
                # Render regular markdown
                if part.strip():
                    st.markdown(part)

# --- RIGHT PANEL: CHAT ASSISTANT ---
with col_chat:
    # We wrap everything in a border container to simulate the 'Card'
    with st.container(height=800, border=True):
        
        # Custom Header inside the card
        # Reduced margin to save vertical space
        st.markdown("""
        <div style="padding-bottom: 10px; border-bottom: 1px solid #eee; margin-bottom: 10px;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="background: #E8EAF6; padding: 8px; border-radius: 8px;">
                        🤖
                    </div>
                    <div>
                        <h3 style="margin:0; font-size:16px;">AI Architect Assistant</h3>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Messages Area (Scrollable within the card)
        # Height reduced to 500 to ensure Header + Messages + Input fits comfortably in 800px
        # allowing ONLY this container to have a scrollbar.
        messages_container = st.container(height=500)
        with messages_container:
            if not st.session_state.messages:
                st.markdown("""
                <div style="background: #F4F6FB; padding: 15px; border-radius: 12px; font-size: 0.95rem; color: #444;">
                  Chào bạn! Tôi là trợ lí AI chuyên về SRS. Tôi có thể giúp bạn viết mô tả yêu cầu, kiểm tra logic nghiệp vụ hoặc gợi ý các tính năng còn thiếu. Bạn cần hỗ trợ gì cho dự án hiện tại?   
                
                </div>
                """, unsafe_allow_html=True)

            for msg in st.session_state.messages:
                role = msg.get("role")
                if role == "system":
                    continue
                
                avatar = "👤" if role == "user" else "🤖"
                with st.chat_message(role, avatar=avatar):
                    st.markdown(msg.get("content"))

        # Input Area (Embedded inside the card)
        # Using a form helps keep it structured and allows 'Enter' to submit
        with st.container():
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            with st.form(key="chat_form", clear_on_submit=True):
                # Columns to put input and button side by side
                c_input, c_btn = st.columns([85, 15])
                with c_input:
                    user_input = st.text_input("Message...", placeholder="Type your message...", label_visibility="collapsed")
                with c_btn:
                    # Use a simple send icon/text
                    submitted = st.form_submit_button("➤")
        
        if submitted and user_input:
            # 1. Display User Message immediately
            user_msg = {"role": "user", "content": user_input}
            st.session_state.messages.append(user_msg)
            with messages_container.chat_message("user", avatar="👤"):
                st.markdown(user_input)
                
            # 2. Run Graph
            with messages_container.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking..."):
                    inputs = {
                        "messages": st.session_state.messages,
                        "user_id": st.session_state.user_id,
                        "conversation_id": st.session_state.conversation_id,
                        "current_project": None, 
                        "mode": "chat",
                        "srs_result": None
                    }
                    
                    async def run_chat():
                        return await st.session_state.graph.ainvoke(inputs)
                    
                    final_state = asyncio.run(run_chat())
                    
                    # 3. Update State & UI
                    st.session_state.messages = final_state["messages"]
                    
                    if final_state.get("srs_result"):
                        st.session_state.srs_content = final_state["srs_result"]
                    
                    last_msg = final_state["messages"][-1]
                    if last_msg["role"] == "assistant":
                        st.markdown(last_msg["content"])
            
            # Force rerun to update artifacts panel and clear input state visually if needed
            st.rerun()
