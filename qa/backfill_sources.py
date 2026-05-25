#!/usr/bin/env python3
"""
Backfill descriptions for tech/sources and tech/entities files.
Extends backfill_tech_concepts.py to cover other wiki directories.
Usage: python3 backfill_sources.py --start=0 --limit=50
       python3 backfill_sources.py --dir=sources --start=0 --limit=50
       python3 backfill_sources.py --dir=entities --start=0 --limit=50
"""
import re, json, os, urllib.request, time, sys
from pathlib import Path

API_KEY = os.environ.get('MINIMAX_API_KEY', '') or 'sk-cp-CRgJEFtLtRjRysYIOlLKhf1Va79fSJPCWRq_rFyvWza74aleOSCZ3gGJsIWmYZrZpKOdY4ez1QNn3xsEjj_4ebxLk_7gX7Qiui7u5Iz6zMClyvWoz838I2Y'
URL = 'https://api.minimaxi.com/anthropic/v1/messages'
WIKI_ROOT = Path('/mnt/data/km/llm-wiki/wiki')
OUTFILE = Path('/tmp/backfill_progress.json')
LOGFILE = Path('/tmp/backfill_log.txt')

# Args
DIR = 'sources'
START = 0
LIMIT = 50

for arg in sys.argv:
    if arg.startswith('--dir='):
        DIR = arg.split('=')[1]
    if arg.startswith('--start='):
        START = int(arg.split('=')[1])
    if arg.startswith('--limit='):
        LIMIT = int(arg.split('=')[1])

WIKI_SUBDIR = Path(f'tech/{DIR}')
TARGET_DIR = WIKI_ROOT / WIKI_SUBDIR

def extract_chinese(text):
    """Extract longest Chinese paragraph from thinking or text block."""
    lines = text.split('\n')
    best = ''
    for line in lines:
        if re.match(r'^(The |Hmm |用户要求|让我|我来|Goal |Definition |So |I |We |This |Let\'s |That |Should |Maybe |No |Yes |It |Which |This is)', line):
            continue
        chinese = ''.join(re.findall(r'[\u4e00-\u9fff]', line))
        if len(chinese) >= 15 and len(line) >= 20:
            clean = re.sub(r'[。\s]*[\u4e00-\u9fff]{1,3}\u5b57.*$', '', line)
            clean = clean.strip('"\'')
            if len(chinese) > len(best):
                best = clean
    return best

def is_system_file(name):
    """Skip obvious system/temporary/placeholder files."""
    # Skip hidden files
    if name.startswith('.'):
        return True
    # Skip CLI argument flags
    if name.startswith('--'):
        return True
    # Skip temp/helper files
    if name.startswith('_') or name.endswith('_'):
        return True
    # Skip placeholder-like names
    if re.match(r'^[0-9a-f]{8,}\.md$', name):  # UUID-like
        return True
    # Skip common system artifacts
    skip_patterns = [
        '.ingest_queue', '.scan_status', '.openclaw',
        '.learnings', '.env', '.inferred_edges',
    ]
    for p in skip_patterns:
        if p in name:
            return True
    # Skip IP address files
    if re.match(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', name):
        return True
    # Skip date files (YYYY, YYYY-MM, YYYY-MM-DD, YYYY-MM-DD_*.md)
    if re.match(r'^[0-9]{4}(-[0-9]{2}){0,2}', name):
        return True
    # Skip version files (X.Y.Z*.md)
    if re.match(r'^[0-9]+\.[0-9]+\.[0-9]+', name):
        return True
    # Skip numeric-only names (port numbers, etc.)
    if re.match(r'^[0-9]+(_[0-9]+)*\.md$', name):
        return True
    return False

def has_real_description(content):
    """Check if file has a real (non-empty) description."""
    for line in content.split('\n'):
        if line.strip().startswith('description:'):
            desc = line.split('description:', 1)[1].strip()
            # Remove quotes
            desc = desc.strip('"').strip("'")
            if desc and desc != '""' and desc != "''":
                return True
            return False
    return False

def generate_desc(entity, api_key):
    """Generate description via MiniMax API."""
    prompts = [
        f'为「{entity}」写一段中文描述，50-100字',
        f'「{entity}」是什么？直接写一段中文描述',
        f'What is {entity}? Answer in Chinese, 2 sentences: ',
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

def update_description(fp, desc):
    """Add or update description in frontmatter."""
    c = fp.read_text()
    # Remove existing description line
    c = re.sub(r'^description:.*\n', '', c, flags=re.MULTILINE)
    m = re.search(r'^---\n', c)
    if m:
        c = c[:m.end()] + f'description: "{desc}"\n' + c[m.end():]
    fp.write_text(c)

# Load files
all_files = sorted([f for f in TARGET_DIR.glob('*.md') if not is_system_file(f.name)])
missing = [f for f in all_files if not has_real_description(f.read_text())]
total_raw = len(list(TARGET_DIR.glob('*.md')))

print(f"Target: tech/{DIR}/", flush=True)
print(f"Total files: {len(all_files)}, System skipped: {total_raw - len(all_files)}, Missing: {len(missing)}", flush=True)
print(f"Processing: {START} to {START+LIMIT} (batch size {LIMIT})", flush=True)

batch = missing[START:START+LIMIT]
print(f"Batch: {len(batch)} files", flush=True)

done = 0
failed = 0
t0 = time.time()

for i, fp in enumerate(batch):
    entity = fp.name.replace('.md', '')
    desc, err = generate_desc(entity, API_KEY)

    if desc:
        update_description(fp, desc)
        msg = f"[{START+i+1}] OK: {entity} -> {desc[:50]}..."
        print(msg, flush=True)
        with LOGFILE.open('a') as f:
            f.write(msg + '\n')
        done += 1
    else:
        msg = f"[{START+i+1}] FAIL: {entity} ({err})"
        print(msg, flush=True)
        with LOGFILE.open('a') as f:
            f.write(msg + '\n')
        failed += 1

    time.sleep(0.5)

elapsed = time.time() - t0
print(f"\nBatch done: {done}/{len(batch)} OK, {failed} failed, {elapsed:.1f}s", flush=True)
OUTFILE.write_text(json.dumps({
    'dir': DIR, 'start': START, 'done': done, 'failed': failed, 'elapsed': elapsed
}))