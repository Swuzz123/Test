from typing import Dict, List, Tuple
from agents.assistant.utils.category_config import CATEGORY_CONFIG

def calculate_completeness(requirements: Dict[str, List[str]]) -> Tuple[float, List[str]]:
  """
  Calculate requirement completeness score
  
  Args:
    requirements: Dict of category -> list of items
      
  Returns:
    (score, missing_categories)
    score: 0.0 to 1.0
    missing_categories: List of category names that need more items
  """
  total_score = 0.0
  missing = []
  
  for category, config in CATEGORY_CONFIG.items():
    if not config["required"]:
      continue 
    
    items = requirements.get(category, [])
    item_count = len(items)
    weight = config["weight"]
    min_items = config["min_items"]
    
    # Calculate category score
    if min_items == 0:
      category_score = 1.0 if item_count > 0 else 0.0
    else:
      # Required category - proportional score
      category_score = min(1.0, item_count / min_items)
    
    # Add weighted score
    total_score += category_score * weight
    
    # Track missing
    if category_score < 1.0 and min_items > 0:
      missing.append(category)
  
  return round(total_score, 2), missing

def is_ready_for_srs(score: float, threshold: float = 0.7) -> bool:
  """Check if score meets threshold"""
  return score >= threshold

def get_next_category_to_ask(missing_categories: List[str]) -> str:
  """Get highest priority missing category"""
  if not missing_categories:
    return "general_details"
  
  # Priority order (most important first)
  priority = [
    "project_type",
    "core_features", 
    "business_goals"
  ]
  
  for cat in priority:
    if cat in missing_categories:
      return cat
  
  return missing_categories[0]

def is_category_optional(category: str) -> bool:
  """
  Check if a category is optional
    """
  config = CATEGORY_CONFIG.get(category, {})
  return not config.get("required", False)

def get_optional_categories() -> List[str]:
  """
  Get list of optional categories
  Assistant Agent can tell user: "All the information is optional, I can determine myself"
  """
  return [
    cat for cat, config in CATEGORY_CONFIG.items()
    if not config.get("required", False)
  ]