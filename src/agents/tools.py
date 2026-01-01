import os
from dotenv import load_dotenv
from tavily import TavilyClient
from langchain_core.tools import tool
from src.utils.tracing import logger

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
def tavily_search(query: str, search_depth: str = "advanced") -> str:
  """
  Search the web for technical information using Tavily.
  
  Args:
    query: Search query (e.g., 'best microservices architecture 2024')
    search_depth: 'basic' or 'advanced' (default: advanced)
  """
  logger.log("TOOL_CALL", f"Tavily Search: {query}", 
            data={"search_depth": search_depth}, level="TOOL")
  
  try:
    response = tavily_client.search(
      query=query,
      search_depth=search_depth,
      max_results=5
    )
    
    results = []
    for result in response.get('results', []):
      results.append({
        "title": result.get('title', ''),
        "url": result.get('url', ''),
        "content": result.get('content', '')[:500]
      })
    
    formatted = "\n\n".join([
      f"**{r['title']}**\nURL: {r['url']}\n{r['content']}"
      for r in results
    ])
    
    logger.log("TOOL_RESPONSE", f"Tavily returned {len(results)} results", 
              data={"num_results": len(results)}, level="TOOL")
    
    return formatted if formatted else "No results found."
      
  except Exception as e:
    logger.log("TOOL_ERROR", f"Tavily search failed: {str(e)}", level="ERROR")
    return f"Search error: {str(e)}"

tools = [tavily_search]