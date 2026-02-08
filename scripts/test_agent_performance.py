"""
Test to measure the actual time spent in each node of the agent graph
"""
import time
from ai.agent import app as agent_app

def test_agent_performance():
    question = "What is glucose?"
    state = {
        "question": question,
        "context": [],
        "numerical_result": "",
        "risk_data": {}
    }
    
    print("Testing agent graph performance...")
    print(f"Question: {question}")
    print("=" * 60)
    
    start = time.time()
    
    for event in agent_app.stream(state):
        for node_name, output in event.items():
            elapsed = time.time() - start
            print(f"[{elapsed:.1f}s] Node '{node_name}' completed")
            
            # Show some details
            if node_name == "categorize_intent":
                print(f"  Intent: {output.get('intent')}")
                print(f"  Entities: {output.get('entities')}")
            elif node_name == "retrieve_knowledge":
                print(f"  Context chunks: {len(output.get('context', []))}")
            elif node_name == "generate_response":
                prompt_len = len(output.get('final_answer', ''))
                print(f"  Final prompt length: {prompt_len} chars")
    
    total = time.time() - start
    print("=" * 60)
    print(f"Total graph execution time: {total:.1f}s")

if __name__ == "__main__":
    test_agent_performance()
