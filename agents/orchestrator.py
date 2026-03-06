import logging, uuid, json
from langfuse import Langfuse
from agents.pre_analyst import get_query_expectations 
from agents.request_generator import generate_cypher_query
from agents.evaluator import evaluate_cypher_result
from DataBase.IYP_connector import test_cypher_on_iyp_traced
from agents.investigator import run_investigation 
langfuse = Langfuse()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def run_autonomous_loop(question: str, max_retries: int = 9):
    run_id = uuid.uuid4().hex
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    history = "No previous attempts."
    history_log = []
    
    with langfuse.start_as_current_observation(name="Autonomous_Cypher_Pipeline", as_type="span", trace_context={"trace_id": run_id, "session_id": session_id}, input={"question": question}) as main_span:

        oracle_res          = get_query_expectations(question, session_id=session_id, trace_id=run_id)
        oracle_expectations = None
        if oracle_res.get("success"):
            oracle_expectations = {"real_world_context": oracle_res.get("real_world_context"), "expected_data_type": oracle_res.get("expected_data_type"), "is_empty_result_plausible": oracle_res.get("is_empty_result_plausible"), "rejection_conditions": oracle_res.get("rejection_conditions")}

        for attempt in range(max_retries):
            current_attempt = attempt + 1
            attempt_prefix = f"[Attempt {current_attempt}]"
            print(f"\n--- 🔄 ATTEMPT {current_attempt}/{max_retries} ---")
    
            gen_result = generate_cypher_query(question, session_id=session_id, trace_id=run_id, previous_history=history, trace_name=f"{attempt_prefix} Cypher Generation")
            
            if not gen_result["success"]:
                print(f"❌ Critical Generation Error: {gen_result.get('error_message')}")
                break

            cypher       = gen_result["cypher"]
            explanation  = gen_result["explanation"]
            db_result    = test_cypher_on_iyp_traced(cypher)
            eval_verdict = evaluate_cypher_result(question=question, cypher=cypher, explanation=explanation, db_output=db_result, session_id=session_id, trace_id=run_id, oracle_expectations=oracle_expectations, trace_name=f"{attempt_prefix} Evaluation")

            if eval_verdict.get("is_valid"):
                print(f"✅ SUCCESS at attempt {current_attempt}!")
                main_span.update(output={"final_cypher": cypher, "data": db_result.get("data")})
                return {"status": "SUCCESS","iterations": current_attempt,"cypher": cypher,"data": db_result.get("data")}
            
            else:
                error_type = eval_verdict.get('error_type')
                analysis = eval_verdict.get('analysis')
                print(f"⚠️ Validation Failed [{error_type}]. Launching Investigator...")
                
                investigation_result = run_investigation(question=question, failed_cypher=cypher, error_message=f"Error Type: {error_type} | Analysis: {analysis}", session_id=session_id, trace_id=run_id, previous_history=history,trace_prefix=attempt_prefix )
                
                investigation_report = investigation_result.get("report", "No report.")
                queries_tested       = investigation_result.get("queries_tested", [])
                
                print(f"🕵️‍♂️ Investigator Report: {investigation_report}")

                queries_tested_str = ""
                if queries_tested:
                    for i, qt in enumerate(queries_tested):
                        queries_tested_str += f"  {i+1}. {qt}\n"
                else:
                    queries_tested_str = "  Aucun test effectué.\n"

                attempt_summary = (
                                f"\n--- ATTEMPT {current_attempt} ---\n"
                                f"FAILED QUERY: {cypher}\n"
                                f"EVALUATOR REJECTION: [{error_type}] {analysis}\n"
                                f"INVESTIGATOR FACTUAL REPORT: {investigation_report}\n"
                            )
                
                if history == "No previous attempts.":
                    history = attempt_summary
                    history_log.append({
                "attempt": current_attempt,
                "cypher_tried": cypher,
                "evaluator_error": error_type,
                "investigator_facts": investigation_report
            })
                else:
                    history += attempt_summary

        print(f"❌ Failed to generate a valid query after {max_retries} attempts.")
        main_span.update(level="ERROR", status_message="Max retries reached")
        return {"status": "FAILED", "iterations": max_retries}














if __name__ == "__main__":
    q = " Quels sont les fournisseurs d'accès étrangers qui ont les plus grandes parts de marché en france ? " 
    # Quels sont les opérateurs télécoms africains qui dépendent le plus de l'infrastructure de Google ou d'Amazon pour accéder à Internet ?
    result = run_autonomous_loop(q)
    print("\nFinal Result:", json.dumps(result, indent=2))