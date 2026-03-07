import csv
from datetime import datetime
import json
import time
import uuid
import os
import threading
import concurrent.futures
from agents.orchestrator import run_autonomous_loop


file_lock = threading.Lock()

def process_single_test(index, row, benchmark_session_id, report_filename, results, detailed_logs):
    """Fonction qui gère un seul test. Sera exécutée en parallèle par les threads."""
    task_id          = row['Task ID']
    difficulty       = row['Difficulty Level']
    prompt           = row['Prompt']
    canonical_cypher = row['Canonical Solution']
    
    print(f"\n[Thread] ⏳ Démarrage TEST {index + 1} | Task: {task_id} | Diff: {difficulty}")
    
    start_time = time.time()
    failure_reason = None
    
    try:
        agent_result = run_autonomous_loop(prompt, session_id=benchmark_session_id)
        status       = agent_result.get("status", "FAILED")
        iterations   = agent_result.get("iterations", 0)
        final_cypher = agent_result.get("cypher", "None")
        
        if status == "FAILED":
            if "reason" in agent_result:
                failure_reason = agent_result["reason"]
            elif iterations > 0:
                failure_reason = f"Max retries reached ({iterations} essais épuisés)"
            else:
                failure_reason = "Échec inexpliqué renvoyé par l'orchestrateur"

    except Exception as e:
        status       = "FAILED"
        iterations   = 0
        final_cypher = "None"
        failure_reason = f"Code Crash (Exception): {str(e)}"
        
    elapsed_time = time.time() - start_time
    
    with file_lock:
        if difficulty not in results["by_difficulty"]:
            results["by_difficulty"][difficulty] = {"total": 0, "success": 0, "failed": 0}

        results["global"]["total"] += 1
        results["by_difficulty"][difficulty]["total"] += 1
        
        if status == "SUCCESS":
            results["global"]["success"] += 1
            results["by_difficulty"][difficulty]["success"] += 1
            print(f"✅ [Test {index + 1}] SUCCÈS en {iterations} itérations ({elapsed_time:.2f}s)")
        else:
            results["global"]["failed"] += 1
            results["by_difficulty"][difficulty]["failed"] += 1
            print(f"❌ [Test {index + 1}] ÉCHEC ({elapsed_time:.2f}s) ➔ Raison : {failure_reason}")
        
        current_success = results["global"]["success"]
        current_total = results["global"]["total"]
        current_rate = (current_success / current_total) * 100
        print(f"📈 SCORE ACTUEL : {current_success}/{current_total} ({current_rate:.2f}%)")
        
        detailed_logs.append({
            "test_index": index + 1,
            "task_id": task_id,
            "difficulty": difficulty,
            "prompt": prompt,
            "status": status,
            "failure_reason": failure_reason,
            "iterations_used": iterations,
            "time_seconds": round(elapsed_time, 2),
            "generated_cypher": final_cypher,
            "canonical_cypher": canonical_cypher
        })
        
        with open(report_filename, "w", encoding="utf-8") as f:
            json.dump({
                "session_id": benchmark_session_id,
                "last_updated": datetime.now().isoformat(),
                "stats_current_run": results,
                "details": detailed_logs
            }, f, indent=4, ensure_ascii=False)



def run_cyphereval_benchmark(csv_file_path: str, limit: int = None, start_at: int = 0, max_workers: int = 10):
    results = {
        "global": {"total": 0, "success": 0, "failed": 0},
        "by_difficulty": {}
    }
    detailed_logs = []
    
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    report_filename = f"benchmark_report_{date_str}.json"
    benchmark_session_id = f"benchmark_cyphereval_{date_str}_{uuid.uuid4().hex[:4]}"
    
    print(f"🚀 Démarrage du benchmark PARALLÈLE (x{max_workers} threads) sur {csv_file_path}...")
    print(f"📝 Les résultats seront sauvegardés en temps réel dans : {report_filename}")
    
    tasks_to_run = []
    
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = list(csv.DictReader(file))
        for index, row in enumerate(reader):
            if index < start_at:
                continue
            if limit and len(tasks_to_run) >= limit:
                break
            tasks_to_run.append((index, row))
            
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_single_test, index, row, benchmark_session_id, report_filename, results, detailed_logs)
            for index, row in tasks_to_run
        ]
        
        concurrent.futures.wait(futures)

    print("\n" + "*"*50)
    print("🏆 RÉSULTATS DU BENCHMARK (FINI) 🏆")
    print("*"*50)
    
    if results["global"]["total"] > 0:
        global_rate = (results["global"]["success"] / results["global"]["total"]) * 100
        print(f"🌍 Taux de succès GLOBAL : {global_rate:.2f}% ({results['global']['success']}/{results['global']['total']})")
        
        print("\n📊 Détail par difficulté :")
        for diff, stats in results["by_difficulty"].items():
            if stats["total"] > 0:
                rate = (stats["success"] / stats["total"]) * 100
                print(f"  - {diff} : {rate:.2f}% ({stats['success']}/{stats['total']})")
    else:
        print("Aucun test n'a été exécuté.")

    with open("benchmark_report.json", "w", encoding="utf-8") as f:
        json.dump(detailed_logs, f, indent=4)
        
    print("\n📝 Un rapport détaillé a été sauvegardé dans 'benchmark_report.json'")

if __name__ == "__main__":
    run_cyphereval_benchmark("variation-A.csv", limit=None, start_at=0, max_workers=5)