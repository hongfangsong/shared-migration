#!/usr/bin/env python3
"""修复 Layer 2 节点内容空洞问题：从 wiki 源文件读取实际 markdown 内容"""
import json
import re
from pathlib import Path

GRAPH_MINI = "/mnt/data/km/llm-wiki/graph/graph_mini.json"
WIKI_ROOT = Path("/mnt/data/km/llm-wiki/wiki")
OUTPUT = "/mnt/data/sub_agents/shared/qa/graph_mini_patched.json"

def strip_frontmatter(content: str) -> str:
    """去掉 frontmatter，返回正文"""
    return re.sub(r"^---\n[\\s\\S]*?\n---\n?", "", content, count=1).strip()

def load_graph():
    with open(GRAPH_MINI) as f:
        return json.load(f)

def save_graph(g, path):
    with open(path, 'w') as f:
        json.dump(g, f, ensure_ascii=False, indent=2)

def main():
    g = load_graph()
    nodes = g['nodes']
    
    fixed = 0
    skipped = 0
    errors = []
    
    for node in nodes:
        if node.get('layer') != 2:
            continue
        
        # 已有足够内容（正文超过200字符）则跳过
        existing = (node.get('markdown') or '').strip()
        if len(existing) > 200:
            skipped += 1
            continue
        
        # path stored as 'wiki/tech/concepts/xxx.md', actual file is 'tech/concepts/xxx.md'
        path_str = node.get('path', '').lstrip('wiki/')
        if not path_str:
            skipped += 1
            continue
        
        full_path = WIKI_ROOT / path_str
        if not full_path.exists():
            errors.append(f"NOT FOUND: {full_path}")
            skipped += 1
            continue
        
        try:
            content = full_path.read_text(encoding='utf-8')
            body = strip_frontmatter(content)
            
            if len(body) > 50:  # 有实质内容
                node['markdown'] = body
                fixed += 1
            else:
                skipped += 1
        except Exception as e:
            errors.append(f"ERROR {full_path}: {e}")
            skipped += 1
    
    print(f"Layer 2 nodes: {len([n for n in nodes if n.get('layer')==2])}")
    print(f"Fixed: {fixed}, Skipped: {skipped}, Errors: {len(errors)}")
    if errors[:5]:
        for e in errors[:5]:
            print(f"  {e}")
    
    # 保存补丁版本
    save_graph(g, OUTPUT)
    print(f"Saved: {OUTPUT}")
    
    # 统计修复后内容长度
    layer2_nodes = [n for n in nodes if n.get('layer') == 2]
    with_content = sum(1 for n in layer2_nodes if len(n.get('markdown','')) > 200)
    print(f"Layer 2 nodes with content >200 chars: {with_content}/{len(layer2_nodes)}")

if __name__ == "__main__":
    main()