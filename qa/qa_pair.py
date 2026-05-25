import json
import os
from datetime import datetime

GRAPH_PATH = "/mnt/data/km/llm-wiki/graph/graph_mini.json"
GRAPH_OUT_PATH = "/mnt/data/sub_agents/shared/qa/graph_mini.json"  # 增量写入路径

def create_qa_pair(question, answer, expert, escalated_at, resolved_at=None):
    """
    生成 Q&A_Pair entity 并追加到 Graph
    """
    qa_id = f"qa/{question[:20].replace(' ', '_')}_{datetime.now().strftime('%Y-%m-%d')}"
    
    qa_node = {
        "id": qa_id,
        "type": "Q&A_Pair",
        "layer": 1,
        "vault": "tech",
        "label": question[:50],
        "description": f"{question} / {answer}",
        "metadata": {
            "question": question,
            "answer": answer,
            "expert": expert,
            "escalated_at": escalated_at,
            "resolved_at": resolved_at
        }
    }
    
    # 追加写入（增量更新）
    out_path = os.path.join(os.path.dirname(GRAPH_PATH), "graph_mini.json")
    if os.path.exists(out_path):
        with open(out_path) as f:
            g = json.load(f)
    else:
        g = {"nodes": [], "edges": []}
    
    g["nodes"].append(qa_node)
    
    with open(out_path, 'w') as f:
        json.dump(g, f, ensure_ascii=False)
    
    return qa_id