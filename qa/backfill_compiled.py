#!/usr/bin/env python3
"""
Backfill descriptions for compiled/concepts files missing descriptions.
Run: python3 backfill_compiled.py --execute --limit=52
"""
import json, re, sys, os, time
from pathlib import Path
from datetime import datetime

WIKI_ROOT = Path("/mnt/data/km/llm-wiki/wiki/compiled/concepts")
API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_URL = "https://api.minimaxi.com/anthropic/v1/messages"

LIMIT = 52
for arg in sys.argv:
    if arg.startswith("--limit="):
        LIMIT = int(arg.split("=")[1])

EXECUTE = "--execute" in sys.argv

def generate_description(concept_name, context, api_key):
    """Generate description via MiniMax LLM"""
    if not api_key:
        return None, "No API key"
    
    # Multi-prompt fallback strategy
    prompts = [
        # Prompt 1: Minimal Chinese
        f"为概念「{concept_name}」生成一段简短中文描述（50-150字），不要标题，不要列表。概念定义：{context[:500]}",
        # Prompt 2: English
        f"Generate a concise English description (50-150 chars) for concept: {concept_name}. Context: {context[:500]}",
        # Prompt 3: Different English style
        f"What is '{concept_name}'? Answer in 1-2 sentences in Chinese: {context[:500]}",
    ]
    
    for i, prompt in enumerate(prompts):
        try:
            import urllib.request
            import urllib.error
            
            body = {
                "model": "MiniMax-M2.7",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            req = urllib.request.Request(
                MINIMAX_URL,
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "x-api-key": api_key,
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            
            text = result.get("content", [{}])[0].get("text", "").strip()
            # Clean markdown
            text = re.sub(r'^#+\s*', '', text)
            text = re.sub(r'\n+', ' ', text)
            text = text.strip('"\'')
            
            if text and len(text) >= 10:
                return text, None
        except Exception as e:
            if i == len(prompts) - 1:
                return None, str(e)
            continue
    
    return None, "All prompts failed"

def update_file(fp, description):
    content = fp.read_text(encoding='utf-8')
    # Remove existing description line if any
    content = re.sub(r'^description:.*\n', '', content, flags=re.MULTILINE)
    # Add description after frontmatter
    if re.match(r'^---', content):
        # Find end of frontmatter
        match = re.search(r'^---\n', content)
        if match:
            pos = match.end()
            content = content[:pos] + f'description: "{description}"\n' + content[pos:]
    fp.write_text(content, encoding='utf-8')

# Load missing list
with open('/tmp/missing_concepts.json') as f:
    missing = json.load(f)

print(f"Total missing: {len(missing)}, processing up to {LIMIT}")

if not EXECUTE:
    print("Use --execute to actually write")
    sys.exit(0)

if not API_KEY:
    print("ERROR: MINIMAX_API_KEY not set")
    sys.exit(1)

done = 0
failed = 0
errors = []

for name in missing[:LIMIT]:
    fp = WIKI_ROOT / name
    if not fp.exists():
        print(f"  [SKIP] {name} - not found")
        continue
    
    concept_name = name.replace('.md', '')
    content = fp.read_text(encoding='utf-8')
    
    # Extract context from content (skip frontmatter and first heading)
    body = re.sub(r'^---\n[\\s\\S]*?\n---\n?', '', content).strip()
    body = re.sub(r'^#+\s*[\w\u4e00-\u9fff].*\n?', '', body).strip()
    context = body[:800] if len(body) > 800 else body
    
    print(f"Processing: {concept_name}... ", end='', flush=True)
    
    desc, err = generate_description(concept_name, context, API_KEY)
    
    if err:
        print(f"FAILED ({err})")
        failed += 1
        errors.append((concept_name, err))
    else:
        update_file(fp, desc)
        print(f"OK: {desc[:40]}...")
        done += 1
        time.sleep(0.5)  # Rate limit
    
    sys.stdout.flush()

print(f"\nDone: {done} | Failed: {failed}")
if errors:
    print("Errors:")
    for c, e in errors[:5]:
        print(f"  {c}: {e}")