import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class BaseNeo4jClient:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def execute_read(self, query: str, params: dict = None) -> list:
        with self.driver.session() as session:
            return [record.data() for record in session.run(query, params or {})]

    def execute_write(self, query: str, params: dict = None) -> list:
        with self.driver.session() as session:
            return [record.data() for record in session.run(query, params or {})]

class TargetDBClient(BaseNeo4jClient):
    """Read-only remote database (IYP)."""
    def __init__(self):
        super().__init__(os.getenv("IYP_NEO4J_URI"), os.getenv("IYP_NEO4J_USER"), os.getenv("IYP_NEO4J_PASSWORD"))
        
    def execute_write(self, query: str, params: dict = None):
        raise PermissionError("Target DB is read-only.")

class MemoryDBClient(BaseNeo4jClient):
    """Read-write local database (RAG)."""
    def __init__(self):
        super().__init__(os.getenv("RAG_NEO4J_URI"), os.getenv("RAG_NEO4J_USER"), os.getenv("RAG_NEO4J_PASSWORD"))

target_db = TargetDBClient()
memory_db = MemoryDBClient()