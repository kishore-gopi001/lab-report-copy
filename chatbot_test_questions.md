# Chatbot Test Questions

This file contains sample questions categorized by their expected intent. Use these to verify the chatbot's performance and guardrails.

## 1. RAG (Patient History & Medical Knowledge)
*Queries about specific patient records or general medical terminology.*

1. "Summarize the lab results for patient 10014354."
2. "What are the latest glucose results for patient 10001725?"
3. "Can you show me the history of Hemoglobin for subject 10014354?"
4. "What does it mean if a Chloride result is marked as ABNORMAL?"
5. "Summarize the overall clinical status for patient 10001725."
6. "Show me all abnormal results for patient 10014354."
7. "What are the WBC levels for subject 10001725?"
8. "List the critical lab findings for patient 10014354."
9. "Can you explain the Potassium test results for patient 10001725?"
10. "What is the trend of Creatinine levels for subject 10014354?"
11. "Show me the Bicarbonate and Sodium results for patient 10001725"
12. "What are the blood test results for patient 10014354?"
13. "Explain what normal ranges are for Glucose tests."
14. "Display the Hematocrit and RBC values for subject 10001725."
15. "What does a high Urea Nitrogen level indicate?"

## 2. COUNT (Quantitative Data)
*Questions focused on the number of records or patient frequencies.*

1. "How many total lab records does patient 10014354 have?"
2. "How many CRITICAL results are there for subject 10001725?"
3. "What is the total count of ABNORMAL glucose tests in the system?" (General system-wide count)
4. "Count the number of Sodium tests performed for patient 10014354."
5. "How many patients currently have a CRITICAL status record?"
6. "How many abnormal records are there?"
7. "How many ABNORMAL results are in the system?"
8. "What is the total count of abnormal lab tests?"
9. "Count the abnormal records"
10. "How many records have ABNORMAL status?"

### System-Wide Counts (LangGraph Agent - No Fast Path)
*Count queries WITHOUT patient IDs - these bypass the fast path and use the full LangGraph agent.*

1. "How many abnormal records are there?"
2. "How many CRITICAL results are in the system?"
3. "What is the total count of NORMAL lab tests?"
4. "Count all the abnormal cases"
5. "How many records have CRITICAL status?"
6. "What is the total number of lab results?"
7. "How many Glucose tests are abnormal?"
8. "Count the CRITICAL Sodium tests"
9. "How many WBC results are in the database?"
10. "Total abnormal Hemoglobin records?"

## 3. RISK (ML Prediction)
*Requests for clinical health risk assessments using the Random Forest model.*

1. "What is the clinical health risk for patient 10014354?"
2. "Perform a risk assessment for subject 10001725."
3. "Is patient 10014354 at high risk based on their latest results?"
4. "Calculate the risk level for subject 10001725 and explain the confidence."
5. "Show me the risk prediction for patient 10014354."

## 4. Normal Path (Full LangGraph Agent)
*These queries specifically bypass the Fast Paths to exercise the full orchestration logic.*

### RAG - General Knowledge (No Patient ID)
1. "What is the clinical significance of White Blood Cell counts?"
2. "Explain the importance of Chloride in the blood."
3. "What does it mean if a Hematocrit result is marked as ABNORMAL?"
4. "What are the common symptoms of high Glucose levels?"
5. "Explain the function of Urea Nitrogen tests."

### RAG - Detailed Retrieval (Keywords: List/Get/Tell/Trend)
1. "List the lab results for subject 10001725." (Uses 'list' - Normal Path only)
2. "Get the sodium levels for subject 10001725." (Uses 'get' - Normal Path only)
3. "Tell me about the recent RBC results for subject 10001725." (Uses 'tell' - Normal Path only)
4. "Analyze the trend for patient 10014354 across all tests." (Uses 'trend' - Normal Path only)
5. "Get the results for patient 10001725."

### Risk - Analytical Assessment
1. "Tell me about the health risk for patient 10014354." (Bypasses 'assessment/prediction' keywords)
2. "Analyze the potential health risks for subject 10001725."

## 4. UNSUPPORTED (Out-of-Scope)
*Non-medical or out-of-scope queries test the guardrails and fallback responses.*

1. "What is the weather like in New York today?" (General knowledge)
2. "Tell me a joke about computers." (Non-medical humor)
3. "Can you help me write a Python script to sort a list?" (General coding)
4. "Who won the last world cup?" (Sports/News)
5. "How do I make chocolate cake?" (Recipes/Cooking)
