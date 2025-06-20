# CQP‑EndNote‑Toolkit

> 将 **文章中交叉引用的文本** → **EndNote** 的格式。

---

## 功能亮点

| 脚本                      | 作用                                                         | 关键字段                       | 数据源       |
| ------------------------- | ------------------------------------------------------------ | ------------------------------ | ------------ |
| `quick_refs2ris_v2.py`    | 把 Word 中 reference list 的 `refs.txt` → **RIS** 文档 `refs.ris` | AU / TI / JO / PY / DOI / ISBN | 本地正则解析 |
| `enrich_with_crossref.py` | 补全 `refs.ris` 的缺漏信息，生成 `refs_full.ris`             | DOI · 卷期页 · 出版社          | 在线 API     |
| `renumber_by_title.py`    | 按 Word 中 reference list 对 `<rec-number>` 重新排序         | rec‑number                     | 本地算法匹配 |

---

## 安装与依赖

```bash
# 克隆仓库
$ git clone https://github.com/<you>/CQP-EndNote-Toolkit.git
$ cd CQP-EndNote-Toolkit

# 安装 Python 依赖
$ pip install -r requirements.txt  # requests, rapidfuzz, rich, lxml ...
```

> **环境要求**：Python ≥ 3.8，且可联网访问 Crossref / OpenLibrary。

---

## 一键流水线

```bash
python scripts/quick_refs2ris_v2.py      refs.txt       refs.ris
python scripts/enrich_with_crossref.py   refs.ris       refs_full.ris
python scripts/renumber_by_title.py      CQP.xml        refs.txt    CQP_renum.xml
```

生成的 `CQP_renum.xml` 导入 EndNote / Cite While You Write 后，即可与 **黄金编号** 对齐。

---

## 目录结构

```
CQP-EndNote-Toolkit/
│─ quick_refs2ris_v2.py
│─ enrich_with_crossref.py
│─ renumber_by_title.py
└─ README.md
```

---

## 常见问题

| 问题                   | 解决方案                                                     |
| ---------------------- | ------------------------------------------------------------ |
| Crossref 429 限速      | 增大 `--sleep` 或启用 VPN；也可在 `scripts/enrich_with_crossref.py` 中调整 `MAX_RETRY`。 |
| XML 中 rec-number 冲突 | 确保黄金列表无重复编号，或先在 EndNote 批量清空 rec-number 再运行脚本。 |
| 非英文期刊匹配失败     | 在黄金列表和 XML 中统一译名，或手动校正拼写差异。            |

---

## Word 批量替换

1. 在 **Word → 替换 (Ctrl + H)** 中执行两次批量替换：

第一次：

| 输入框       | 内容（半角英文）                    |
| ------------ | ----------------------------------- |
| **查找内容** | `\[([0-9]{1,4}),[ ]*([0-9]{1,4})\]` |
| **替换为**   | `[\1] [\2]`                         |

示例：

```text
[100, 101]   →   [100] [101]
```

第二次：

| 输入框       | 内容               |
| ------------ | ------------------ |
| **查找内容** | `\[([0-9]{1,4})\]` |
| **替换为**   | `{#\1}`            |

示例：

```text
[57]  →  {#57}
[201] → {#201}
```

2. 在 Word 功能区点击 **EndNote ► Update Citations and Bibliography** 完成编号同步。

---

