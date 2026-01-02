import json
from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from prompts import  EXTRACTION_PROMPT, EXTRACTION_SYSTEM

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

def extract_requirements(
  user_message: str, 
  current_requirements: Dict[str, List[str]]
) -> Dict[str, List[str]]:
  """
  Extract requirements from user message
  
  Args:
    user_message: User's input
    current_requirements: Existing requirements (to avoid duplicates)
      
  Returns:
    Dict of extracted requirements by category
  """
  try:
    prompt = EXTRACTION_PROMPT.format(
      user_message=user_message,
      current_requirements=json.dumps(current_requirements, indent=2)
    )
    
    response = llm.invoke([
      SystemMessage(content=EXTRACTION_SYSTEM),
      HumanMessage(content=prompt)
    ])
    
    content = response.content.strip()
    
    # Remove markdown code blocks if present
    if "```json" in content:
      content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
      content = content.split("```")[1].split("```")[0]
    
    # Parse JSON
    extracted = json.loads(content.strip())
    
    # Validate structure
    if not isinstance(extracted, dict):
      return {}
    
    return extracted
      
  except Exception as e:
    print(f"[Extraction Error] {str(e)}")
    return {}

def merge_requirements(
  current: Dict[str, List[str]], 
  new: Dict[str, List[str]]
) -> Dict[str, List[str]]:
  """
  Merge new requirements into current (avoid duplicates)
  
  Args:
    current: Current requirements
    new: Newly extracted requirements
      
  Returns:
    Merged requirements dict
  """
  result = current.copy()
  
  for category, items in new.items():
    if category not in result:
      result[category] = []
    
    # Add new items (avoid duplicates)
    for item in items:
      if item not in result[category]:
        result[category].append(item)
  
  return result