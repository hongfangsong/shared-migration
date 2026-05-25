#!/usr/bin/env python3
"""
Backfill descriptions for tech/concepts files.
Handles MiniMax thinking-block responses by extracting Chinese text from thinking.
Usage: python3 backfill_tech_concepts.py --start=0 --limit=50
"""
import re, json, os, urllib.request, time, sys
from pathlib import Path

API_KEY = os.environ.get('MINIMAX_API_KEY', '') or 'sk-cp-CRgJEFtLtRjRysYIOlLKhf1Va79fSJPCWRq_rFyvWza74aleOSCZ3gGJsIWmYZrZpKOdY4ez1QNn3xsEjj_4ebxLk_7gX7Qiui7u5Iz6zMClyvWoz838I2Y'
URL = 'https://api.minimaxi.com/anthropic/v1/messages'
WIKI_ROOT = Path('/mnt/data/km/llm-wiki/wiki/tech/concepts')
OUTFILE = Path('/tmp/backfill_tech_progress.json')
LOGFILE = Path('/tmp/backfill_tech_log.txt')

START = 0
LIMIT = 50
for arg in sys.argv:
    if arg.startswith('--start='):
        START = int(arg.split('=')[1])
    if arg.startswith('--limit='):
        LIMIT = int(arg.split('=')[1])

def extract_chinese(text):
    """Extract longest Chinese paragraph from thinking or text block."""
    lines = text.split('\n')
    best = ''
    for line in lines:
        # Skip meta-commentary lines
        if re.match(r'^(The |Hmm |用户要求|让我|我来|Goal |Definition |So |I |We |This |Let\'s |That |Should |Maybe |No |Yes |It |Which |This is)', line):
            continue
        chinese = ''.join(re.findall(r'[\u4e00-\u9fff]', line))
        if len(chinese) >= 15 and len(line) >= 20:
            # Remove trailing count annotations
            clean = re.sub(r'[。\s]*[\u4e00-\u9fff]{1,3}\u5b57.*$', '', line)
            clean = clean.strip('"\'')
            if len(chinese) > len(best):
                best = clean
    return best

def generate_desc(concept, api_key):
    prompts = [
        f'\u4e3a\u300c{concept}\u300d\u5199\u4e00\u6bb5\u4e2d\u6587\u63cf\u8ff0\uff0c50-100\u5b57',
        f'\u4e3a\u300c{concept}\u300d\u751f\u6210\u4e00\u6bb5\u7b80\u8981\u63cf\u8ff0\uff0c\u4e2d\u6587\uff0c\u76f4\u63a5\u5199\u6bb5\u843d',
        f'What is {concept}? Answer in 2 sentences in Chinese: ',
    ]
    for p in prompts:
        try:
            body_req = {'model': 'MiniMax-M2.7', 'max_tokens': 250,
                       'messages': [{'role': 'user', 'content': p}]}
            req = urllib.request.Request(URL,
                data=json.dumps(body_req).encode('utf-8'),
                headers={'Authorization': f'Bearer {api_key}',
                        'x-api-key': api_key, 'Content-Type': 'application/json'},
                method='POST')
            with urllib.request.urlopen(req, timeout=20) as resp:
                r = json.loads(resp.read().decode('utf-8'))

            all_text = ''
            for item in r.get('content', []):
                t = item.get('type', '')
                if t == 'text':
                    txt = item.get('text', '')
                    # If text has substantial Chinese content, use it
                    chinese = ''.join(re.findall(r'[\u4e00-\u9fff]', txt))
                    if len(chinese) >= 15:
                        return txt, None
                    all_text += txt + '\n'
                elif t == 'thinking':
                    all_text += item.get('thinking', '') + '\n'

            desc = extract_chinese(all_text)
            if desc and len(desc) >= 15:
                return desc, None
        except Exception as e:
            continue
    return None, "all prompts failed"

# Load all concept files
all_files = sorted([f for f in WIKI_ROOT.glob('*.md')])
missing = [f for f in all_files
           if not re.search(r'^description:\s*\S', f.read_text(), re.MULTILINE)]

print(f"Total files: {len(all_files)}, Missing: {len(missing)}, Processing: {START} to {START+LIMIT}", flush=True)

batch = missing[START:START+LIMIT]
print(f"Batch: {len(batch)} files", flush=True)

done = 0
failed = 0
t0 = time.time()

for i, fp in enumerate(batch):
    concept = fp.name.replace('.md', '')
    desc, err = generate_desc(concept, API_KEY)

    if desc:
        c = fp.read_text()
        c = re.sub(r'^description:.*\n', '', c, flags=re.MULTILINE)
        m = re.search(r'^---\n', c)
        if m:
            c = c[:m.end()] + f'description: "{desc}"\n' + c[m.end():]
        fp.write_text(c)
        msg = f"[{START+i+1}] OK: {concept} -> {desc[:50]}..."
        print(msg, flush=True)
        with LOGFILE.open('a') as f:
            f.write(msg + '\n')
        done += 1
    else:
        msg = f"[{START+i+1}] FAIL: {concept}"
        print(msg, flush=True)
        with LOGFILE.open('a') as f:
            f.write(msg + '\n')
        failed += 1

    time.sleep(0.5)

elapsed = time.time() - t0
print(f"\nBatch done: {done}/{len(batch)} OK, {failed} failed, {elapsed:.1f}s", flush=True)
OUTFILE.write_text(json.dumps({'start': START, 'done': done, 'failed': failed, 'elapsed': elapsed}))