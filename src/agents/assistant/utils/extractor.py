import json
from src.utils.tracing import logger
from src.agents.assistant.prompts import EXTRACTION_SYSTEM, EXTRACTION_PROMPT
from src.memory.singleton import get_memory_manager

def extract_requirements(user_message: str, current_requirements: dict) -> dict:
    """
    Extract requirements from user message using OpenAI Client
    """
    client = get_memory_manager().get_client()
    
    # Format existing reqs for prompt
    req_str = json.dumps(current_requirements, indent=2) if current_requirements else "{}"
    
    prompt = EXTRACTION_PROMPT.format(
        user_message=user_message,
        current_requirements=req_str
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
        
    except Exception as e:
        logger.log("EXTRACTOR_ERROR", f"Failed to extract requirements: {e}", level="ERROR")
        return {}

def merge_requirements(existing: dict, new_reqs: dict) -> dict:
    """
    Merge new requirements into existing ones without duplication
    """
    merged = existing.copy()
    
    for category, items in new_reqs.items():
        if not items:
            continue
            
        if category not in merged:
            merged[category] = []
            
        current_lower = {x.lower() for x in merged[category]}
        
        for item in items:
            if item.lower() not in current_lower:
                merged[category].append(item)
                current_lower.add(item.lower())
                
    return merged
