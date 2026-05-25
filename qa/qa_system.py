#!/usr/bin/env python3
"""Q&A 问答系统主入口"""
import json
from question_classifier import classify_question
from answer_generator import generate_answer
from expert_escalation import escalate_to_expert
from qa_pair import create_qa_pair

def qa_answer(question, asker_id="unknown"):
    """
    主流程：
    1. Classify → 2. 判断置信度 → 3a. 命中→Answer Generator / 3b. 未命中→Expert Escalation
    """
    result = classify_question(question)
    top_score = result["top_score"]
    candidates = result["candidates"]
    
    if top_score >= 0.60 and candidates:
        # 命中介面
        top = candidates[0]
        answer = generate_answer(top["node_id"], question)
        return {
            "type": "hit",
            "answer": answer,
            "confidence": top_score
        }
    else:
        # 升级界面
        escalation = escalate_to_expert(question, candidates, asker_id)
        return {
            "type": "escalation",
            "candidates": candidates,
            "escalation_id": escalation.get("bitable", {}).get("data", {}).get("record", {}).get("record_id"),
            "confidence": top_score
        }

if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "cron任务不执行怎么办"
    r = qa_answer(q)
    print(json.dumps(r, ensure_ascii=False, indent=2))