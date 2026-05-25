import json
from category_map import enrich_answer_with_category

GRAPH_PATH = "/mnt/data/km/llm-wiki/graph/graph_mini.json"

def load_graph():
    with open(GRAPH_PATH) as f:
        return json.load(f)

def get_node(node_id):
    g = load_graph()
    for n in g['nodes']:
        if n['id'] == node_id:
            return n
    return None

def generate_answer(candidate_node_id, question_text):
    """
    从 Graph 节点读取 description，拼接关联 Source，返回结构化答案
    """
    node = get_node(candidate_node_id)
    if not node:
        return {"error": f"Node {candidate_node_id} not found"}
    
    description = node.get('description', '') or node.get('markdown', '')
    # Strip markdown
    if description.startswith('---'):
        description = description.split('---', 2)[-1]
    
    # Get source nodes via edges
    g = load_graph()
    edges = g.get('edges', [])
    source_ids = [e['target'] for e in edges if e.get('source') == candidate_node_id and e.get('target', '').endswith('/sources/')][:3]
    
    sources = []
    for sid in source_ids:
        for n in g['nodes']:
            if n['id'] == sid:
                src = n.get('markdown', '') or n.get('description', '') or ''
                if src.startswith('---'):
                    src = src.split('---', 2)[-1][:200]
                sources.append({"id": sid, "preview": src[:100]})
    
    return {
        "answer": description[:500],
        "source_nodes": sources,
        "vault": node.get('vault'),
        "layer": node.get('layer'),
        "confidence": 0.85,
        "category": enrich_answer_with_category(candidate_node_id, node.get('layer', 2))
    }

if __name__ == "__main__":
    import sys
    nid = sys.argv[1] if len(sys.argv) > 1 else "tech/concepts/tech"
    r = generate_answer(nid, "")
    print(json.dumps(r, ensure_ascii=False, indent=2))