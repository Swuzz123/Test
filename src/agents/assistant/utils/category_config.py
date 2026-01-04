# Category weights and minimum requirements
CATEGORY_CONFIG = {
  # Required Components
  "project_type": {
    "weight": 0.30, 
    "min_items": 1,
    "required": True,
    "description": "Loại dự án (web application, web mobile, etc.)"
  },
  "core_features": {
    "weight": 0.45,
    "min_items": 3,
    "required": True,
    "description": "Các tính năng chính"
  },
  "business_goals": {
    "weight": 0.25,
    "min_items": 1,
    "required": True,
    "description": "Mục tiêu kinh doanh / Logic nghiệp vụ"
  },
  
  # Non-required Components
  "tech_stack": {
    "weight": 0.0,
    "min_items": 0,
    "required": False,
    "description": "Công nghệ sử dụng (optional - có thể để AI quyết định)"
  },
  "user_roles": {
    "weight": 0.0,
    "min_items": 0,
    "required": False,
    "description": "Vai trò người dùng (optional)"
  },
  "non_functional": {
    "weight": 0.0,
    "min_items": 0,
    "required": False,
    "description": "Yêu cầu phi chức năng (optional)"
  },
  "integrations": {
    "weight": 0.0,
    "min_items": 0,
    "required": False,
    "description": "Tích hợp bên thứ ba (optional)"
  },
  "constraints": {
    "weight": 0.0,
    "min_items": 0,
    "required": False,
    "description": "Ràng buộc (optional)"
  }
}