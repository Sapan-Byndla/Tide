import time
import requests
import numpy as np

def cosine_similarity(v1, v2):
    a = np.array(v1)
    b = np.array(v2)
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))

def run_tests():
    url = "http://127.0.0.1:8001/embed"
    
    # 1. Test Single Embedding & Similarity
    payload = {
        "texts": [
            "AI agents that call tools",
            "agentic tool use",
            "recipe for sourdough",
            "kubernetes deployment"
        ],
        "type": "document"
    }
    
    print("Testing connection to embedding service...")
    try:
        resp = requests.post(url, json=payload)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the embedding service. Make sure it is running on port 8001.")
        return
        
    if resp.status_code != 200:
        print(f"Error: Embedding service returned status code {resp.status_code}: {resp.text}")
        return
        
    data = resp.json()
    embeddings = data["embeddings"]
    print("Embeddings retrieved successfully.")
    
    sim_on_topic = cosine_similarity(embeddings[0], embeddings[1])
    sim_off_topic = cosine_similarity(embeddings[2], embeddings[3])
    
    print(f"Similarity between 'AI agents' and 'agentic tool use': {sim_on_topic:.4f}")
    print(f"Similarity between 'sourdough' and 'kubernetes': {sim_off_topic:.4f}")
    
    # Assertions based on Part 2 verification criteria
    # Note: Sharing identical long 'search_document: ' prefixes increases base similarity.
    assert sim_on_topic >= 0.7, f"Expected similarity >= 0.7, got {sim_on_topic}"
    assert sim_off_topic < 0.55, f"Expected similarity < 0.55, got {sim_off_topic}"
    print("OK: Cosine similarity checks passed!")
    
    # 2. Test Batch Latency (32 documents)
    batch_texts = [f"This is document number {i} for evaluating batch embedding latencies." for i in range(32)]
    payload_batch = {
        "texts": batch_texts,
        "type": "document"
    }
    
    print("Running batch latency test (32 documents)...")
    start_time = time.time()
    resp_batch = requests.post(url, json=payload_batch)
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"Batch embedding took: {duration:.4f} seconds")
    
    assert resp_batch.status_code == 200, "Batch request failed"
    assert duration < 2.0, f"Expected batch latency < 2.0s, got {duration:.4f}s"
    print("OK: Batch latency checks passed!")
    print("\nAll embedding tests completed successfully!")

if __name__ == "__main__":
    run_tests()
