EXTRACTION_SYSTEM = """You are a requirements extraction specialist. 
Extract structured requirements from user messages and return ONLY JSON.
No markdown, no code blocks, just pure JSON."""

EXTRACTION_PROMPT = """
Extract requirements from this message:

USER MESSAGE:
{user_message}

CURRENT REQUIREMENTS (don't duplicate):
{current_requirements}

Return ONLY this JSON structure (no markdown, no code blocks):
{{
  "project_type": ["item1"],
  "core_features": ["feature1", "feature2"],
  "tech_stack": ["tech1"],
  "user_roles": ["role1"],
  "business_goals": ["goal1"],
  "non_functional": ["req1"],
  "integrations": ["integration1"],
  "constraints": ["constraint1"]
}}

Only include categories with NEW items. Be specific and extract clearly stated requirements only.
"""