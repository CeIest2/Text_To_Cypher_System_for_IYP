import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from utils.llm_caller import call_llm_with_tracking
from utils.helpers import load_schema_doc
from typing import List, Optional

logger = logging.getLogger(__name__)


class PreAnalysisResult(BaseModel):
    real_world_context: str         = Field(description="Brief explanation of the real-world context based on your general knowledge.")
    implicit_filters: Optional[str] = Field(default=None, description="Clear instructions for the Generator to apply a semantic WHERE clause (e.g., 'Filter AS nodes to only include ISPs, excluding CDNs and Cloud providers') OR null.")
    expected_data_type: str         = Field(description="E.g., Float, List of strings, Integer...")
    is_empty_result_plausible: bool = Field(description="false if querying data about a major global player or a broad topic (empty result is a code error). true if querying an obscure player or a highly restrictive condition.")
    rejection_conditions: List[str] = Field(description="List of specific cases where the result MUST be considered an error (e.g., 'The result is an empty list []', 'The value is greater than 100', 'The list contains fewer than 3 items').")

def get_query_expectations(user_question: str, session_id: str = "pre_analyst_default", trace_id: str = None, trace_name: str = "pre_analysis") -> Dict[str, Any]:
    
    schema_doc  = load_schema_doc()
    variables   = {"schema_doc": schema_doc, "question": user_question}
    
    response = call_llm_with_tracking(prompt_name="iyp-pre-analyst", variables=variables, session_id=session_id, model_name="gemini-2.5-flash", trace_id=trace_id, trace_name=trace_name, tags=["pre_analyst"], pydantic_schema=PreAnalysisResult)
    
    if response["success"]:
        content = response["content"] 
        
        return {"success": True, "real_world_context": content.real_world_context, "expected_data_type": content.expected_data_type, "is_empty_result_plausible": content.is_empty_result_plausible, "rejection_conditions": content.rejection_conditions,"implicit_filters": content.implicit_filters}
    
    return response









if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    print("\n" + "="*50 + "\nTESTING PRE-ANALYST AGENT\n" + "="*50)
    
    test_q = "What is Orange's market share in France?"
    result = get_query_expectations(test_q, session_id="test_pre_analyst")
    
    if result["success"]:
        print(f"✅ CONTEXTE: {result['real_world_context']}")
        print(f"✅ TYPE ATTENDU: {result['expected_data_type']}")
        print(f"✅ VIDE PLAUSIBLE ?: {result['is_empty_result_plausible']}")
        print(f"✅ FILTRES IMPLICITES: {result['implicit_filters']}")
        print(f"✅ REJET SI: {result['rejection_conditions']}")
    else:
        print(f"❌ FAILED: {result.get('error_message')}")
        
    print("="*50 + "\n")