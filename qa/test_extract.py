#!/usr/bin/env python3
import urllib.request, json, re, time
key = 'sk-cp-CRgJEFtLtRjRysYIOlLKhf1Va79fSJPCWRq_rFyvWza74aleOSCZ3gGJsIWmYZrZpKOdY4ez1QNn3xsEjj_4ebxLk_7gX7Qiui7u5Iz6zMClyvWoz838I2Y'

def extract_chinese(text):
    lines = text.split('\n')
    best = ''
    for line in lines:
        if re.match(r'^(The |Hmm |用户要求|让我|我来|Goal|Definition|So |I |We |This |Let\'s)', line):
            continue
        chinese = ''.join(re.findall(r'[\u4e00-\u9fff]', line))
        if len(chinese) >= 15 and len(line) >= 20:
            clean = re.sub(r'[。\s]*[\u4e00-\u9fff]{1,3}\u5b57.*$', '', line)
            clean = clean.strip('"\'')
            if len(chinese) > len(best):
                best = clean
    return best

tests = ['DeFi套利机器人', 'LLM_Wiki', 'TDD开发方法']
for concept in tests:
    p = f'\u4e3a\u300c{concept}\u300d\u5199\u4e00\u6bb5\u4e2d\u6587\u63cf\u8ff0\uff0c50-100\u5b57'
    body = {'model': 'MiniMax-M2.7', 'max_tokens': 250, 'messages': [{'role': 'user', 'content': p}]}
    req = urllib.request.Request(
        'https://api.minimaxi.com/anthropic/v1/messages',
        data=json.dumps(body).encode('utf-8'),
        headers={'Authorization': f'Bearer {key}', 'x-api-key': key, 'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            r = json.loads(resp.read().decode('utf-8'))
        all_text = ''
        for item in r['content']:
            all_text += (item.get('text', '') or item.get('thinking', '')) + '\n'
        desc = extract_chinese(all_text)
        print(f'{concept}: [{len(desc)}] {desc[:80]}')
    except Exception as e:
        print(f'{concept}: ERROR {e}')
    time.sleep(0.5)