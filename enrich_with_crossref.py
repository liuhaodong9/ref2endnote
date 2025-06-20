#!/usr/bin/env python3
"""
enrich_with_crossref.py  ★ v1.2
================================
将**两种输入**批量补全为完整 RIS：
1. **已有 RIS**（含 TY ‑ AU ‑ TI 等标签）
2. **纯文本一行一条**（如 refs.txt）
   → 脚本会先把每行转成临时 RIS 记录，再调 Crossref/OpenLibrary 补 DOI/卷期页等。

★ 依赖
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Python ≥ 3.8  |  requests → `pip install requests`

★ 用法示例
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# A) 输入已是 RIS
$ python enrich_with_crossref.py coke_refs.ris coke_refs_full.ris

# B) 输入纯文本（refs.txt）
$ python enrich_with_crossref.py refs.txt coke_refs_full.ris

导入 EndNote：File ► Import ► File…
  • Import File = coke_refs_full.ris
  • Import Option = Reference Manager (RIS)
  • Duplicates = Discard Duplicates
"""

import re, sys, time, json
from pathlib import Path
from typing import List, Dict, Optional

try:
    import requests
except ImportError:
    sys.exit("❌ 需要安装 requests： pip install requests")

# ────────────────────────── Config ──────────────────────────
CROSSREF_BASE = "https://api.crossref.org/works"
OPENLIB_BASE  = "https://openlibrary.org/api/books"
HEADERS = {"User-Agent": "EndNoteBatchFix/1.2 (mailto:your_email@example.com)"}
MAX_RETRY = 3        # 网络重试
SLEEP     = 1.0      # 间隔秒

# ────────────────────────── RIS Helpers ──────────────────────────

def parse_ris(text: str) -> List[Dict[str, List[str]]]:
    """把 RIS 文本切分为记录列表，每条记录是 tag→list 的 dict"""
    recs, rec = [], {}
    for line in text.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^(?P<tag>[A-Z0-9]{2})  - (?P<val>.*)$", line)
        if not m:
            continue
        tag, val = m.group("tag"), m.group("val").strip()
        if tag == "TY" and rec:
            recs.append(rec); rec = {}
        rec.setdefault(tag, []).append(val)
        if tag == "ER":
            recs.append(rec); rec = {}
    if rec: recs.append(rec)
    return recs


def parse_plain(text: str) -> List[Dict[str, List[str]]]:
    """把一行一条的参考文献文本快速包装成简易 RIS 记录"""
    recs = []
    for line in text.splitlines():
        line = line.strip()
        if not line: continue
        # 去掉前缀编号 [n]
        line = re.sub(r"^\s*\[?\d+\]?\s*", "", line)
        recs.append({"TY": ["GEN"], "TI": [line], "N1": [line]})
    return recs


def ris_value(rec, tag):
    return rec.get(tag, [""])[0]

def set_value(rec, tag, val):
    if val: rec[tag] = [val]

def add_value(rec, tag, val):
    if val: rec.setdefault(tag, []).append(val)


def record_to_ris(rec):
    pref = ["TY","AU","TI","T2","JO","CY","PB","PY","VL","IS","SP","EP","DO","ISBN","N1"]
    lines = [f"{tag}  - {v}" for tag in pref for v in rec.get(tag, [])]
    for tag in sorted(rec):
        if tag in pref or tag=="ER": continue
        lines += [f"{tag}  - {v}" for v in rec[tag]]
    lines.append("ER  -")
    return "\n".join(lines)

# ────────────────────────── Requests ──────────────────────────

def safe_request(url, params):
    for _ in range(MAX_RETRY):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=20)
            if r.ok:
                return r.json()
        except requests.RequestException as e:
            msg = str(e)
        time.sleep(SLEEP)
    print(f"⚠️  请求失败: {url} | {msg}")
    return None


def cr_by_title(title):
    if not title: return None
    data = safe_request(CROSSREF_BASE, {"query.title": title, "rows": 1})
    items = data and data.get("message", {}).get("items")
    return items[0] if items else None


def cr_by_doi(doi):
    if not doi: return None
    data = safe_request(f"{CROSSREF_BASE}/{doi}", {})
    return data and data.get("message")


def ol_by_isbn(isbn):
    if not isbn: return None
    data = safe_request(OPENLIB_BASE, {"bibkeys": f"ISBN:{isbn}", "format": "json", "jscmd": "data"})
    return data and data.get(f"ISBN:{isbn}")

# ────────────────────────── Enrich ──────────────────────────

TITLE_TAGS = ["TI", "T1"]

def enrich(rec):
    title = next((ris_value(rec, t) for t in TITLE_TAGS if ris_value(rec, t)), "")
    doi   = ris_value(rec, "DO")
    rtype = ris_value(rec, "TY").upper() or "GEN"

    item = cr_by_doi(doi) if doi else cr_by_title(title)

    if item:
        # 作者
        rec.pop("AU", None)
        for a in item.get("author", []):
            add_value(rec, "AU", f"{a.get('family','')}, {a.get('given','')}")
        set_value(rec, "DO", item.get("DOI", doi))
        # 卷期页/期刊
        if rtype in {"JOUR", "GEN"}:
            set_value(rec, "JO", item.get("container-title", [ris_value(rec, "JO")])[0])
            set_value(rec, "VL", item.get("volume", ris_value(rec, "VL")))
            set_value(rec, "IS", item.get("issue",  ris_value(rec, "IS")))
            pg = item.get("page", "")
            if pg:
                sp, _, ep = pg.partition("-")
                set_value(rec, "SP", sp); set_value(rec, "EP", ep)
        # 年份
        year = item.get("issued", {}).get("date-parts", [[""]])[0][0]
        set_value(rec, "PY", str(year) if year else ris_value(rec, "PY"))
        set_value(rec, "T2", item.get("container-title", [ris_value(rec, "T2")])[0])

    if rtype in {"BOOK", "CHAP"}:
        isbn = ris_value(rec, "ISBN")
        if isbn:
            bk = ol_by_isbn(isbn)
            if bk:
                set_value(rec, "PB", bk.get("publishers", [{}])[0].get("name", ris_value(rec, "PB")))
                set_value(rec, "CY", bk.get("publish_places", [{}])[0].get("name", ris_value(rec, "CY")))
                pages = bk.get("number_of_pages")
                if pages:
                    set_value(rec, "SP", "1"); set_value(rec, "EP", str(pages))
    return rec

# ────────────────────────── CLI ──────────────────────────

def main():
    if len(sys.argv) != 3:
        sys.exit("用法: python enrich_with_crossref.py  input_file  output.ris")

    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    if not src.exists():
        sys.exit(f"❌ 输入文件不存在: {src}")

    raw = src.read_text(encoding="utf-8", errors="ignore")
    records = parse_ris(raw)
    if not records:  # 若非 RIS，则按纯文本处理
        records = parse_plain(raw)
        print("⚙️  检测到纯文本，已按一行一条转换为临时 RIS。")

    print(f"📚 共 {len(records)} 条记录，开始在线补全…\n")
    enriched = []
    for idx, rec in enumerate(records, 1):
        enriched.append(enrich(rec))
        print(f"[{idx}/{len(records)}] ✓ {ris_value(rec,'TI')[:60]}…")
        time.sleep(SLEEP)

    dst.write_text("\n\n".join(record_to_ris(r) for r in enriched), encoding="utf-8")
    print(f"\n✅ 完成！已写入 {dst} 。")

if __name__ == "__main__":
    main()
