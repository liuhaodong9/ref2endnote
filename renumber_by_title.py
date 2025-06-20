#!/usr/bin/env python3
"""
renumber_by_title.py ★ v3.0
────────────────────────────────────────────────────────
1. 黄金列表 → <rec-number>，三层匹配：标题→期刊+年份→年份
2. 改号后按 rec-number 升序重排 <record>
3. 写出 XML 并打印验证表
用法：
    python renumber_by_title.py  CQP.xml  golden_list.txt  CQP_renum.xml
"""

import re, sys, unicodedata, difflib, xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

TITLE_THR = 0.75      # 标题相似度阈值

# ──────────────────── 工具 ────────────────────
def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^0-9a-z]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()

def extract_year(text: str) -> str:
    m = re.search(r"(19|20)\d{2}", text)
    return m.group(0) if m else ""

# ─────────────── 读取黄金列表 ───────────────
def load_golden(p: Path):
    """
    返回 {编号: {'title':norm,'journal':norm,'year':yyyy}}
    """
    mp = {}
    for ln in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*\[?(\d{1,4})\]?\s*(.+)", ln)
        if not m:             # 空行 / 异常行
            continue
        num, rest = int(m.group(1)), m.group(2)
        segs = [s.strip() for s in rest.split(".") if s.strip()]
        title   = segs[1] if len(segs) > 1 else segs[0]
        journal = segs[2] if len(segs) > 2 else ""
        year    = extract_year(rest)
        mp[num] = {"title": norm(title),
                   "journal": norm(journal),
                   "year": year}
    return mp

# ─────────────── 主逻辑 ───────────────
def renumber(src: Path, gold: Path, dst: Path):
    tree = ET.parse(src); root = tree.getroot()

    # 为多策略匹配建立索引
    rec_info = {}                        # id(rec) → dict
    title_idx = {}                       # norm_title → rec
    jy_idx = defaultdict(list)           # (journal, year) → [rec,...]
    y_idx  = defaultdict(list)           # year → [rec,...]

    for rec in root.findall(".//record"):
        title_raw = rec.findtext(".//titles/title/style", "")
        jour_raw  = (rec.findtext(".//periodical/full-title", "")
                     or rec.findtext(".//publisher/style", ""))
        year_raw  = rec.findtext(".//dates/year", "") or extract_year(title_raw)

        nt, nj = norm(title_raw), norm(jour_raw)
        rec_info[id(rec)] = {"rec": rec, "title": nt, "journal": nj, "year": year_raw}

        if nt:            title_idx[nt] = rec
        jy_idx[(nj, year_raw)].append(rec)
        y_idx[year_raw].append(rec)

    golden = load_golden(gold)
    used = set()          # 记录已经分配的 rec id

    # ── ① 标题匹配 ──
    for num, g in golden.items():
        best, bscore = None, 0
        for xt, rec in title_idx.items():
            if id(rec) in used:
                continue
            s = difflib.SequenceMatcher(None, g["title"], xt).ratio()
            if s > bscore:
                best, bscore = rec, s
        if best and bscore >= TITLE_THR:
            best.find("rec-number").text = str(num)
            used.add(id(best))

    # ── ② 期刊 + 年份 ──
    for num, g in golden.items():
        if any(r.findtext("rec-number") == str(num) for r in root.findall(".//record")):
            continue
        for rec in jy_idx.get((g["journal"], g["year"]), []):
            if id(rec) not in used:
                rec.find("rec-number").text = str(num)
                used.add(id(rec))
                break

    # ── ③ 仅年份 ──
    for num, g in golden.items():
        if any(r.findtext("rec-number") == str(num) for r in root.findall(".//record")):
            continue
        for rec in y_idx.get(g["year"], []):
            if id(rec) not in used:
                rec.find("rec-number").text = str(num)
                used.add(id(rec))
                break

    # ── 重排记录 ──
    recs = root.findall(".//record")
    recs.sort(key=lambda r: int(r.findtext("rec-number", "999999")))
    root[:] = recs
    tree.write(dst, encoding="utf-8", xml_declaration=True)
    print(f"✅ 已写入 {dst}")

    # ── 快速验证 ──
    rn2title = {int(r.findtext("rec-number", "0")):
                r.findtext(".//titles/title/style", "")[:60]
                for r in recs}
    missing = [n for n in golden if n not in rn2title]
    print("\n黄金号 | XML号 | 标题（截 50 字）")
    print("-"*90)
    for n in sorted(golden):
        print(f"{n:>6} | {n if n in rn2title else 'NA':>5} | {rn2title.get(n,'（缺失）')}")
    if missing:
        print("\n⚠️ 未匹配编号:", missing)
    else:
        print("\n✔️ 全部黄金编号已就位")

# ─────────────── CLI ───────────────
if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("用法: python renumber_by_title.py  CQP.xml golden_list.txt  CQP_renum.xml")
    renumber(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
