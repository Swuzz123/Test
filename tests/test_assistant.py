import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.assistant.graph import run_assistant

if __name__ == "__main__":
  """
  Test Assistant Agent workflow
  """
  print("\n" + "="*80)
  print("TESTING ASSISTANT AGENT")
  print("="*80 + "\n")
  
  # Message 1: Initial vague request
  print("USER: I want to build a task management app\n")
  response1, state1 = run_assistant(
    user_message="I want to build a task management app",
    user_id="test_user",
    session_id="test_session"
  )
  print(f"ASSISTANT: {response1}\n")
  print(f"Completeness: {int(state1['validation_score'] * 100)}%")
  print(f"Ready for SRS: {state1['is_ready_for_srs']}\n")
  print("-"*80 + "\n")
  
  # Message 2: More details
  print("USER: It should have task creation, assignment, deadlines, comments, and notifications. Use React and Node.js\n")
  response2, state2 = run_assistant(
    user_message="It should have task creation, assignment, deadlines, comments, and notifications. Use React and Node.js",
    user_id="test_user",
    session_id="test_session",
    existing_state=state1
  )
  print(f"ASSISTANT: {response2}\n")
  print(f"Completeness: {int(state2['validation_score'] * 100)}%")
  print(f"Ready for SRS: {state2['is_ready_for_srs']}\n")
  print("-"*80 + "\n")
  
  # Message 3: Even more details
  print("USER: For project managers and team members. Should handle 10,000 concurrent users\n")
  response3, state3 = run_assistant(
    user_message="For project managers and team members. Should handle 10,000 concurrent users",
    user_id="test_user",
    session_id="test_session",
    existing_state=state2
  )
  print(f"ASSISTANT: {response3}\n")
  print(f"Completeness: {int(state3['validation_score'] * 100)}%")
  print(f"Ready for SRS: {state3['is_ready_for_srs']}\n")
  print("-"*80 + "\n")
  
  # Message 4: Confirmation (if ready)
  if state3["should_trigger_srs"]:
    print("USER: Yes, generate the SRS\n")
    response4, state4 = run_assistant(
      user_message="Yes, generate the SRS",
      user_id="test_user",
      session_id="test_session",
      existing_state=state3
    )
    print(f"ASSISTANT: {response4}\n")
    
    if state4.get("srs_document"):
      print(f"\nSRS GENERATED!")
      print(f"Preview: {state4['srs_document'][:500]}...\n")
  
  print("="*80)
  print("TEST COMPLETE")
  print("="*80)