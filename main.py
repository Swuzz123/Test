import asyncio
from datetime import datetime

from src.utils.tracing import logger
from src.utils.export_md import export_to_markdown
from agents.srs.graph import generate_srs_langgraph

async def interactive_mode():
  """Interactive CLI (same interface)"""
  print("\n" + "="*80)
  print(" SRS MULTI-AGENT SYSTEM - LANGGRAPH VERSION")
  print(" Powered by OpenAI + Tavily + LangGraph")
  print("="*80)
  print("\nCommands:")
  print("  • Type your project idea and press Enter")
  print("  • Type 'trace' to export execution trace")
  print("  • Type 'q' to quit")
  print("="*80 + "\n")
  
  current_srs = None
  current_project = None
  
  while True:
    try:
      user_input = input("\nProject Idea (or command): ").strip()
      
      if not user_input:
        continue
      
      if user_input.lower() == 'q':
        print("\nGoodbye!\n")
        break
      
      if user_input.lower() == 'trace':
        if logger.logs:
          logger.export_trace()
        else:
          print("No trace data available.")
        continue
      
      if user_input.lower().startswith('save'):
        if current_srs and current_project:
          print("\nSaving SRS document...")
          export_to_markdown(current_srs)
          logger.export_trace(f"trace_langgraph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        else:
          print("No SRS document to save.")
        continue
      
      current_project = user_input
      print(f"\nGenerating SRS using LangGraph for: {user_input}\n")
      
      current_srs = await generate_srs_langgraph(user_input)
      
      print("\n" + "="*80)
      print(" FINAL SRS DOCUMENT")
      print("="*80 + "\n")
      print(current_srs)
      print("\n" + "="*80)
      print("\nType 'save' to export as markdown, or 'trace' for execution log")
        
    except KeyboardInterrupt:
      print("\n\nInterrupted. Goodbye!\n")
      break
    except Exception as e:
      print(f"\nError: {str(e)}\n")
      import traceback
      traceback.print_exc()
      logger.log("SYSTEM_ERROR", str(e), level="ERROR")

if __name__ == "__main__":
  asyncio.run(interactive_mode())