from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SubQueryPlan(BaseModel):
    intent: str = Field(description="Clear search intent (e.g., 'Get cybersecurity score')")
    required_entities: List[str] = Field(description="Required keywords/entities (e.g., ['Cybersecurity', 'Country'])")

class ResearchPlan(BaseModel):
    steps: List[SubQueryPlan] = Field(description="Ordered sub-queries to answer the main question")

class ExecutionResult(BaseModel):
    query: str
    success: bool
    data: List[Dict[str, Any]] = []
    error: Optional[str] = None

class QueryStep(BaseModel):
    intent: str
    explanation: str
    cypher_query: str

class FinalAnswer(BaseModel):
    status: str = Field(description="SUCCESS, IMPOSSIBLE or FAILED")
    queries: List[str] = Field(description="Exact Cypher queries used")
    extracted_data: List[Dict[str, Any]] = Field(description="Raw data extracted from the Target DB")
    interpretation: str = Field(description="Final natural language answer based on extracted data")