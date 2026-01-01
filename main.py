import asyncio
from datetime import datetime

from src.utils.tracing import logger
from src.agents.srs_agent import generate_srs, export_to_markdown

async def interactive_mode():
    """
    Interactive command-line interface
    """
    print("\n" + "="*80)
    print(" SRS MULTI-AGENT SYSTEM v2.0")
    print(" Powered by OpenAI GPT-4 + Tavily Search")
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
            user_input = input("\n🚀 Project Idea (or command): ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'q':
                print("\n👋 Goodbye!\n")
                break
            
            if user_input.lower() == 'trace':
                if logger.logs:
                    logger.export_trace()
                else:
                    print("⚠️  No trace data available. Generate an SRS first.")
                continue
            
            if user_input.lower().startswith('save'):
                if current_srs and current_project:
                    print("\n💾 Saving SRS document...")
                    export_to_markdown(current_srs, current_project)
                    logger.export_trace(f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                else:
                    print("⚠️  No SRS document to save. Generate one first.")
                continue
            
            # Generate SRS
            current_project = user_input
            print(f"\n🔄 Generating SRS for: {user_input}\n")
            
            current_srs = await generate_srs(user_input)
            
            print("\n" + "="*80)
            print(" FINAL SRS DOCUMENT")
            print("="*80 + "\n")
            print(current_srs)
            print("\n" + "="*80)
            print("\n💡 Type 'save' to export as markdown, or 'trace' for execution log")
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            logger.log("SYSTEM_ERROR", str(e), level="ERROR")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    asyncio.run(interactive_mode())