import json
import time
import requests

# 飞书 Bitable 工单表
BITABLE_APP_TOKEN = "VLu5b9WcAa4bZ1s9D4JcpBt0nTh"
BITABLE_TABLE_ID = "tbl5IKimRE1TPhQQ"

# Expert 工单群
EXPERT_GROUP_ID = "oc_6d74d5cc93107cd2740eaadc18d781f0"

# Bot appId/secret
BOT_APP_ID = "cli_a9699ac3dc399bc0"
BOT_SECRET = "NrkJGkMSd3ncnUj5bqv7hZqMf2n7pKLr"  # Service-Bot

def gettenantaccesstoken():
    resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        headers={"Content-Type": "application/json"},
        json={"app_id": BOT_APP_ID, "app_secret": BOT_SECRET}
    )
    return resp.json().get("tenant_access_token", "")

def bitable_create_record(token, payload):
    resp = requests.post(
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records",
        headers={"Authorization": f"Bearer {token}"},
        json={"fields": payload}
    )
    return resp.json()

def feishu_send_group(group_id, msg):
    token = gettenantaccesstoken()
    resp = requests.post(
        "https://open.feishu.cn/open-apis/im/v1/messages",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"receive_id": group_id, "msg_type": "text", "content": json.dumps({"text": msg})}
    )
    return resp.json()

def escalate_to_expert(question, candidates, asker_id):
    """
    1. 写入 Bitable 工单
    2. 通知 Expert 工单群
    """
    token = gettenantaccesstoken()
    
    # Bitable record
    record_payload = {
        "fields": {
            "标题": f"Q&A 未命中：{question[:50]}",
            "状态": {"text": "pending"},
            "描述": f"原始问题：{question}\n\nTop-3 候选：{json.dumps(candidates, ensure_ascii=False)}",
            "标签": {"text": "auto-escalation"}
        }
    }
    bitable_result = bitable_create_record(token, record_payload)
    
    # Notify expert group
    msg = f"🤖 有新的 Q&A 升级工单需要处理\n\n问题：{question}\n提问者：{asker_id}\n候选：{candidates[0]['node_id'] if candidates else 'N/A'}"
    notify_result = feishu_send_group(EXPERT_GROUP_ID, msg)
    
    return {
        "bitable": bitable_result,
        "notify": notify_result,
        "timestamp": int(time.time())
    }