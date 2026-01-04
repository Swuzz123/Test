from typing import List

def _detect_user_language(messages: List[dict]) -> str:
  """
  Detect user's language from conversation history
  
  Logic:
  - Check last 3 user messages
  - Detect if Vietnamese or English
  - Default to Vietnamese if mixed
  """
  if not messages:
    return "Vietnamese"
  
  # Get last 3 user messages
  user_messages = [m["content"] for m in messages if m.get("role") == "user"][-3:]
  
  if not user_messages:
    return "Vietnamese"
  
  # Simple detection: check for Vietnamese characters
  vietnamese_chars = "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"
  
  # Count Vietnamese characters across messages
  all_text = " ".join(user_messages).lower()
  vn_count = sum(1 for char in all_text if char in vietnamese_chars)
  
  # If more than 3 Vietnamese chars, assume Vietnamese
  if vn_count > 3:
    return "Vietnamese"
  else:
    return "English"