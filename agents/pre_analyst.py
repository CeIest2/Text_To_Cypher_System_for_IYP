import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from utils.llm_caller import call_llm_with_tracking
from utils.helpers import load_schema_doc

logger = logging.getLogger(__name__)


class PreAnalysisResult(BaseModel):
    real_world_context: str         = Field(description="Real-world context of the question (max 3 sentences).")
    implicit_filters: Optional[str] = Field(default=None, description="Specific WHERE clause directive using a real schema property or Tag label, or null.")
    expected_data_type: str         = Field(description="Expected result type, e.g. 'Float between 0.0 and 100.0', 'List of integers (ASNs)'.")
    is_empty_result_plausible: bool = Field(description="False for major players/broad topics. True for obscure entities or highly restrictive conditions.")
    rejection_conditions: List[str] = Field(description="Specific falsifiable conditions indicating an invalid result.")
    technical_translation: str      = Field(description="One dense sentence using exact IYP node labels and relationship types for RAG vector search.")


def get_query_expectations(
    user_question: str,
    session_id: str = "pre_analyst_default",
    trace_id: str = None,
    trace_name: str = "pre_analysis"
) -> Dict[str, Any]:

    schema_doc = load_schema_doc()
    variables  = {"schema_doc": schema_doc, "question": user_question}

    response = call_llm_with_tracking(
        prompt_name="iyp-pre-analyst",
        variables=variables,
        session_id=session_id,
        model_name="gemini-2.5-flash-lite",
        trace_id=trace_id,
        trace_name=trace_name,
        tags=["pre_analyst"],
        pydantic_schema=PreAnalysisResult
    )

    if response["success"]:
        content = response["content"]
        return {
            "success": True,
            "real_world_context":        content.real_world_context,
            "expected_data_type":        content.expected_data_type,
            "is_empty_result_plausible": content.is_empty_result_plausible,
            "rejection_conditions":      content.rejection_conditions,
            "implicit_filters":          content.implicit_filters,
            "technical_translation":     content.technical_translation,
        }

    return response


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    print("\n" + "="*50 + "\nTESTING PRE-ANALYST AGENT\n" + "="*50)

    test_q = "What is Orange's market share in France?"
    result = get_query_expectations(test_q, session_id="test_pre_analyst")

    if result["success"]:
        print(f"✅ CONTEXTE:          {result['real_world_context']}")
        print(f"✅ TYPE ATTENDU:      {result['expected_data_type']}")
        print(f"✅ VIDE PLAUSIBLE ?:  {result['is_empty_result_plausible']}")
        print(f"✅ FILTRES IMPLICITES:{result['implicit_filters']}")
        print(f"✅ REJET SI:          {result['rejection_conditions']}")
        print(f"✅ TRADUCTION TECH:   {result['technical_translation']}")
    else:
        print(f"❌ FAILED: {result.get('error_message')}")

    print("="*50 + "\n")