<!-- README.zh.md (中文) -->
> [English version](README.md) · 中文
# EndNote‑Toolkit

将 **文章中交叉引用的文本** → **endnote** 的格式。

------

## 功能亮点

| 脚本                      | 作用                                                         | 关键字段                       | 数据源       |
| ------------------------- | ------------------------------------------------------------ | ------------------------------ | ------------ |
| `quick_refs2ris_v2.py`    | 把word中reference list的refs.txt文档 →refs.ris的 **RIS文档** | AU / TI / JO / PY / DOI / ISBN | 本地正则解析 |
| `enrich_with_crossref.py` | 补全refs.ris的参考文献中的缺漏信息，得到refs_full.ris        | DOI · 卷期页 · 出版社          | 在线 API     |
| `renumber_by_title.py`    | 按word中reference list对 `<rec-number>` 排序                 | rec‑number                     | 本地算法匹配 |

------

## 安装与依赖

```bash
# 克隆仓库
$ git clone https://github.com/<you>/CQP-EndNote-Toolkit.git
$ cd CQP-EndNote-Toolkit

# 安装 Python 依赖
$ pip install -r requirements.txt  # requests, rapidfuzz, rich, lxml ...
```

> **环境**：Python ≥ 3.8；能联网访问 Crossref/OpenLibrary。

------

## 一键流水线

```bash
python scripts/quick_refs2ris_v2.py  refs.txt  refs.ris
python scripts/enrich_with_crossref.py  refs.ris  refs_full.ris
python scripts/renumber_by_title.py  CQP.xml  refs.txt  CQP_renum.xml
```

完成后将 `CQP_renum.xml` 导入 EndNote / Cite While You Write，即可与 **黄金编号** 对齐。

------

## 目录结构

```
EndNote-Toolkit/
│─ quick_refs2ris_v2.py
│─ enrich_with_crossref.py
│─ renumber_by_title.py
└─ README.md
```

------

| 问题                   | 解决方案                                                     |
| ---------------------- | ------------------------------------------------------------ |
| Crossref 429 限速      | 增大 `--sleep` 或启动 VPN；也可在 `scripts/enrich_with_crossref.py` 中调整 `MAX_RETRY`。 |
| XML 中 rec-number 冲突 | 确认黄金列表无重复编号，或先在 EndNote 批量清空 rec-number 再跑脚本。 |
| 非英文期刊匹配失败     | 在黄金列表和 XML 里统一翻译或手动拉平拼写差异。              |

------

## Word 

1. 在 Word 中按 `Ctrl + H` 

| 输入框       | 填入内容（半角英文）                |
| ------------ | ----------------------------------- |
| **查找内容** | `\[([0-9]{1,4}),[ ]*([0-9]{1,4})\]` |
| **替换为**   | `[\1] [\2]`                         |

执行 **全部替换(Replace All)** 后示例：

```text
[100, 101]   →   [100] [101]
```

------

| 输入框       | 填入内容           |
| ------------ | ------------------ |
| **查找内容** | `\[([0-9]{1,4})\]` |
| **替换为**   | `{#\1}`            |

再次 **全部替换**，则：

```text
[57]  →  {#57}
[201] → {#201}
```

------

2.在 Word 功能区点击 **EndNote ► Update Citations and Bibliography**。
