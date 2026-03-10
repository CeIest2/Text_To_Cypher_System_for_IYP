# DataBase/db_client.py
import os
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class DatabaseManager:
    _drivers = {}

    @classmethod
    def get_driver(cls, db_name: str):
        if db_name not in cls._drivers:
            cls._drivers[db_name] = cls._initialize_driver(db_name)
        return cls._drivers[db_name]

    @classmethod
    def _initialize_driver(cls, db_name: str):
        if db_name == "IYP":
            uri      = os.getenv("IYP_URI")
            user     = os.getenv("IYP_USER")
            password = os.getenv("IYP_PASSWORD")
        elif db_name == "RAG":
            uri      = os.getenv("RAG_URI")
            user     = os.getenv("RAG_USER")
            password = os.getenv("RAG_PASSWORD")
        else:
            raise ValueError(f"Unknown database configuration: '{db_name}'. Expected 'IYP' or 'RAG'.")

        try:
            driver = GraphDatabase.driver(uri, auth=(user, password),max_connection_pool_size=100,connection_acquisition_timeout=2.0)
            driver.verify_connectivity()
            logger.info(f"✅ Successfully initialized Neo4j connection pool for: {db_name}")
            return driver
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j ({db_name}): {e}")
            raise

    @classmethod
    def close_all(cls):
        for name, driver in cls._drivers.items():
            driver.close()
            logger.info(f"🔌 Closed Neo4j connection pool for: {name}")
        cls._drivers.clear()