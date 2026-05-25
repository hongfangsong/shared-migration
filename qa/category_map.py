#!/usr/bin/env python3
"""Category → Layer 映射：从 node_id 路径解析 category tree"""
import json
from pathlib import Path

GRAPH_MINI = "/mnt/data/km/llm-wiki/graph/graph_mini.json"


def parse_category(node_id: str, layer: int) -> dict:
    """
    从 node_id 路径解析 category tree
    
    Graph Layer → Q&A Category 映射：
    | Graph Layer | Q&A Category | 例 |
    |------------|-------------|---|
    | Layer 3 | 一级类目 | 系统优化、媒体热点、客服机器人 |
    | Layer 2 | 二级类目 | Cron调度、认证机制、vibecoding |
    | Layer 1 | 三级类目 | doc-bot、build_graph.py、MiniMax模型 |
    | Layer 0 | 答案来源 | 复盘报告、媒体热点报告 |
    
    返回：
    {
        "level1": "tech",           # vault 名
        "level2": "concepts",        # layer 名
        "level3": "cron-monitoring", # 具体 entity/concept 名
        "display": "tech / concepts / cron-monitoring"
    }
    """
    parts = node_id.split("/")
    
    if layer == 0:
        level1 = parts[0] if len(parts) > 0 else ""
        level2 = ""
        level3 = ""
    elif layer == 1:
        level1 = parts[0] if len(parts) > 0 else ""
        level2 = ""
        level3 = parts[-1] if len(parts) > 0 else ""
    elif layer == 2:
        level1 = parts[0] if len(parts) > 0 else ""
        level2 = parts[1] if len(parts) > 1 else ""
        level3 = parts[-1] if len(parts) > 0 else ""
    elif layer == 3:
        level1 = parts[0] if len(parts) > 0 else ""
        level2 = parts[1] if len(parts) > 1 else ""
        level3 = parts[-1] if len(parts) > 0 else ""
    else:
        level1 = level2 = level3 = ""
    
    display = " / ".join(filter(None, [level1, level2, level3]))
    
    return {
        "level1": level1,
        "level2": level2,
        "level3": level3,
        "display": display,
        "layer": layer,
        "vault": level1
    }


def get_suggested_category(node_id: str, layer: int) -> str:
    """
    返回用户友好的类目建议字符串
    用于未命中时展示"建议归类"
    """
    cat = parse_category(node_id, layer)
    
    # Layer 3 → 一级类目
    if layer == 3:
        return f"一级类目：{cat['level1']}（{cat['display']}）"
    # Layer 2 → 二级类目
    elif layer == 2:
        return f"二级类目：{cat['level2']}（归属：{cat['level1']}）"
    # Layer 1 → 三级类目
    elif layer == 1:
        return f"三级类目：{cat['level3']}（归属：{cat['level1']} / {cat['level2']}）"
    # Layer 0 → 答案来源
    else:
        return f"来源：{cat['level1']}"
    
    return cat['display']


def enrich_answer_with_category(node_id: str, layer: int) -> dict:
    """
    为答案补充类目信息的增强版返回
    """
    cat = parse_category(node_id, layer)
    return {
        "node_id": node_id,
        "layer": layer,
        "category": cat,
        "suggested_category": get_suggested_category(node_id, layer)
    }


# ---- 测试 ----
if __name__ == "__main__":
    test_cases = [
        ("tech/sources/code-execution.md", 0),
        ("tech/entities/doc-bot", 1),
        ("tech/concepts/cron-monitoring", 2),
        ("compiled/synthesis/系统优化总览", 3),
        ("lifestyle/entities/咖啡", 1),
    ]
    
    print("=== Category → Layer 映射测试 ===\n")
    for node_id, layer in test_cases:
        result = parse_category(node_id, layer)
        suggested = get_suggested_category(node_id, layer)
        print(f"Node: {node_id} (Layer {layer})")
        print(f"  Parsed: {result}")
        print(f"  Suggested: {suggested}")
        print()
    
    # 测试 enrich_answer_with_category
    print("=== enrich_answer_with_category ===")
    enriched = enrich_answer_with_category("tech/concepts/cron-monitoring", 2)
    print(json.dumps(enriched, ensure_ascii=False, indent=2))
