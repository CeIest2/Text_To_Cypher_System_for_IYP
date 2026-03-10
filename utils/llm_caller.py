import os
import logging
from typing import Dict, Any, List, Optional, Type
from dotenv import load_dotenv
from pydantic import BaseModel
from functools import lru_cache
from utils.local_prompts import LOCAL_FALLBACK_PROMPTS

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
langfuse_client = Langfuse()
logger = logging.getLogger(__name__)


@lru_cache(maxsize=32)
@lru_cache(maxsize=32)
def _fetch_prompt_template(prompt_name: str) -> ChatPromptTemplate:
    try:
        logger.info(f"📥 Fetching prompt '{prompt_name}' from Langfuse (Cache MISS)...")
        langfuse_prompt = langfuse_client.get_prompt(prompt_name)
        prompt_messages = langfuse_prompt.get_langchain_prompt()
        logger.debug(f"✅ Successfully loaded '{prompt_name}' from Langfuse.")
        return ChatPromptTemplate.from_messages(prompt_messages)
        
    except Exception as e:
        logger.warning(f"⚠️ Langfuse unreachable or prompt missing: {e}.")
        logger.warning(f"🛡️ Switching to LOCAL FALLBACK for '{prompt_name}'...")
        
        if prompt_name in LOCAL_FALLBACK_PROMPTS:
            fallback_messages = LOCAL_FALLBACK_PROMPTS[prompt_name]
            return ChatPromptTemplate.from_messages(fallback_messages)
        else:
            logger.error(f"❌ CRITICAL: No local fallback found for '{prompt_name}'!")
            raise

def _build_tracking_config(session_id: str, trace_name: str, tags: list, trace_id: str = None) -> dict:
    metadata = {"langfuse_session_id": session_id, "langfuse_trace_name": trace_name, "langfuse_tags": tags}
    if trace_id:
        metadata["langfuse_trace_id"] = trace_id
    return {"callbacks": [CallbackHandler()], "metadata": metadata, "run_name": trace_name}

def call_llm_with_tracking(
    prompt_name: str,
    variables: Dict[str, Any],
    session_id: str,
    trace_name: str = "llm_call",
    tags: List[str] = [],
    model_name: str = "gemini-2.5-flash-lite",
    temperature: float = 0.0,
    trace_id: str = None,
    pydantic_schema: Optional[Type[BaseModel]] = None,
    thinking_budget: Optional[int] = None  
) -> Dict[str, Any]:

    try:
        prompt_template = _fetch_prompt_template(prompt_name)

        llm_kwargs = {
            "model": model_name,
            "temperature": temperature,
            "google_api_key": os.getenv("GOOGLE_API_KEY"),
            "max_output_tokens": 4096,
        }
        if thinking_budget is not None:
            llm_kwargs["thinking_budget"] = thinking_budget

        llm = ChatGoogleGenerativeAI(**llm_kwargs)

        tracking_config = _build_tracking_config(session_id, trace_name, tags, trace_id=trace_id)
        tracking_config["run_name"] = trace_name

        if pydantic_schema:
            chain = prompt_template | llm.with_structured_output(pydantic_schema)
        else:
            chain = prompt_template | llm | StrOutputParser()

    except Exception as e:
        logger.error(f"Erreur d'initialisation LLM: {e}")
        return {"success": False, "content": None, "error_message": str(e)}

    try:
        logger.info(f"Appel LLM pour '{trace_name}'...")
        response_content = chain.invoke(variables, config=tracking_config)
        return {"success": True, "content": response_content, "error_message": None}

    except Exception as e:
        logger.error(f"Échec de l'exécution LLM: {e}")
        return {"success": False, "content": None, "error_message": str(e)}


if __name__ == "__main__":
    from pydantic import Field

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    class TestCypherGeneration(BaseModel):
        reasoning: str = Field(description="Explication")
        cypher: str = Field(description="Requête Cypher")
        explanation: str = Field(description="Détails")

    schema_path = "docs/IYP_doc.md"

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            real_schema_doc = f.read()
    except FileNotFoundError:
        print(f"❌ Erreur : Le fichier {schema_path} est introuvable.")
        exit(1)

    test_variables = {"schema_doc": real_schema_doc, "question": "Quelle est la part de marché (population servie) de l'AS 3215 en France ?", "previous_history": "No previous attempts."}

    result = call_llm_with_tracking(
        prompt_name="iyp-cypher-generator",
        variables=test_variables,
        session_id="test_reel_llm_001",
        trace_name="test_direct_call_reel",
        tags=["test_reel", "llm_module"],
        pydantic_schema=TestCypherGeneration
    )

    print("\n" + "="*40)
    print("RÉSULTAT DU TEST RÉEL AVEC PYDANTIC")
    print("="*40)

    if result["success"]:
        print("✅ SUCCÈS ! Réponse structurée obtenue :")
        print("-" * 40)