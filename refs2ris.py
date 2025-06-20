#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quick_refs2ris_v2.py  ——  把行格式参考文献批量转成改进版 RIS
调用: python quick_refs2ris_v2.py refs.txt coke_refs.ris
"""
import re, sys, pathlib

re_year  = re.compile(r'\b(19|20)\d{2}\b')
re_doi   = re.compile(r'(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)')
re_isbn  = re.compile(r'ISBN[\s:]*((97[89][- ]?)?\d{1,5}[- ]?\d{1,7}[- ]?\d{1,7}[- ]?[\dxX])')
re_voliss= re.compile(r';\s*(\d+)\s*\(\s*([\w\-]+)\s*\)\s*:')
re_pages = re.compile(r':\s*([0-9]+)\s*[-–]\s*([0-9]+)')
re_city  = re.compile(r'\b([A-Z][a-z]+(?: [A-Z][a-z]+)*)[:;,]?\s*$')

def guess_type(src, parsed):
    """根据关键字+结构猜 Reference Type"""
    if 'Proceedings' in src or 'Conference' in src:
        return 'CONF'
    if 'Report' in src or 'Standard' in src or 'ISO' in src:
        return 'RPRT'
    if 'Press' in src or 'Publisher' in src or parsed.get('ISBN'):
        return 'BOOK'
    if re.search(r'\d\(\d', src):           # 15(2)
        return 'JOUR'
    return 'GEN'

def parse_line(line: str):
    orig = line.strip()
    line  = re.sub(r'^\[\d+\]\s*', '', orig)      # 去掉 [1] 编号
    parts = [p.strip() for p in re.split(r'\.\s+', line, maxsplit=3)]
    authors_raw = parts[0]
    title       = parts[1] if len(parts) > 1 else ''
    src_rest    = parts[2] if len(parts) > 2 else ''
    rest        = parts[3] if len(parts) > 3 else ''

    # 作者
    authors = [a.strip() for a in re.split(r'[;,]', authors_raw) if a.strip() and a.lower()!='et al']

    # DOI / ISBN
    doi  = re_doi.search(orig)
    isbn = re_isbn.search(orig)

    # 卷、期、页
    m_v  = re_voliss.search(orig)
    m_pg = re_pages.search(orig)

    volume, issue, sp, ep = '', '', '', ''
    if m_v:
        volume, issue = m_v.groups()
    if m_pg:
        sp, ep = m_pg.groups()

    # 出版社 / 出版地（只对书粗抓一下）
    publisher, city = '', ''
    if 'Press' in orig or 'Publisher' in orig:
        segs = re.split(r';', orig)
        for s in segs:
            if 'Press' in s or 'Publisher' in s:
                publisher = s.strip()
            if city == '':
                m_city = re_city.search(s)
                if m_city:
                    city = m_city.group(1)

    year = re_year.search(orig).group(0) if re_year.search(orig) else ''

    parsed = dict(
        authors=authors, title=title, source=src_rest, year=year,
        volume=volume, issue=issue, sp=sp, ep=ep,
        doi=doi.group(1) if doi else '',
        ISBN=isbn.group(1) if isbn else '',
        publisher=publisher, city=city
    )
    parsed['type'] = guess_type(orig, parsed)
    parsed['raw']  = orig
    return parsed

def to_ris(d):
    out = [f"TY  - {d['type']}"]
    for au in d['authors']:
        out.append(f"AU  - {au}")
    if d['title']:  out.append(f"TI  - {d['title']}")
    if d['source']:
        if d['type'] == 'BOOK':
            out.append(f"T2  - {d['source']}")     # 书系列/版次放 T2
        else:
            out.append(f"JO  - {d['source']}")
    if d['year']:    out.append(f"PY  - {d['year']}")
    if d['volume']:  out.append(f"VL  - {d['volume']}")
    if d['issue']:   out.append(f"IS  - {d['issue']}")
    if d['sp']:      out.append(f"SP  - {d['sp']}")
    if d['ep']:      out.append(f"EP  - {d['ep']}")
    if d['doi']:     out.append(f"DO  - {d['doi']}")
    if d['ISBN']:    out.append(f"SN  - {d['ISBN']}")
    if d['publisher']: out.append(f"PB  - {d['publisher']}")
    if d['city']:      out.append(f"CY  - {d['city']}")
    out.append(f"N1  - {d['raw']}")
    out.append("ER  -")
    return "\n".join(out)

def main(in_path, out_path):
    recs = []
    for ln in pathlib.Path(in_path).read_text(encoding='utf-8').splitlines():
        if ln.strip():
            recs.append(to_ris(parse_line(ln)))
    pathlib.Path(out_path).write_text("\n\n".join(recs), encoding='utf-8')
    print(f"✔ 转换完成：{len(recs)} 条 → {out_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python refs2ris_v2.py refs.txt coke_refs.ris")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
