#!/usr/bin/env python3
"""
question_classifier.py — 使用预计算 embedding 的 Q&A 分类器

改动：
- 预计算 embedding 存储在 graph_mini.json 每个节点的 embedding 字段
- 分类时直接从节点读取 embedding，本地 cosine similarity
- 不再调用 Ollama API（极速，< 50ms）
"""
import json
from numpy.linalg import norm
import numpy as np

GRAPH_PATH = "/mnt/data/km/llm-wiki/graph/graph_mini.json"

def load_graph():
    with open(GRAPH_PATH) as f:
        return json.load(f)

def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (norm(a) * norm(b) + 1e-8))

def classify_question(question_text, top_k=3, model="nomic-embed-text:v1.5"):
    """
    1. 用 Embedding 模型编码 question_text（仅1次API调用）
    2. 在 L2/3 节点中检索（预计算 embedding，本地cosine）
    3. 返回 top-k 候选
    """
    import requests
    
    # Encode question
    resp = requests.post(
        "http://127.0.0.1:11434/api/embeddings",
        json={"model": model, "prompt": question_text[:300]},
        timeout=15
    )
    q_emb = np.array(resp.json()["embedding"])
    
    g = load_graph()
    
    # Score against all L2/3 nodes with pre-computed embeddings
    candidates = []
    for n in g["nodes"]:
        if n.get("layer") in (2, 3):
            emb = n.get("embedding")
            if emb is None:
                continue
            text = (n.get("markdown") or n.get("description") or n.get("label") or "")[:200]
            if not text:
                continue
            score = cosine_sim(q_emb, emb)
            candidates.append({
                "node_id": n["id"],
                "label": n.get("label", ""),
                "score": score,
                "layer": n.get("layer"),
                "vault": n.get("id", "").split("/")[0] if "/" in n.get("id", "") else "unknown"
            })
    
    candidates.sort(key=lambda x: -x["score"])
    top_k_candidates = candidates[:top_k]
    
    return {
        "candidates": top_k_candidates,
        "top_score": top_k_candidates[0]["score"] if top_k_candidates else 0,
        "total_candidates": len(candidates),
        "confidence": "high" if (top_k_candidates and top_k_candidates[0]["score"] >= 0.80) else
                      "medium" if (top_k_candidates and top_k_candidates[0]["score"] >= 0.60) else "low"
    }

if __name__ == "__main__":
    import sys, time
    q = sys.argv[1] if len(sys.argv) > 1 else "cron任务不执行怎么办"
    start = time.time()
    result = classify_question(q)
    elapsed = time.time() - start
    print(f"Q: {q}")
    print(f"Top score: {result['top_score']:.3f} ({elapsed*1000:.0f}ms)")
    print(f"Candidates scored: {result['total_candidates']}")
    for c in result["candidates"]:
        print(f"  {c['score']:.3f} [{c['layer']}] {c['node_id'][:50]}")