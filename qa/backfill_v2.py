#!/usr/bin/env python3
import re, json, os, urllib.request, time
from pathlib import Path

api_key = os.environ.get('MINIMAX_API_KEY', '')
WIKI_ROOT = Path('/mnt/data/km/llm-wiki/wiki/compiled/concepts')

clean = []
for f in WIKI_ROOT.glob('*.md'):
    content = f.read_text()
    fm = re.search(r'^description:\s*(.*)$', content, re.MULTILINE)
    if not fm or not fm.group(1).strip():
        clean.append(f.name)

print(f'Missing: {len(clean)}')

done = 0
for name in clean[:30]:
    fp = WIKI_ROOT / name
    concept = name.replace('.md', '')
    
    content = fp.read_text()
    body = re.sub(r'^---\n[\\s\\S]*?\n---\n?', '', content).strip()
    body = re.sub(r'^#+\s*[\w\u4e00-\u9fff].*\n?', '', body).strip()
    context = body[:600]
    
    prompts = [
        f'\u4e3a\u300c{concept}\u300d\u751f\u621050-150\u5b57\u4e2d\u6587\u63cf\u8ff0\uff08\u5b9a\u4e49+\u7528\u9014\uff09\uff0c\u4e0d\u7528\u6807\u9898\uff0c\u76f4\u63a5\u5199\u6bb5\u843d\uff1a{context}',
        f'What is {concept}? Answer in 1-2 sentences Chinese: {context[:400]}',
    ]
    
    desc = None
    for p in prompts:
        try:
            body_req = {'model': 'MiniMax-M2.7', 'max_tokens': 150, 'messages': [{'role': 'user', 'content': p}]}
            req = urllib.request.Request(
                'https://api.minimaxi.com/anthropic/v1/messages',
                data=json.dumps(body_req).encode('utf-8'),
                headers={'Authorization': f'Bearer {api_key}', 'x-api-key': api_key, 'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                r = json.loads(resp.read().decode('utf-8'))
            text = r.get('content', [{}])[0].get('text', '').strip()
            text = re.sub(r'^#+\s*', '', text)
            text = re.sub(r'\n+', ' ', text).strip('"\'')
            if text and len(text) >= 10:
                desc = text
                break
        except Exception as e:
            continue
    
    if desc:
        c = fp.read_text()
        c = re.sub(r'^description:.*\n', '', c, flags=re.MULTILINE)
        if re.match(r'^---', c):
            m = re.search(r'^---\n', c)
            c = c[:m.end()] + f'description: "{desc}"\n' + c[m.end():]
        fp.write_text(c)
        print(f'OK: {concept} -> {desc[:60]}...')
        done += 1
    else:
        print(f'FAIL: {concept}')
    
    time.sleep(0.5)

print(f'Done: {done}/30')