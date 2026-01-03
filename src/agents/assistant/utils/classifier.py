import json
from src.utils.tracing import logger
from src.agents.assistant.prompts import CLASSIFICATION_SYSTEM, CLASSIFICATION_PROMPT
from src.memory.singleton import get_memory_manager

def classify_confirmation(user_message: str) -> bool:
    """
    Classify whether the user is confirming the SRS generation using OpenAI Client
    """
    client = get_memory_manager().get_client()
    
    prompt = CLASSIFICATION_PROMPT.format(user_message=user_message)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": CLASSIFICATION_SYSTEM},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        logger.log("CLASSIFIER", f"Classification result: {data}", level="INFO")
        return data.get("is_confirmed", False)
        
    except Exception as e:
        logger.log("CLASSIFIER_ERROR", f"Failed to classify confirmation: {e}", level="ERROR")
        # Default to False for safety
        return False
