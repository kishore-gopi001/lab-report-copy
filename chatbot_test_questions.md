# Chatbot Test Questions

This file contains sample questions categorized by their expected intent. Use these to verify the chatbot's performance and guardrails.

## 1. RAG (Patient History & Medical Knowledge)
*Queries about specific patient records or general medical terminology.*

1. "Summarize the lab results for patient 10014354."
2. "What are the latest glucose results for patient 10001725?"
3. "Can you show me the history of Hemoglobin for subject 10014354?"
4. "What does it mean if a Chloride result is marked as ABNORMAL?"
5. "Summarize the overall clinical status for patient 10001725."

## 2. COUNT (Quantitative Data)
*Questions focused on the number of records or patient frequencies.*

1. "How many total lab records does patient 10014354 have?"
2. "How many CRITICAL results are there for subject 10001725?"
3. "What is the total count of ABNORMAL glucose tests in the system?" (General system-wide count)
4. "Count the number of Sodium tests performed for patient 10014354."
5. "How many patients currently have a CRITICAL status record?"

## 3. RISK (ML Prediction)
*Requests for clinical health risk assessments using the Random Forest model.*

1. "What is the clinical health risk for patient 10014354?"
2. "Perform a risk assessment for subject 10001725."
3. "Is patient 10014354 at high risk based on their latest results?"
4. "Calculate the risk level for subject 10001725 and explain the confidence."
5. "Show me the risk prediction for patient 10014354."

## 4. UNSUPPORTED (Out-of-Scope)
*Non-medical or out-of-scope queries test the guardrails and fallback responses.*

1. "What is the weather like in New York today?" (General knowledge)
2. "Tell me a joke about computers." (Non-medical humor)
3. "Can you help me write a Python script to sort a list?" (General coding)
4. "Who won the last world cup?" (Sports/News)
5. "How do I make chocolate cake?" (Recipes/Cooking)
