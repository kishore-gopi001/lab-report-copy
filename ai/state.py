from typing import Dict, List, Any, Union, TypedDict

class AgentState(TypedDict):
    """
    Maintains the state across the LangGraph workflow.
    """
    question: str
    intent: str  # One of: "rag", "count", "risk", "unsupported"
    entities: Dict[str, Any]  # Extracted entities like subject_id or test name
    context: List[str]  # Chunks retrieved from RAG
    numerical_result: Union[int, float, None, str]  # Results from SQL queries
    risk_data: Dict[str, Any]  # Output from the ML risk model
    final_answer: str  # The prompt prepared for the final LLM synthesis
