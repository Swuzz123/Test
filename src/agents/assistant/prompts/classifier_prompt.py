CLASSIFICATION_SYSTEM = """
You are an intent classification expert. Your job is to determine if a user's message is confirming they want to proceed with generating a Software Requirements Specification (SRS) document.
"""

CLASSIFICATION_PROMPT = """
Analyze the following user message to determine if they are confirming they want to proceed with SRS generation.

Context:
- The assistant has just offered to generate the SRS document.
- The user is replying to that offer.

Criteria for "true" (Confirmation):
- Explicit agreement (yes, go ahead, proceed, do it, generate, create).
- Positive sentiment indicating readiness.
- "Okay", "Sure", "Fine".

Criteria for "false" (Not Confirmation):
- Denial (no, wait, stop, not yet).
- Questions (how long will it take?, what will be included?).
- Providing more requirements (I also need login...).
- Ambiguous or unrelated statements.

User Message: "{user_message}"

Return ONLY a valid JSON object with a single boolean field "is_confirmed".
Example: {{"is_confirmed": true}}
"""
