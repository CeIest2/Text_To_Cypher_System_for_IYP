import os
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

def get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def load_schema_doc(filename: str = "IYP_doc.md") -> str:
    path = os.path.join(get_project_root(), "docs", filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Fichier de documentation introuvable : {path}")
        raise
    except Exception as e:
        logger.error(f"Erreur lors du chargement de {filename} : {e}")
        raise

def format_db_output(data: Any) -> str:
    if data is None:
        return "No data returned (None)."
    
    if isinstance(data, (dict, list)):
        try:
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception:
            return str(data)
    
    return str(data)

def truncate_deep_lists(data, max_items=10):
    if isinstance(data, list):
        if len(data) > max_items:
            truncated = [truncate_deep_lists(item, max_items) for item in data[:max_items]]
            truncated.append(f"... [TRONQUÉ : contient {len(data)} éléments au total]")
            return truncated
        else:
            return [truncate_deep_lists(item, max_items) for item in data]
    
    elif isinstance(data, dict): 
        return {key: truncate_deep_lists(value, max_items) for key, value in data.items()}
    else: 
        return data

def save_json_debug(data: dict, filename: str):
    debug_dir = os.path.join(get_project_root(), "debug")
    os.makedirs(debug_dir, exist_ok=True)
    
    path = os.path.join(debug_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Trace de débogage sauvegardée dans {path}")