import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from ai.agent import app as agent_app

def test_query(question):
    print(f"\n--- Testing Query: '{question}' ---")
    state = agent_app.invoke({"question": question})
    print(f"Intent identified: {state.get('intent')}")
    print(f"Entities: {state.get('entities')}")
    print(f"Context found: {len(state.get('context', []))} chunks")
    print(f"Aggregation result: {state.get('numerical_result')}")
    print(f"Risk prediction: {state.get('risk_data')}")
    # print(f"Final Prompt Prepared: {state.get('final_answer')}")
    print("-" * 40)

if __name__ == "__main__":
    # Test cases
    test_query("What is glucose?") # RAG intent
    test_query("How many critical patients are there?") # Count intent
    test_query("What is the risk level for patient 10014354?") # Risk intent
