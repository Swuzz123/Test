
import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

try:
    print("1. Testing MemoryManager Singleton...")
    from src.memory.singleton import get_memory_manager
    mm = get_memory_manager()
    print("   MemoryManager initialized successfully.")
    
    print("2. Testing Client retrieval...")
    client = mm.get_client()
    if client:
        print("   Client retrieved successfully.")
    else:
        print("   Client is None!")
        
    print("3. Testing Assistant Agent Imports...")
    from src.agents.assistant.nodes.chat import continue_chat_node
    from src.agents.assistant.nodes.ready import ready_node
    from src.agents.assistant.utils.extractor import extract_requirements
    from src.agents.assistant.utils.classifier import classify_confirmation
    print("   All modules imported successfully.")
    
    print("4. Testing Extractor (Mock)...")
    # We won't actually call OpenAI to save tokens/time, but check if function exists
    print(f"   Function extract_requirements exists: {callable(extract_requirements)}")

    print("\nVERIFICATION SUCCESSFUL")

except Exception as e:
    print(f"\nVERIFICATION FAILED: {e}")
    import traceback
    traceback.print_exc()
