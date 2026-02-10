import json
import re
from langchain_core.messages import HumanMessage
from ai.llm_client import LocalChatOllama as ChatOpenAI
from app.vector.chroma_store import search_documents
from ai.risk_model import predict_patient_risk
from database.db import get_connection
from ai.state import AgentState
from ai.prompts import INTENT_CAT_PROMPT, LIGHTWEIGHT_RAG_PROMPT, FINAL_SYNTHESIS_PROMPT, GENERAL_KNOWLEDGE_PROMPT, OUT_OF_SCOPE_PROMPT
from app.services.context_service import truncate_patient_history
from ai.config import SUPPORTED_LAB_TESTS, UNSUPPORTED_RESPONSE

llm = ChatOpenAI(temperature=0)

def categorize_intent(state: AgentState):
    """LLM-driven intent classification with robust heuristics."""
    prompt = INTENT_CAT_PROMPT.format(question=state['question'])
    response = llm.invoke([HumanMessage(content=prompt)])
    
    content = response.content.strip()
    
    try:
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(content)
    except Exception:
        data = {"intent": "unsupported", "entities": {}}
        
    if not isinstance(data, dict) or "intent" not in data: 
        data = {"intent": "unsupported", "entities": {}}
    if "entities" not in data or not isinstance(data["entities"], dict): 
        data["entities"] = {}
    
    lower_question = state['question'].lower()

    # --- Domain Guardrail (Heuristic) ---
    negative_keywords = [
        "marriage", "wedding", "weather", "joke", "politics", "news", "recipe", 
        "sport", "game", "movie", "song", "laptop", "computer", "phone", "price",
        "buy", "sell", "who is", "who are you", "what is your name", "travel",
        "hotel", "flight", "restaurant", "food", "coding", "programming"
    ]
    
    # 1. Catch obvious out-of-scope keywords
    if any(nw in lower_question for nw in negative_keywords):
        return {"intent": "unsupported", "entities": {}}

    # 2. Heuristic Intent Fixes
    if any(w in lower_question for w in ["show", "list", "summarize", "history", "trend", "results for", "display", "get", "tell"]):
        data["intent"] = "rag"
    
    # 3. Clinical Density Check (Safety Catch)
    # If the LLM or heuristics flagged it as RAG/Count/Risk, but there's ZERO clinical context,
    # and NO patient ID / test name extracted, force to unsupported.
    clinical_keywords = ["lab", "result", "test", "report", "clinical", "patient", "blood", "doctor", "health", "risk", "status", "subject"] + [t.lower() for t in SUPPORTED_LAB_TESTS]
    has_clinical_context = any(ck in lower_question for ck in clinical_keywords)
    
    if data["intent"] in ["rag", "count", "risk"] and not has_clinical_context:
        # Check if subject_id was extracted at least
        if "subject_id" not in data["entities"]:
            data["intent"] = "unsupported"

    
    if "critical" in lower_question: data["entities"]["status"] = "CRITICAL"
    elif "abnormal" in lower_question: data["entities"]["status"] = "ABNORMAL"
        
    id_match = re.search(r'\d{7,}', lower_question)
    if id_match:
        data["entities"]["subject_id"] = id_match.group()
    else:
        # Strictly clear subject_id if not found via regex to avoid LLM hallucinations
        data["entities"].pop("subject_id", None)
    
    for test in SUPPORTED_LAB_TESTS:
        if test.lower() in lower_question:
            data["entities"]["test"] = test
            break

    return {
        "intent": data.get("intent", "unsupported"),
        "entities": data.get("entities", {})
    }

def retrieve_knowledge(state: AgentState):
    """RAG Node using shared context service for truncation."""
    query = state['question']
    entities = state.get('entities', {})
    subject_id = entities.get('subject_id')
    test_name = entities.get('test', '')
    
    where_filter = None
    if subject_id:
        where_filter = {"subject_id": str(subject_id)}
        
    results = search_documents(query, k=1, where=where_filter)
    
    context = []
    if results:
        doc = results[0]
        content = truncate_patient_history(doc['content'], doc['metadata'], test_name)
        formatted_doc = f"METADATA: {doc['metadata']}\nCONTENT:\n{content}"
        context.append(formatted_doc)
        
    return {"context": context}

def execute_aggregation(state: AgentState):
    """Aggregator Node for SQL queries."""
    entities = state['entities']
    conn = get_connection()
    cur = conn.cursor()
    
    status = entities.get("status", "").upper()
    subject_id = entities.get("subject_id")
    
    query = "SELECT COUNT(*) FROM lab_interpretations"
    params = []
    where_clauses = []
    
    if status:
        where_clauses.append("status = ?")
        params.append(status)
    if subject_id:
        where_clauses.append("subject_id = ?")
        params.append(subject_id)
        
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    cur.execute(query, params)
    count = cur.fetchone()[0]
    conn.close()
    
    res_str = f"Found {count} records"
    if status: res_str += f" with status {status}"
    if subject_id: res_str += f" for patient {subject_id}"
    
    return {"numerical_result": res_str}

def predict_risk(state: AgentState):
    """Risk Node for ML prediction."""
    subject_id = state['entities'].get('subject_id')
    if not subject_id:
        return {"risk_data": {"error": "No patient ID found"}}
    
    risk_res = predict_patient_risk(subject_id)
    return {"risk_data": risk_res}

def generate_response(state: AgentState):
    """Synthesis Node."""
    if state.get("intent") == "rag":
        context_str = state.get('context', [""])[0] if state.get('context') else "No records found."
        subject_id = state['entities'].get('subject_id')
        
        if not state.get('context') and subject_id:
            return {"final_answer": f"DIRECT_RESPONSE: No data present related to subject {subject_id}."}

        if subject_id:
            prompt = LIGHTWEIGHT_RAG_PROMPT.format(
                subject_id=subject_id,
                context_str=context_str, 
                question=state['question']
            )
        else:
            # General Knowledge Path - check for clinical context first
            clinical_terms = ["lab", "result", "risk", "status", "patient", "blood", "test", "medical", "clinical"] + [t.lower() for t in SUPPORTED_LAB_TESTS]
            if not any(term in state['question'].lower() for term in clinical_terms):
                return {"final_answer": OUT_OF_SCOPE_PROMPT.format(question=state['question'])}

            prompt = GENERAL_KNOWLEDGE_PROMPT.format(
                context_str=context_str if "METADATA" not in context_str else "General medical query (ignoring specific patient data).",
                question=state['question']
            )
    elif state.get("intent") == "unsupported":
        return {"final_answer": f"DIRECT_RESPONSE: {UNSUPPORTED_RESPONSE}"}
    else:
        num_res = state.get('numerical_result', "")
        risk_res = state.get('risk_data', {})
        
        # Guard against halluncinating on empty data for potential missed 'unsupported'
        if not num_res and (not risk_res or "error" in risk_res):
            clinical_terms = ["lab", "result", "risk", "status", "patient", "blood", "test", "medical"] + [t.lower() for t in SUPPORTED_LAB_TESTS]
            if not any(term in state['question'].lower() for term in clinical_terms):
                return {"final_answer": f"DIRECT_RESPONSE: {UNSUPPORTED_RESPONSE}"}

        data_str = f"Stats: {num_res}. Risk: {risk_res}"
        prompt = FINAL_SYNTHESIS_PROMPT.format(data=data_str, question=state['question'])
        
    return {"final_answer": prompt}
