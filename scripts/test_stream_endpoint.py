"""
Diagnostic script to test the /chat/stream endpoint and identify issues.
"""

import requests
import json
import time
import sys

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
STREAM_ENDPOINT = "http://127.0.0.1:8000/chat/stream"
MODEL = "tinyllama:latest"

def test_ollama_connection():
    """Test if Ollama is running and accessible"""
    print("=" * 60)
    print("TEST 1: Ollama Connection")
    print("=" * 60)
    
    try:
        # Test basic connectivity
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print("[OK] Ollama is running")
            print(f"Available models: {[m['name'] for m in models]}")
            
            # Check if tinyllama is available
            if any("tinyllama" in m['name'] for m in models):
                print("[OK] tinyllama model is available")
                return True
            else:
                print("[ERROR] tinyllama model NOT found")
                print("   Run: ollama pull tinyllama")
                return False
        else:
            print(f"[ERROR] Ollama returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to Ollama at http://127.0.0.1:11434")
        print("   Make sure Ollama is running: ollama serve")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def test_ollama_generation():
    """Test if Ollama can generate responses"""
    print("\n" + "=" * 60)
    print("TEST 2: Ollama Generation Speed")
    print("=" * 60)
    
    payload = {
        "model": MODEL,
        "prompt": "What is glucose?",
        "stream": False,
        "options": {"temperature": 0}
    }
    
    try:
        start = time.time()
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("response", "")
            print(f"[OK] Generation successful in {elapsed:.2f}s")
            print(f"Response preview: {content[:100]}...")
            
            if elapsed > 30:
                print("[WARNING] Generation took >30s (very slow)")
            elif elapsed > 10:
                print("[WARNING] Generation took >10s (slow)")
            
            return True
        else:
            print(f"[ERROR] Generation failed with status {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out after 60s")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def test_ollama_streaming():
    """Test if Ollama streaming works"""
    print("\n" + "=" * 60)
    print("TEST 3: Ollama Streaming")
    print("=" * 60)
    
    payload = {
        "model": MODEL,
        "prompt": "What is glucose?",
        "stream": True,
        "options": {"temperature": 0}
    }
    
    try:
        start = time.time()
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60)
        
        chunks_received = 0
        first_chunk_time = None
        
        for line in response.iter_lines():
            if not line:
                continue
            
            chunk = json.loads(line)
            if "response" in chunk and chunk["response"]:
                chunks_received += 1
                if first_chunk_time is None:
                    first_chunk_time = time.time() - start
                    print(f"[OK] First chunk received in {first_chunk_time:.2f}s")
            
            if chunk.get("done"):
                break
        
        elapsed = time.time() - start
        print(f"[OK] Streaming completed in {elapsed:.2f}s")
        print(f"   Total chunks: {chunks_received}")
        
        if first_chunk_time and first_chunk_time > 10:
            print("[WARNING] First chunk took >10s (slow)")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def test_stream_endpoint():
    """Test the FastAPI /chat/stream endpoint"""
    print("\n" + "=" * 60)
    print("TEST 4: FastAPI /chat/stream Endpoint")
    print("=" * 60)
    
    payload = {
        "question": "What is glucose?"
    }
    
    try:
        print("Sending request to /chat/stream...")
        start = time.time()
        
        response = requests.post(
            STREAM_ENDPOINT,
            json=payload,
            stream=True,
            timeout=90
        )
        
        if response.status_code != 200:
            print(f"[ERROR] Endpoint returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        print("[OK] Connection established, waiting for events...")
        
        events_received = 0
        first_event_time = None
        tokens_received = 0
        
        for line in response.iter_lines():
            if not line:
                continue
            
            line_str = line.decode('utf-8')
            
            if line_str.startswith("data: "):
                data_str = line_str[6:]  # Remove "data: " prefix
                
                try:
                    event = json.loads(data_str)
                    events_received += 1
                    
                    if first_event_time is None:
                        first_event_time = time.time() - start
                        print(f"[OK] First event received in {first_event_time:.2f}s")
                    
                    event_type = event.get("type")
                    content = event.get("content", "")
                    
                    if event_type == "status":
                        print(f"   Status: {content}")
                    elif event_type == "token":
                        tokens_received += 1
                        if tokens_received == 1:
                            print(f"   First token: '{content}'")
                    elif event_type == "done":
                        print("[OK] Stream completed")
                        break
                        
                except json.JSONDecodeError:
                    print(f"[WARNING] Could not parse event: {data_str}")
        
        elapsed = time.time() - start
        print(f"\n[SUMMARY]:")
        print(f"   Total time: {elapsed:.2f}s")
        print(f"   Events received: {events_received}")
        print(f"   Tokens received: {tokens_received}")
        
        if tokens_received == 0:
            print("[CRITICAL] No tokens were received!")
            print("   This explains why no output is displayed")
            return False
        
        if first_event_time and first_event_time > 30:
            print("[WARNING] First event took >30s (very slow)")
        
        return tokens_received > 0
        
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to FastAPI server at http://127.0.0.1:8000")
        print("   Make sure the server is running: uvicorn app.main:app --reload")
        return False
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out after 90s")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n[DIAGNOSTIC] STREAM ENDPOINT DIAGNOSTIC TOOL\n")
    
    results = {
        "ollama_connection": test_ollama_connection(),
        "ollama_generation": test_ollama_generation(),
        "ollama_streaming": test_ollama_streaming(),
        "stream_endpoint": test_stream_endpoint()
    }
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    if not all_passed:
        print("\n[WARNING] Some tests failed. Review the output above for details.")
        sys.exit(1)
    else:
        print("\n[SUCCESS] All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
