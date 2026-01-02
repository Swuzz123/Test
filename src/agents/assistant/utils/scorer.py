from typing import Dict, List, Tuple

# Category weights and minimum requirements
CATEGORY_CONFIG = {
  "project_type": {"weight": 0.20, "min_items": 1},
  "core_features": {"weight": 0.25, "min_items": 3},
  "tech_stack": {"weight": 0.15, "min_items": 2},
  "user_roles": {"weight": 0.10, "min_items": 1},
  "business_goals": {"weight": 0.10, "min_items": 1},
  "non_functional": {"weight": 0.10, "min_items": 1},
  "integrations": {"weight": 0.05, "min_items": 0}, 
  "constraints": {"weight": 0.05, "min_items": 0} 
}

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
    items = requirements.get(category, [])
    item_count = len(items)
    min_items = config["min_items"]
    weight = config["weight"]
    
    # Calculate category score
    if min_items == 0:
      # Optional category
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

def is_ready_for_srs(score: float, threshold: float = 0.8) -> bool:
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
    "tech_stack",
    "user_roles",
    "business_goals",
    "non_functional"
  ]
  
  for cat in priority:
    if cat in missing_categories:
      return cat
  
  return missing_categories[0]