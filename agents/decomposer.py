import json, logging
from typing import Dict, Any
from utils.llm_caller import call_llm_with_tracking
from utils.helpers import load_schema_doc, parse_llm_json

logger = logging.getLogger(__name__)

def decompose_query(user_question: str, oracle_filters: str = "None", session_id: str = "decomposer_default", trace_id: str = None, trace_name: str = "query_decomposition") -> Dict[str, Any]:
    
    schema_doc = load_schema_doc()
    variables = {
        "schema_doc": schema_doc, 
        "implicit_filters": oracle_filters,
        "question": user_question
    }
    
    response = call_llm_with_tracking(
        prompt_name="iyp-decomposer", 
        variables=variables, 
        session_id=session_id, 
        model_name="gemini-2.5-flash", 
        trace_id=trace_id, 
        trace_name=trace_name, 
        tags=["decomposer"], 
        response_format="json"
    )
    
    if response["success"]:
        try:
            content = parse_llm_json(response["content"])
            return {
                "success": True, 
                "is_complex": content.get("is_complex"),
                "reasoning": content.get("reasoning"),
                "sub_questions": content.get("sub_questions", [])
            }
        except ValueError:
            logger.error("LLM output could not be parsed as JSON.")
            return {"success": False, "error_message": "LLM output format error: expected valid JSON."}
    
    return response