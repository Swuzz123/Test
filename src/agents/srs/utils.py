# tavily_tools = [
#   {
#     "type": "function",
#     "function": {
#       "name": "tavily_search",
#       "description": "Search the web for information about software architectures, technical references, best practices, and modern tech stack solutions. Use this to research before making technical decisions.",
#       "parameters": {
#         "type": "object",
#         "properties": {
#           "query": {
#             "type": "string",
#             "description": "Detailed search query (e.g., 'best microservices architecture for e-commerce 2024')"
#           },
#           "search_depth": {
#             "type": "string",
#             "enum": ["basic", "advanced"],
#             "description": "Search depth: 'basic' for quick results, 'advanced' for comprehensive research",
#             "default": "advanced"
#           }
#         },
#         "required": ["query"]
#       }
#     }
#   }
# ]