# app/services/chat_handler.py

import json
import re
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from ai.agent import app as agent_app
from ai.llm_client import LocalChatOllama as ChatOpenAI
from ai.prompts import LIGHTWEIGHT_RAG_PROMPT
from ai.risk_model import predict_patient_risk
from app.vector.chroma_store import search_documents
from app.queries.sql_templates import get_count_query
from app.services.context_service import truncate_patient_history
from database.db import get_connection
from ai.config import CHATBOT_GREETINGS, SUPPORTED_LAB_TESTS

async def handle_chat_stream(question: str):
    """
    Streaming handler for chatbot queries:
    - Implements FastPaths for common queries
    - Falls back to LangGraph agent for complex logic
    """
    lower_q = question.lower().strip()
    patient_match = re.search(r'\d{6,}', question)
    
    # ============================================================
    # FAST PATH 0: GREETINGS & SHORT INPUTS
    # ============================================================
    if lower_q in CHATBOT_GREETINGS or len(lower_q) <= 2:
        yield f"data: {json.dumps({'type': 'token', 'content': 'Hello! I am your Lab Assistant. How can I help you with your lab results or medical questions today?'})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    # ============================================================
    # FAST PATH 1: COUNT Intent
    # ============================================================
    is_count = any(w in lower_q for w in ["how many", "total", "count", "number of", "records"])
    if is_count and patient_match:
        yield f"data: {json.dumps({'type': 'status', 'content': 'Aggregating records...'})}\n\n"
        subject_id = patient_match.group()
        status = "CRITICAL" if "critical" in lower_q else "ABNORMAL" if "abnormal" in lower_q else "NORMAL" if "normal" in lower_q else None
        
        test_found = None
        for t in SUPPORTED_LAB_TESTS:
            if t.lower() in lower_q:
                test_found = t
                break

        entities = {"subject_id": subject_id}
        if status: entities["status"] = status
        if test_found: entities["test_name"] = test_found
        
        try:
            sql, params = get_count_query(entities)
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(sql, params)
            count = cur.fetchone()[0]
            conn.close()
            
            status_desc = f"{status} " if status else ""
            test_desc = f"{test_found} " if test_found else ""
            
            prompt = (
                f"You are a factual data reporter. Based ONLY on the following information, state the count clearly.\n"
                f"DATA: Patient {subject_id} has exactly {count} {status_desc}{test_desc}laboratory records.\n"
                f"RULE: Do NOT provide medical advice. Do NOT guess test values. Do NOT explain what the test means. Just state the count."
            )
            
            yield f"data: {json.dumps({'type': 'status', 'content': 'Reporting count...'})}\n\n"
            llm = ChatOpenAI(streaming=True)
            async for chunk in llm.astream([HumanMessage(content=prompt)]):
                if chunk.content: yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'token', 'content': f'Error calculating counts: {str(e)}'})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    # ============================================================
    # FAST PATH 2: RISK Intent
    # ============================================================
    is_risk = any(w in lower_q for w in ["risk", "prediction", "assessment"])
    if is_risk and patient_match:
        yield f"data: {json.dumps({'type': 'status', 'content': 'Predicting patient risk...'})}\n\n"
        subject_id = int(patient_match.group())
        risk_data = predict_patient_risk(subject_id)
        
        if "error" in risk_data:
            prompt = f"Explain that we couldn't calculate risk for patient {subject_id} due to: {risk_data['error']}"
        else:
            prompt = f"Based on our Random Forest model, patient {subject_id} has a {risk_data['risk_label']} risk level ({risk_data['confidence']}% confidence). Explain this to the user."
        
        yield f"data: {json.dumps({'type': 'status', 'content': 'Generating clinical summary...'})}\n\n"
        llm = ChatOpenAI(streaming=True)
        async for chunk in llm.astream([HumanMessage(content=prompt)]):
            if chunk.content: yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    # ============================================================
    # FAST PATH 3: Patient RAG
    # ============================================================
    is_history = any(w in lower_q for w in ["results", "latest", "show", "summarize", 
    "overall status","summary", "what are", "history", "report"])
    if is_history and patient_match and not is_count:
        yield f"data: {json.dumps({'type': 'status', 'content': 'Retrieving clinical records...'})}\n\n"
        subject_id = patient_match.group()
        
        results = search_documents(question, k=1, where={"subject_id": subject_id})
        
        if results:
            doc = results[0]
            test_match = re.search(r'(Glucose|Hemoglobin|Chloride|Creatinine|WBC|Sodium|Potassium)', question, re.I)
            test_name = test_match.group().lower() if test_match else ""
            
            content = truncate_patient_history(doc['content'], doc['metadata'], test_name)
            context_str = f"METADATA: {doc['metadata']}\nCONTENT:\n{content}"
            
            prompt = LIGHTWEIGHT_RAG_PROMPT.format(
                subject_id=subject_id,
                context_str=context_str,
                question=question
            )
            yield f"data: {json.dumps({'type': 'status', 'content': 'Synthesizing report...'})}\n\n"
            llm = ChatOpenAI(streaming=True)
            async for chunk in llm.astream([HumanMessage(content=prompt)]):
                if chunk.content: yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'token', 'content': f'No clinical history found for patient {subject_id}.'})}\n\n"
            
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    # ============================================================
    # NORMAL PATH: Full Agent Graph
    # ============================================================
    state = {"question": question, "context": [], "numerical_result": "", "risk_data": {}}
    final_prompt = ""
    
    for event in agent_app.stream(state):
        for node_name, output in event.items():
            if node_name == "generate_response":
                final_prompt = output["final_answer"]
            else:
                yield f"data: {json.dumps({'type': 'status', 'content': f'Node {node_name} finished...'})}\n\n"

    if final_prompt:
        if final_prompt.startswith("DIRECT_RESPONSE: "):
            content = final_prompt.replace("DIRECT_RESPONSE: ", "")
            yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
        else:
            llm = ChatOpenAI(streaming=True)
            yield f"data: {json.dumps({'type': 'status', 'content': 'Synthesizing final answer...'})}\n\n"
            
            async for chunk in llm.astream([HumanMessage(content=final_prompt)]):
                if chunk.content:
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
    
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
