import os
import sys
import json
from langchain_core.messages import HumanMessage

# Add project root to path
sys.path.insert(0, os.getcwd())

from ai.agent import app as agent_app

def test_normal_path(question):
    print(f"\n[TEST] Question: {question}")
    state = {"question": question, "context": [], "numerical_result": "", "risk_data": {}}
    
    steps = []
    final_prompt = ""
    
    print("Normal Path Execution (LangGraph Nodes):")
    for event in agent_app.stream(state):
        for node_name, output in event.items():
            print(f"  -> Finished Node: {node_name}")
            steps.append(node_name)
            if node_name == "generate_response":
                final_prompt = output["final_answer"]
    
    if "categorize_intent" in steps and "generate_response" in steps:
        print("SUCCESS: Normal Path executed correctly.")
        if final_prompt:
            print(f"Final Prompt/Response (first 100 chars): {final_prompt[:100]}...")
    else:
        print("FAILURE: Normal Path did not execute expected nodes.")

if __name__ == "__main__":
    print("=== AI Normal Path (LangGraph) Verification ===")
    
    # 1. RAG with keywords NOT in Fast Path (list, get, tell)
    test_normal_path("List the lab results for 10001725.")
    test_normal_path("Get the sodium levels for subject 10001725.")
    
    # 2. General Knowledge (No ID)
    test_normal_path("What is the clinical significance of White Blood Cell counts?")
    
    # 3. System-wide Count (No ID)
    test_normal_path("How many abnormal results are in the database?")
    
    # 4. Risk without specific "assessment/prediction" keywords
    test_normal_path("Tell me about the health risk for patient 10014354.")
