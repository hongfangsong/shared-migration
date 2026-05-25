#!/usr/bin/env python3
"""
Layer 2 concept 节点 LLM Backfill 脚本 v5（优先级链路版）

对于每个需要补全的 concept，按优先级尝试：

1. Graph INFERRED edge titles（已有 LLM 生成的概念描述，最优先）
2. 原始文件名关键词搜索
3. 内容关键词搜索（展开多关键词）
4. LLM 生成（基于原始文件内容）

description 格式：
- 不以 # 开头（去掉 markdown 标题残留）
- 中文，50-150 字，连贯段落

用法：
  python3 backfill_concept_description.py --dry-run
  python3 backfill_concept_description.py --execute
  python3 backfill_concept_description.py --execute --limit 20
"""
import json, re, sys, os, shutil, glob
from pathlib import Path
from datetime import datetime

GRAPH_MINI = "/mnt/data/km/llm-wiki/graph/graph_mini.json"
WIKI_ROOT = Path("/mnt/data/km/llm-wiki/wiki")
RAW_ROOT = Path("/mnt/data/km/knowledge/raw")
BACKUP_DIR = Path("/mnt/data/km/llm-wiki/graph/backups")
PATCHED = "/mnt/data/sub_agents/shared/qa/graph_mini_patched.json"

DRY_RUN = "--dry-run" in sys.argv
EXECUTE = "--execute" in sys.argv
LIMIT = 20
for arg in sys.argv:
    if arg.startswith("--limit="):
        LIMIT = int(arg.split("=")[1])

# ============ 工具函数 ============

def strip_frontmatter(content):
    """去掉 frontmatter 和 markdown 标题残留"""
    content = re.sub(r'^---\n[\\s\\S]*?\n---\n?', '', content).strip()
    # 去掉开头残留的 # 标题行
    content = re.sub(r'^#+\s*[\w\u4e00-\u9fff].*\n?', '', content).strip()
    return content

def parse_frontmatter(content):
    match = re.match(r'---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}, content
    yaml_str = match.group(1)
    body = content[match.end():].strip()
    yaml_dict = {}
    for line in yaml_str.split('\n'):
        m = re.match(r'^(\w+):\s*(.*)$', line.strip())
        if m:
            yaml_dict[m.group(1)] = m.group(2).strip().strip('"\'')
    return yaml_dict, body

# ============ 策略 1: Graph INFERRED edge titles ============

def get_inferred_descriptions(graph, concept_id):
    """从 graph edges 收集 INFERRED edge titles 作为描述"""
    titles = []
    for e in graph.get('edges', []):
        if e.get('to') == concept_id and e.get('type') == 'INFERRED':
            title = e.get('title', '').strip()
            if title and len(title) > 10:
                titles.append(title)
    return titles

# ============ 策略 2+3: 原始文件搜索 ============

def search_raw_files(concept_name, vault=None, top_k=5):
    """搜索最相关的 raw 文件，返回 [(file_path, score, preview)]"""
    candidates = []

    # 生成关键词变体
    keywords = set()
    keywords.add(concept_name)
    keywords.add(concept_name.lower())
    keywords.add(concept_name.replace('-', ' '))
    keywords.add(concept_name.replace('-', '_'))
    keywords.add(concept_name.replace('_', ' '))
    # 拆分复合词
    for sep in ['-', '_', ' ', '.']:
        parts = concept_name.split(sep)
        if len(parts) >= 2:
            for p in parts:
                if len(p) >= 2:
                    keywords.add(p)
                    keywords.add(p.lower())

    search_roots = [RAW_ROOT]
    if vault:
        vault_map = {
            'tech': RAW_ROOT / 'Tech',
            'compiled': RAW_ROOT / 'compiled',
            'lifestyle': RAW_ROOT / 'lifestyle',
            'others': RAW_ROOT / 'others',
        }
        if vault in vault_map and vault_map[vault].exists():
            search_roots = [vault_map[vault]]

    for search_root in search_roots:
        if not search_root.exists():
            continue
        for f in search_root.glob("**/*.md"):
            try:
                fname_lower = f.name.lower()
                # Filename score
                fn_score = 0
                for kw in keywords:
                    if kw.lower() in fname_lower:
                        fn_score += 1
                if fn_score == 0:
                    continue

                # Read content preview (first 50 lines)
                lines = f.read_text(encoding='utf-8', errors='ignore').split('\n')[:50]
                content_lower = ' '.join(lines).lower()
                ct_score = sum(1 for kw in keywords if kw.lower() in content_lower)

                total = fn_score * 10 + ct_score
                if total > 0:
                    body = strip_frontmatter('\n'.join(lines))
                    candidates.append({
                        'file': f,
                        'filename_score': fn_score,
                        'total_score': total,
                        'preview': body[:500]
                    })
            except Exception:
                continue

    # Dedupe + sort
    candidates.sort(key=lambda x: -x['total_score'])
    seen = set()
    unique = []
    for c in candidates:
        try:
            key = c['file'].read_text(encoding='utf-8', errors='ignore')[:100]
            if key not in seen:
                seen.add(key)
                unique.append(c)
        except:
            pass
    return unique[:top_k]

# ============ 策略 4: LLM 生成 ============

def generate_description_via_llm(concept_name, context, api_key=None):
    import requests
    if not api_key:
        api_key = os.environ.get("MINIMAX_API_KEY", "")
        if not api_key:
            return None

    # 清洗 context
    context = strip_frontmatter(context)
    if len(context) < 50:
        return None

    prompt = f"""你是一个知识库管理员。基于以下关于「{concept_name}」的原始文档内容，写一段50-150字的概念描述。

要求：中文，第三人称，客观描述，直接说明概念是什么、解决什么问题，不要列要点，要连贯段落，不超过150字。不要以#或*开头，直接写正文。

---原始内容---
{context[:3000]}
---"""

    try:
        resp = requests.post(
            "https://api.minimaxi.com/anthropic/v1/messages",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "x-api-key": api_key
            },
            json={
                "model": "MiniMax-M2.7",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 600,
                "temperature": 0.3
            },
            timeout=90
        )
        result = resp.json()
        content_list = result.get("content", [])
        for item in content_list:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text", "").strip()
                # 清洗：以#开头或*开头的行去掉
                text = re.sub(r'^[#*].*$', '', text, flags=re.MULTILINE).strip()
                # 取前150字
                if text and len(text) >= 20:
                    return text[:200]
        # Fallback
        for item in content_list:
            if isinstance(item, dict) and item.get("type") != "thinking":
                text = item.get("text", "").strip()
                if text:
                    text = re.sub(r'^[#*].*$', '', text, flags=re.MULTILINE).strip()
                    return text[:200]
        return None
    except Exception as e:
        print(f"    [LLM ERROR] {e}")
        return None

def compose_from_edge_titles(titles):
    """把多个 edge titles 组合成一个连贯段落"""
    chinese_titles = [t for t in titles if len(t) >= 20 and re.search(r'[\u4e00-\u9fff]', t)]
    if chinese_titles:
        chinese_titles.sort(key=len, reverse=True)
        combined = '。'.join(chinese_titles[:3])
        if len(combined) > 150:
            combined = combined[:150] + '…'
        return combined
    en_titles = [t for t in titles if len(t) >= 20]
    if en_titles:
        en_titles.sort(key=len, reverse=True)
        return en_titles[0][:150]
    return None

def generate_name_based_description(concept_name, vault, api_key):
    """对无原始文档的概念，直接基于概念名生成描述"""
    import requests
    if not api_key:
        api_key = os.environ.get("MINIMAX_API_KEY", "")
        if not api_key:
            return None

    # 尝试最多3种不同 prompt 风格
    prompts = [
        # 风格1：极简直接
        f"{concept_name}是什么？用中文回答，80字以内。",
        # 风格2：解释要求
        f"Give a one-sentence Chinese definition of {concept_name} (max 80 Chinese characters).",
        # 风格3：换一种英文问法
        f"What is {concept_name}? Answer in one short Chinese sentence.",
    ]

    for attempt, prompt in enumerate(prompts, 1):
        try:
            resp = requests.post(
                "https://api.minimaxi.com/anthropic/v1/messages",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "x-api-key": api_key
                },
                json={
                    "model": "MiniMax-M2.7",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 250,
                    "temperature": 0.3
                },
                timeout=60
            )
            result = resp.json()
            content_list = result.get("content", [])

            # Collect all non-empty text from all blocks
            all_text = []
            for item in content_list:
                if isinstance(item, dict) and item.get("type") == "text":
                    t = item.get("text", "").strip()
                    if t:
                        all_text.append(t)

            if not all_text:
                continue  # try next prompt style

            combined = ' '.join(all_text)

            # Skip full instruction-echo
            if re.match(r'^(The user asks|用户|你).{0,50}(?:：|:)', combined):
                continue  # try next prompt

            # Extract Chinese content
            # Look for first Chinese sentence
            match = re.search(r'[\u4e00-\u9fff][^\n。！？]{5,}', combined)
            if match:
                text = match.group(0)
                # Clean trailing incomplete sentences
                text = re.sub(r'^(用户|你).{0,20}', '', text)
                text = text.strip()
                if len(text) >= 15:
                    return text[:150]

            # If no Chinese found but we got some English, use it
            if len(combined) >= 20:
                return combined[:150]

        except Exception as e:
            print(f"    [NameLLM ERROR attempt {attempt}] {e}")
            continue

    return None

def update_concept_file(concept_path, description):
    content = concept_path.read_text(encoding='utf-8')
    if re.search(r'^description:', content, re.MULTILINE):
        content = re.sub(r'^description:.*\n', f'description: "{description}"\n', content, flags=re.MULTILINE)
    else:
        match = re.match(r'(---\n.*?\n)(---)', content, re.DOTALL)
        if match:
            content = content.replace(
                match.group(1) + match.group(2),
                match.group(1) + f'description: "{description}"\n' + match.group(2)
            )
    concept_path.write_text(content, encoding='utf-8')

def update_graph_node(node_id, description, graph):
    for node in graph['nodes']:
        if node['id'] == node_id:
            node['description'] = description
            break

def process_concept(node, api_key, graph):
    node_id = node['id']
    path = node.get('path', '')

    if not path or not path.startswith('wiki/'):
        return False, "Invalid path"

    rel_path = path.replace('wiki/', '', 1)
    parts = rel_path.split('/')
    if len(parts) < 3:
        return False, "Path too short"
    vault = parts[0]
    filename = Path(parts[-1]).stem

    concept_path = WIKI_ROOT / rel_path
    if not concept_path.exists() or concept_path.is_dir():
        return False, "File not found"

    fm, _ = parse_frontmatter(concept_path.read_text(encoding='utf-8'))
    concept_name = fm.get('concept', filename)

    # === 策略 1: INFERRED edge titles ===
    inferred_titles = get_inferred_descriptions(graph, node_id)
    if inferred_titles:
        desc = compose_from_edge_titles(inferred_titles)
        if desc:
            update_concept_file(concept_path, desc)
            return True, f"[edge] {desc[:60]}..."

    # === 策略 2+3: raw 文件搜索 ===
    results = search_raw_files(concept_name, vault=vault, top_k=3)
    if not results:
        results = search_raw_files(concept_name, vault=None, top_k=3)

    if results:
        best = results[0]
        content = best['file'].read_text(encoding='utf-8', errors='ignore')
        clean_content = strip_frontmatter(content)
        if len(clean_content) >= 50:
            # === 策略 4: LLM 生成 ===
            desc = generate_description_via_llm(concept_name, clean_content, api_key)
            if desc:
                update_concept_file(concept_path, desc)
                return True, f"[llm] {desc[:60]}..."

    # === 策略 5: 纯概念名 LLM 生成（兜底）===
    desc = generate_name_based_description(concept_name, vault, api_key)
    if desc:
        update_concept_file(concept_path, desc)
        return True, f"[name] {desc[:60]}..."

    return False, "No relevant sources found"

def main():
    if os.path.exists(PATCHED):
        graph = json.load(open(PATCHED))
        print(f"Loaded patched graph: {len(graph['nodes'])} nodes")
    else:
        graph = json.load(open(GRAPH_MINI))
        print(f"Loaded original graph: {len(graph['nodes'])} nodes")

    layer2_nodes = [n for n in graph['nodes'] if n.get('layer') == 2]
    print(f"Layer 2 nodes: {len(layer2_nodes)}")

    needs_work = []
    for n in layer2_nodes:
        path = n.get('path', '')
        if not path or not path.startswith('wiki/'):
            continue
        rel_path = path.replace('wiki/', '', 1)
        cp = WIKI_ROOT / rel_path
        if not cp.exists() or cp.is_dir():
            continue
        fm, _ = parse_frontmatter(cp.read_text(encoding='utf-8'))
        if not fm.get('description'):
            needs_work.append(n)

    print(f"Needs work: {len(needs_work)}")

    if DRY_RUN:
        print(f"\n=== DRY RUN: first {min(10, len(needs_work))} ===")
        for n in needs_work[:10]:
            titles = get_inferred_descriptions(graph, n['id'])
            results = search_raw_files(Path(n['path'].replace('wiki/','',1)).stem if n.get('path') else '', 
                                       vault=n['id'].split('/')[0] if '/' in n['id'] else None, top_k=2)
            print(f"  {n['id']}")
            print(f"    edge titles: {len(titles)}")
            print(f"    raw files: {len(results)}")
        return

    if not EXECUTE:
        print("\nUse --dry-run or --execute [--limit N]")
        return

    api_key = os.environ.get("MINIMAX_API_KEY", "")
    if not api_key:
        print("ERROR: MINIMAX_API_KEY not set")
        return

    BACKUP_DIR.mkdir(exist_ok=True)
    bp = BACKUP_DIR / f"graph_bak_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    shutil.copy(GRAPH_MINI, bp)
    print(f"Backup: {bp}")

    done = 0
    failed = 0
    errors = []

    total = min(LIMIT, len(needs_work))
    print(f"\nProcessing {total}...")

    for i, node in enumerate(needs_work[:total]):
        node_id = node['id']
        print(f"[{i+1}/{total}] {node_id}...", end=" ", flush=True)
        ok, result = process_concept(node, api_key, graph)
        if ok:
            print(f"✅ {result}")
            done += 1
            update_graph_node(node_id, result, graph)
        else:
            print(f"⏳ {result}")
            failed += 1
            errors.append(f"{node_id}: {result}")

    if done > 0:
        with open(PATCHED, 'w') as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)
        print(f"\nSaved to {PATCHED}")

    print(f"\nDone: {done} | Failed: {failed}")
    if errors:
        print(f"First errors: {errors[:5]}")

if __name__ == "__main__":
    main()