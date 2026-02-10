# ai/prompts.py

INTENT_CAT_PROMPT = """Analyze the user's query and categorize it into exactly one of these intents:
1. 'rag': Queries about medical terms, lab tests (WBC, Glucose, etc.), or specific patient history found in clinical records.
2. 'count': Quantitative questions about lab result counts (e.g., "total abnormal results").
3. 'risk': Assessment of clinical health risk for a specific patient.
4. 'unsupported': ANY query not directly related to clinical laboratory records, medical history, or patient health risk.

CRITICAL: If the query is about weather, marriage, jokes, politics, news, general chat, or non-medical personal advice, you MUST use 'unsupported'. Do NOT try to fit general questions into medical categories.

Return JSON only: {{"intent": "...", "entities": {{"subject_id": "...", "test": "...", "status": "..."}}}}

Query: {question}
"""

# MINIMALIST PROMPT for TinyLlama (Patient Specific)
LIGHTWEIGHT_RAG_PROMPT = """Analyze these patient labs and provide a summary. 
Do NOT repeat yourself. Focus on the most important results.

PATIENT: {subject_id}
{context_str}

QUESTION: {question}
ANSWER (Concise interpretation):"""

# MINIMALIST PROMPT for TinyLlama (General Knowledge)
GENERAL_KNOWLEDGE_PROMPT = """You are a helpful clinical assistant. Answer the user's general medical question using the provided context or your internal knowledge if the context is missing.
CONTEXT: {context_str}

QUESTION: {question}
ANSWER:"""

# Fallback/General prompt for other nodes
FINAL_SYNTHESIS_PROMPT = """You are a clinical assistant. Synthesize a  medical response.
CONTEXT/DATA: {data}
QUESTION: {question}
ANSWER:"""
# Out of scope handler
OUT_OF_SCOPE_PROMPT = """You are a specialized Clinical Lab Assistant. 
The user asked: "{question}"
This is outside your scope of laboratory medical reports and clinical data.
Politely inform the user that you can only assist with lab results, medical history summaries, and health risk predictions. 
Do NOT try to answer the question if it is about weather, general news, jokes (unless medical), or non-related topics."""
