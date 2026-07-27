#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 AI 日报 Markdown 转换为结构化 HTML（v2 排版要求）。
直接解析 Markdown 源码，按 🔹 标记拆分新闻条目，组装为结构化卡片。
- 每条新闻 -> <article class="news-card">（header / news-body / news-meta）
- 摘要标签 .label-badge；来源、置信度分别渲染为 .badge（蓝底/黄底）
- 维度补充说明、弹性原则说明等 📌 标记 -> .note-card
- 今日趋势点评整段 -> <section class="insight-section">，含三级子标题
- CSS 内嵌 <head>，860px 容器、卡片顶部蓝色渐变条、hover 上浮、暗黑模式、移动端自适应
"""
import re
import sys
import subprocess

MD_PATH = "2026-07-28-AI-Daily.md"
HTML_PATH = "2026-07-28-AI-Daily.html"
DOC_TITLE = "AI 行业每日热点深度简报 · 2026-07-28"


def ensure_markdown_lib():
    try:
        import markdown  # noqa: F401
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
                               "markdown"])


def md_inline(text):
    """用 markdown 库转换一段内联/简单文本为 HTML 片段。"""
    import markdown
    html = markdown.markdown(text, extensions=["extra"])
    # markdown 会把单行包成 <p>...</p>，去掉
    m = re.fullmatch(r"\s*<p>(.*)</p>\s*", html, flags=re.DOTALL)
    return m.group(1).strip() if m else html.strip()


def parse_news_items(md_text):
    """
    扫描 markdown 源码，提取所有以 '> **🔹' 起始的新闻条目。
    返回列表，每项 dict(title, summary_paragraphs, source, confidence,
                       line_start, line_end)。
    每个条目的内容由连续的 '>' 引用块组成（其间可有空行），
    直到下一个 '> **🔹' 或非引用内容。
    """
    lines = md_text.splitlines()
    items = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.strip().startswith("> **🔹"):
            item_start = i
            title_raw = line.strip()[2:].strip()  # 去掉 '> '
            title = re.sub(r"^\*\*🔹\s*\d*[.、]?\s*", "", title_raw)
            title = title.rstrip("*").strip()
            i += 1
            bq_lines = []   # 列表元素：(内容, 原始行号)
            while i < n:
                raw = lines[i]
                s = raw.strip()
                if s.startswith("> **🔹"):
                    break  # 下一条目开始
                if s == "":
                    bq_lines.append(("", i))
                    i += 1
                    continue
                if s.startswith(">"):
                    bq_lines.append((s[1:].strip(), i))
                    i += 1
                    continue
                # 非引用、非空行 → 条目结束
                break
            summary = []
            source = ""
            confidence = ""
            source_line_no = None
            # 定位摘要正文：📝 之后到 📰 之前
            start = 0
            for idx in range(len(bq_lines)):
                if bq_lines[idx][0].startswith("📝"):
                    start = idx + 1
                    break
            end = len(bq_lines)
            src_line_idx = None
            for idx in range(start, len(bq_lines)):
                if bq_lines[idx][0].startswith("📰"):
                    end = idx
                    # 来源行是 📰 之后第一个非空行
                    for j in range(idx + 1, len(bq_lines)):
                        if bq_lines[j][0] != "":
                            src_line_idx = j
                            source_line_no = bq_lines[j][1]
                            break
                    break
            # 摘要按空行分段
            cur = []
            for idx in range(start, end):
                bl = bq_lines[idx][0]
                if bl == "":
                    if cur:
                        summary.append(" ".join(cur))
                        cur = []
                else:
                    cur.append(bl)
            if cur:
                summary.append(" ".join(cur))
            # 来源行
            if src_line_idx is not None:
                raw_src = bq_lines[src_line_idx][0]
                src_m = re.search(r"`([^`]+)`", raw_src)
                if src_m:
                    source = src_m.group(1).strip()
                conf_m = re.search(r"置信度.*?[:：]\s*(.*)", raw_src)
                if conf_m:
                    confidence = re.sub(r"\*\*?", "", conf_m.group(1)).strip()
            item_end = (source_line_no + 1) if source_line_no is not None else i
            items.append({
                "title": title,
                "summary": summary,
                "source": source,
                "confidence": confidence,
                "line_start": item_start,
                "line_end": item_end,
            })
        else:
            i += 1
    return items


def build_card(item):
    title_html = md_inline(item["title"])
    summary_html = "".join(f"<p>{md_inline(p)}</p>" for p in item["summary"])
    label = '<span class="label-badge">📝 摘要</span>'
    footer = ""
    badges = []
    if item["source"]:
        badges.append(f'<span class="badge badge-source">📰 {item["source"]}</span>')
    if item["confidence"]:
        badges.append(f'<span class="badge badge-conf">置信度 {item["confidence"]}</span>')
    if badges:
        footer = '<footer class="news-meta">' + "".join(badges) + '</footer>'
    return (
        '<article class="news-card">'
        f'<header class="news-header">{title_html}</header>'
        f'<div class="news-body">{label}{summary_html}</div>'
        f'{footer}'
        '</article>'
    )


def build_body(md_text):
    items_all = parse_news_items(md_text)
    lines = md_text.splitlines()
    section = None
    item_idx = 0
    intl_cards = []
    cn_cards = []
    for line in lines:
        if line.startswith("## ") and "国际动态" in line:
            section = "intl"
        elif line.startswith("## ") and "国内动态" in line:
            section = "cn"
        elif line.startswith("## ") and "今日趋势点评" in line:
            section = None
        if line.strip().startswith("> **🔹"):
            if item_idx < len(items_all):
                card = build_card(items_all[item_idx])
                if section == "intl":
                    intl_cards.append(card)
                elif section == "cn":
                    cn_cards.append(card)
                item_idx += 1

    # 先计算新闻条目占用的行号集合，构建时跳过这些行
    skip_lines = set()
    for it in items_all:
        for ln in range(it["line_start"], it["line_end"]):
            skip_lines.add(ln)

    parts = []
    lines = md_text.splitlines()
    for li, line in enumerate(lines):
        if li in skip_lines:
            continue
        s = line.strip()
        if s.startswith("# "):
            title = s[2:].strip()
            parts.append(f'<h1>{md_inline(title)}</h1>')
        elif s.startswith("## ") and "国际动态" in s:
            title = s[3:].strip()
            parts.append(f'<h2 class="module-title">{md_inline(title)}</h2>')
            parts.append("<!--INTL-->")
        elif s.startswith("## ") and "国内动态" in s:
            title = s[3:].strip()
            parts.append(f'<h2 class="module-title">{md_inline(title)}</h2>')
            parts.append("<!--CN-->")
        elif s.startswith("## ") and "今日趋势点评" in s:
            title = s[3:].strip()
            parts.append('<section class="insight-section">'
                         f'<h2 class="insight-title">{md_inline(title)}</h2>')
        elif s.startswith("### "):
            title = s[4:].strip()
            parts.append(f'<h3>{md_inline(title)}</h3>')
        elif s.startswith(">"):
            content = s[1:].strip()
            if content == "":
                continue
            if content.startswith("📌") or "弹性原则" in content or "本简报覆盖" in content:
                parts.append(f'<div class="note-card">{md_inline(content)}</div>')
            else:
                parts.append(f'<blockquote>{md_inline(content)}</blockquote>')
        elif s.startswith("---"):
            parts.append('</section>')
            parts.append('<hr/>')
        elif s == "":
            continue
        elif s.startswith("*") and s.endswith("*") and len(s) > 2:
            inner = s.strip("*").strip()
            parts.append(f'<p class="foot">{md_inline(inner)}</p>')
        else:
            parts.append(f'<p>{md_inline(s)}</p>')

    body = "\n".join(parts)
    body = body.replace("<!--INTL-->", "\n".join(intl_cards))
    body = body.replace("<!--CN-->", "\n".join(cn_cards))
    if '<section class="insight-section">' in body and '</section>' not in body:
        body += '</section>'
    return body

CSS = """
:root{
  --bg:#f6f8fa; --surface:#ffffff; --text:#1f2328; --muted:#656d76;
  --border:#d0d7de; --accent:#2563eb; --accent2:#60a5fa;
  --card-bar:linear-gradient(90deg,#2563eb,#60a5fa);
  --insight-bg:linear-gradient(135deg,#eff6ff,#f0f9ff);
  --code-bg:#f6f8fa; --shadow:0 6px 24px rgba(0,0,0,.06);
  --badge-src-bg:#2563eb; --badge-src-fg:#fff;
  --badge-conf-bg:#f59e0b; --badge-conf-fg:#fff;
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#0d1117; --surface:#161b22; --text:#e6edf3; --muted:#9198a1;
    --border:#30363d; --accent:#60a5fa; --accent2:#93c5fd;
    --card-bar:linear-gradient(90deg,#60a5fa,#3b82f6);
    --insight-bg:linear-gradient(135deg,#0b1a2e,#0f2233);
    --code-bg:#161b22; --shadow:0 6px 24px rgba(0,0,0,.4);
    --badge-src-bg:#1d4ed8; --badge-conf-bg:#b45309;
  }
}
*{box-sizing:border-box}
body{
  margin:0; padding:24px 16px; background:var(--bg); color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",
    "Hiragino Sans GB","Microsoft YaHei",Roboto,Helvetica,Arial,sans-serif;
  font-size:16px; line-height:1.7; -webkit-font-smoothing:antialiased;
}
.container{
  max-width:860px; margin:0 auto; background:var(--surface);
  border-radius:16px; box-shadow:var(--shadow);
  padding:36px 40px; border:1px solid var(--border); overflow:hidden;
}
@media (max-width:640px){
  .container{padding:22px 18px; border-radius:12px}
  body{padding:12px 8px}
  .news-card{padding:16px 16px 14px}
  h1{font-size:1.4rem}
  h2{font-size:1.15rem}
}
h1{font-size:1.7rem; margin:0 0 10px; line-height:1.35; word-break:break-word}
h2{font-size:1.3rem; margin:34px 0 16px; line-height:1.4; word-break:break-word}
h3{font-size:1.08rem; margin:22px 0 10px}
p{margin:10px 0}
a{color:var(--accent); text-decoration:none}
code{
  background:var(--code-bg); padding:2px 6px; border-radius:5px;
  font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;
  font-size:.9em; border:1px solid var(--border);
}
.module-title{border-left:5px solid var(--accent); padding-left:12px}
.insight-title{border-left:none; padding-left:0; margin-top:0}
/* 新闻卡片 */
.news-card{
  position:relative; background:var(--surface);
  border:1px solid var(--border); border-radius:12px;
  padding:18px 20px 16px; margin:16px 0;
  box-shadow:0 1px 3px rgba(0,0,0,.04);
  transition:transform .18s ease, box-shadow .18s ease;
  overflow:hidden;
}
.news-card::before{
  content:""; position:absolute; top:0; left:0; right:0; height:4px;
  background:var(--card-bar); border-radius:12px 12px 0 0;
}
.news-card:hover{transform:translateY(-3px); box-shadow:0 10px 28px rgba(37,99,235,.12)}
.news-header{font-weight:700; font-size:1.06rem; margin:4px 0 10px; line-height:1.45}
.news-body p{margin:8px 0}
.label-badge{
  display:inline-block; font-size:.78rem; font-weight:700;
  color:var(--accent); background:rgba(37,99,235,.1);
  padding:2px 9px; border-radius:20px; margin:0 0 6px;
}
.news-meta{margin-top:12px; display:flex; flex-wrap:wrap; gap:8px}
.badge{
  display:inline-flex; align-items:center; gap:4px;
  font-size:.78rem; padding:4px 11px; border-radius:20px;
  font-weight:600; line-height:1.4; word-break:break-word;
}
.badge-source{background:var(--badge-src-bg); color:var(--badge-src-fg)}
.badge-conf{background:var(--badge-conf-bg); color:var(--badge-conf-fg)}
.note-card{
  background:var(--insight-bg); border:1px solid var(--border);
  border-left:5px solid var(--accent2); border-radius:10px;
  padding:14px 16px; margin:18px 0; color:var(--text); font-size:.95rem;
}
blockquote{
  border-left:4px solid var(--border); margin:14px 0; padding:6px 14px;
  color:var(--muted); background:var(--code-bg); border-radius:0 8px 8px 0;
}
.insight-section{
  background:var(--insight-bg); border:1px solid var(--border);
  border-left:5px solid var(--accent); border-radius:12px;
  padding:8px 22px 18px; margin:30px 0;
}
hr{border:none; border-top:1px solid var(--border); margin:28px 0}
.foot{color:var(--muted); font-size:.85rem; text-align:center; margin-top:24px}
"""


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<div class="container">
{body}
</div>
</body>
</html>
"""


def main():
    ensure_markdown_lib()
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()
    body = build_body(md_text)
    html = HTML_TEMPLATE.format(title=DOC_TITLE, css=CSS, body=body)
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK -> {HTML_PATH}")


if __name__ == "__main__":
    main()
