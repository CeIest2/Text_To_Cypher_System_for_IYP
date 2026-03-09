import os
import json
import logging
from dotenv import load_dotenv, load_load_dotenv
from neo4j import GraphDatabase
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAG_URI      = os.getenv("RAG_URI", "bolt://localhost:7687")
RAG_USER     = os.getenv("RAG_USER", "neo4j")
RAG_PASSWORD = os.getenv("RAG_PASSWORD", "password")
JSON_PATH    = "docs/few_shot_examples.json"

embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

def setup_rag():
    logger.info("🔌 Connexion à la base RAG locale...")
    driver = GraphDatabase.driver(RAG_URI, auth=(RAG_USER, RAG_PASSWORD))

    with driver.session() as session:
        session.run("MATCH (n:CypherExample) DETACH DELETE n")
        
        logger.info("🏗️ Création de l'index vectoriel...")
        session.run("""
            CREATE VECTOR INDEX example_intent_embedding IF NOT EXISTS
            FOR (n:CypherExample) ON (n.embedding)
            OPTIONS {indexConfig: {
             `vector.dimensions`: 768,
             `vector.similarity_function`: 'cosine'
            }}
        """)

        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            examples = json.load(f)

        logger.info(f"🧠 Génération des embeddings pour {len(examples)} exemples...")
        
        for ex in examples:
            intent = ex["intent"]
            cypher = ex["cypher"]
            
            vector = embeddings.embed_query(intent)
            
            session.run("""
                CREATE (n:CypherExample {
                    intent: $intent,
                    cypher: $cypher,
                    embedding: $embedding
                })
            """, intent=intent, cypher=cypher, embedding=vector)
            
        logger.info("✅ Base RAG locale initialisée avec succès !")

    driver.close()

if __name__ == "__main__":
    setup_rag()