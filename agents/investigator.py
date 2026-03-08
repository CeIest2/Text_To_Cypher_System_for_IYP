import json
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from utils.llm_caller import call_llm_with_tracking
from DataBase.IYP_connector import test_cypher_on_iyp_traced

logger = logging.getLogger(__name__)

class InvestigatorDiagnostic(BaseModel):
    hypotheses: str         = Field(description="A brief explanation of what might have caused the failure based on the error message and the query structure.")
    test_queries: List[str] = Field(description="A list of 1 to 3 simple TEST Cypher queries to validate your hypotheses. Example: [\"MATCH (c:Country {country_code: 'GB'}) RETURN c LIMIT 1\"]")

class InvestigatorSynthesis(BaseModel):
    investigation_report: str = Field(description="Write your report using ONLY factual descriptions of the test results. Example: 'Test 1 returned 5 rows with relationship COUNTRY. Test 2 returned null for a.country_code.'")

def run_investigation(question: str, failed_cypher: str, error_message: str, session_id: str, trace_id: str = None, previous_history: str = "No previous attempts.", trace_prefix: str = "") -> Dict[str, Any]:
    logger.info("🕵️‍♂️ Starting Investigation Phase...")

    diag_vars     = {"question": question, "failed_cypher": failed_cypher, "error_message": error_message, "previous_history": previous_history}
    diag_response = call_llm_with_tracking(prompt_name="iyp-investigator-diagnostic", variables=diag_vars, session_id=session_id, trace_id=trace_id, trace_name=f"{trace_prefix} Investigator Diagnostic".strip(), tags=["investigator"], pydantic_schema=InvestigatorDiagnostic)

    if not diag_response["success"]:
        return {"report": f"Investigator Error (Diagnostic): {diag_response['error_message']}", "queries_tested": []}

    diag_data    = diag_response["content"] 
    test_queries = diag_data.test_queries

    if not test_queries:
        return {"report": "The investigator did not find any relevant tests to perform.", "queries_tested": []}

    test_results_summary = []
    for i, q in enumerate(test_queries[:3]):
        logger.info(f"🕵️‍♂️ Executing test {i+1}: {q}")
        db_res = test_cypher_on_iyp_traced(q)
        
        if db_res.get("success"):
            data_str = json.dumps(db_res.get('data'), ensure_ascii=False, default=str)[:500]
            test_results_summary.append(f"Test Query: {q}\nResult: {data_str}")
        else:
            test_results_summary.append(f"Test Query: {q}\nResult: ERROR - {db_res.get('message')}")

    synth_vars = {"question": question, "failed_cypher": failed_cypher, "test_results": "\n\n".join(test_results_summary)}
    
    synth_response = call_llm_with_tracking(prompt_name="iyp-investigator-synthesis", variables=synth_vars, session_id=session_id, trace_id=trace_id, trace_name=f"{trace_prefix} Investigator Synthesis".strip(), tags=["investigator"], pydantic_schema=InvestigatorSynthesis)

    if synth_response["success"]:
        synth_data = synth_response["content"] 
        return {"report": synth_data.investigation_report, "queries_tested": test_queries}
            
    return {"report": "Investigation synthesis failed.", "queries_tested": test_queries}