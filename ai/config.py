# ai/config.py

# --- Supported Lab Tests ---
SUPPORTED_LAB_TESTS = [
    "RBC", "WBC", "Hematocrit", "Hemoglobin", "Platelets", 
    "Chloride", "Bicarbonate", "Sodium", "Potassium", 
    "Creatinine", "Glucose", "Urea Nitrogen"
]

# --- Chatbot Greetings ---
CHATBOT_GREETINGS = [
    "hi", "hello", "hey", "good morning", "good afternoon", 
    "hii", "hiii", "h", "help", "ok", "yes", "no"
]

# --- LLM Settings ---
OLLAMA_HOST = "http://127.0.0.1:11434"
OLLAMA_URL_GENERATE = f"{OLLAMA_HOST}/api/generate"
OLLAMA_URL_CHAT = f"{OLLAMA_HOST}/api/chat"
DEFAULT_MODEL = "tinyllama:latest"

# --- Clinical Guardrails ---
SAFE_FALLBACK = (
    "Some laboratory values are outside expected ranges. "
    "These findings may warrant clinical review by a healthcare professional."
)
# --- Out-of-Scope Response ---
UNSUPPORTED_RESPONSE = (
    "I am sorry, but I am a specialized Lab Assistant. I can only help you with questions "
    "about laboratory results, clinical medical history, and health risk predictions. "
    "I cannot assist with general knowledge, non-medical advice, or other unrelated tasks."
    "Example: What is sodium level of patient 1234567? - patient specific"
    "Example: What is the total lab results? - count specific"
    "Example: What is the risk of patient 1234567? - risk specific"
)
