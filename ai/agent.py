# ai/agent.py

from langgraph.graph import StateGraph, END
from ai.state import AgentState
from ai.nodes import (
    categorize_intent,
    retrieve_knowledge,
    execute_aggregation,
    predict_risk,
    generate_response
)

# ==============================================================================
# PROTOTYPE HEALTHCARE AGENT (LANGGRAPH)
# ==============================================================================
# Lean version: Graph topology moved here, logic moves to ai/nodes.py
# ==============================================================================

### Build Graph ###
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("categorize_intent", categorize_intent)
workflow.add_node("retrieve_knowledge", retrieve_knowledge)
workflow.add_node("execute_aggregation", execute_aggregation)
workflow.add_node("predict_risk", predict_risk)
workflow.add_node("generate_response", generate_response)

# Routing Logic
def route_intent(state: AgentState):
    intent = state.get("intent")
    if intent == "rag":
        return "retrieve_knowledge"
    elif intent == "count":
        return "execute_aggregation"
    elif intent == "risk":
        return "predict_risk"
    else:
        return "generate_response"

# Define Edges
workflow.set_entry_point("categorize_intent")

workflow.add_conditional_edges(
    "categorize_intent",
    route_intent,
    {
        "retrieve_knowledge": "retrieve_knowledge",
        "execute_aggregation": "execute_aggregation",
        "predict_risk": "predict_risk",
        "generate_response": "generate_response"
    }
)

workflow.add_edge("retrieve_knowledge", "generate_response")
workflow.add_edge("execute_aggregation", "generate_response")
workflow.add_edge("predict_risk", "generate_response")
workflow.add_edge("generate_response", END)

# Compile
app = workflow.compile()
