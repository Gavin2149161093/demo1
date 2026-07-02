#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 AI 日报 Markdown 转换为结构化 HTML（v2 排版规范）。
- 把每条新闻 <blockquote> 拆分为 <article class="news-card">
  内部拆分 header / news-body / news-meta
- 📝 与 📰 渲染为 .label-badge；来源/置信度渲染为两个 .badge（来源蓝底、置信度黄底）
- 📌 维度补充说明升级为 .note-card
- 今日趋势点评整段包裹为 <section class="insight-section">
- 处理 Python-Markdown 合并相邻引用块的问题：先按 🔹 / 📌 标记拆分 <blockquote>
依赖：markdown + pygments
"""
import re
import html as html_lib
from pathlib import Path
import markdown

BASE = Path(__file__).parent
MD_PATH = BASE / "2026-07-03-AI-Daily.md"
HTML_PATH = BASE / "2026-07-03-AI-Daily.html"
TITLE = "AI 行业每日热点深度简报 · 2026-07-03"

md_text = MD_PATH.read_text(encoding="utf-8")

# 1) Markdown -> HTML（合并相邻引用块由后续脚本按 🔹/📌 标记重新拆分）
html_body = markdown.markdown(
    md_text,
    extensions=["extra", "sane_lists", "codehilite", "fenced_code",
                "toc", "md_in_html", "nl2br"],
    extension_configs={
        "codehilite": {"guess_lang": False, "noclasses": True},
        "toc": {"permalink": False},
    },
)


def strip_tags(s: str) -> str:
    """去掉 HTML 标签，仅保留文本（含 emoji）。"""
    s = re.sub(r"<[^>]+>", "", s)
    return html_lib.unescape(s).strip()


def render_badges(src_conf_html: str) -> str:
    """从 `<code>来源</code> | **置信度**：⭐⭐⭐⭐⭐（5/5）` 段落生成两个徽章。"""
    src_m = re.search(r"<code>(.*?)</code>", src_conf_html, re.DOTALL)
    source = strip_tags(src_m.group(1)) if src_m else strip_tags(
        src_conf_html.split("|")[0])
    # 置信度：取 | 右侧的 ⭐ 串与分数
    right = src_conf_html.split("|", 1)[-1] if "|" in src_conf_html else src_conf_html
    conf_m = re.search(r"(⭐+(?:[（(]\d+/5[）)])?)", right)
    conf = conf_m.group(1) if conf_m else strip_tags(right)
    return (
        f'<span class="badge badge-source">📰 来源：{html_lib.escape(source)}</span>'
        f'<span class="badge badge-conf">置信度：{html_lib.escape(conf)}</span>'
    )


def build_card(paras: list) -> str:
    """把一个新闻卡片的 <p> 列表组装成 <article class="news-card">。"""
    # header = 第一个含 🔹 的段落
    header_html = paras[0]
    title = strip_tags(header_html)

    body_paras, meta_paras = [], []
    state = "title"  # title -> body -> meta
    label_summary = label_source = ""
    src_conf_html = ""
    for p in paras[1:]:
        txt = strip_tags(p)
        if txt.startswith("📝"):
            label_summary = txt
            state = "body"
            continue
        if txt.startswith("📰"):
            label_source = txt
            state = "meta"
            continue
        if state == "meta" and ("<code>" in p or "⭐" in p):
            src_conf_html = p
            continue
        if state == "body":
            body_paras.append(p)

    parts = [f'<header class="news-header">{html_lib.escape(title)}</header>']
    body_inner = ""
    if label_summary:
        body_inner += f'<span class="label-badge">{html_lib.escape(label_summary)}</span>'
    body_inner += "".join(f"<p>{bp}</p>" for bp in body_paras)
    parts.append(f'<div class="news-body">{body_inner}</div>')

    meta_inner = ""
    if label_source:
        meta_inner += f'<span class="label-badge">{html_lib.escape(label_source)}</span>'
    if src_conf_html:
        meta_inner += f'<div class="badges">{render_badges(src_conf_html)}</div>'
    parts.append(f'<footer class="news-meta">{meta_inner}</footer>')
    return '<article class="news-card">' + "".join(parts) + "</article>"


def build_note(paras: list) -> str:
    """把 📌 维度补充说明组装为 .note-card。"""
    header = strip_tags(paras[0])
    body = "".join(f"<p>{p}</p>" for p in paras[1:])
    return (
        f'<div class="note-card">'
        f'<div class="note-title">{html_lib.escape(header)}</div>'
        f'<div class="note-body">{body}</div></div>'
    )


def transform_blockquotes(html: str) -> str:
    """拆分被 Python-Markdown 合并的引用块，并升级为卡片/笔记结构。"""
    def repl(m):
        inner = m.group(1)
        paras = re.findall(r"<p>(.*?)</p>", inner, re.DOTALL)
        if not paras:
            return m.group(0)
        # 找到每个卡片的起点（含 🔹 或 📌 的 <p>）
        cards, cur = [], []
        for p in paras:
            if re.search(r"🔹|📌", strip_tags(p)):
                if cur:
                    cards.append(cur)
                cur = [p]
            else:
                if cur:
                    cur.append(p)
                # 不属于任何卡片的孤立段落（如顶部 meta 引用块）保留
                else:
                    cards.append([("__raw__", p)])
        if cur:
            cards.append(cur)

        out = []
        for c in cards:
            if len(c) == 1 and isinstance(c[0], tuple):
                out.append(f'<div class="report-meta">{c[0][1]}</div>')
                continue
            txt0 = strip_tags(c[0])
            if "📌" in txt0:
                out.append(build_note(c))
            elif "🔹" in txt0:
                out.append(build_card(c))
            else:
                out.append('<div class="report-meta">' +
                           "".join(f"<p>{p}</p>" for p in c) + "</div>")
        return "\n".join(out)

    # 非贪婪匹配最外层 <blockquote>…</blockquote>（日报中无嵌套）
    return re.sub(r"<blockquote>(.*?)</blockquote>", repl, html, flags=re.DOTALL)


html_body = transform_blockquotes(html_body)

# 2) 给模块标题（国际/国内）加 .module-title 类（保留已有 id 等属性）
def add_module_class(html: str) -> str:
    pat = re.compile(r'<h2([^>]*)>([^<]*(?:国际动态|国内动态)[^<]*</h2>)')
    def repl(m):
        attrs = m.group(1)
        if 'class=' in attrs:
            attrs = re.sub(r'class="([^"]*)"', r'class="\1 module-title"', attrs)
        else:
            attrs = attrs + ' class="module-title"'
        return f'<h2{attrs}>{m.group(2)}'
    return pat.sub(repl, html)

html_body = add_module_class(html_body)


# 3) 把"今日趋势点评"整段包裹为 <section class="insight-section">
def wrap_insight(html: str) -> str:
    idx = html.find("今日趋势点评")
    if idx == -1:
        return html
    # 找到包含该文字的 <h2 ...> 起始位置
    h2_start = html.rfind("<h2", 0, idx)
    if h2_start == -1:
        return html
    head, tail = html[:h2_start], html[h2_start:]
    # 在 tail 中找到紧跟该 h2 的关闭以及后续同级 h2（若有）作为边界
    return head + '<section class="insight-section">' + tail + "</section>"


html_body = wrap_insight(html_body)

CSS = """
:root{
  --bg:#f6f8fa; --surface:#ffffff; --fg:#1f2328; --muted:#656d76;
  --border:#d0d7de; --accent:#0969da; --accent-2:#1f6feb; --accent-soft:#ddf4ff;
  --quote-bg:#f6f8fa; --code-bg:#f6f8fa; --tag-bg:#eaeef2;
  --card-shadow:0 1px 2px rgba(0,0,0,.04),0 6px 18px rgba(0,0,0,.05);
  --card-hover-shadow:0 8px 24px rgba(9,105,218,.14),0 2px 6px rgba(0,0,0,.06);
  --bar-grad:linear-gradient(90deg,#0969da,#4aa3ff);
  --src-bg:#0969da; --src-fg:#ffffff;
  --conf-bg:#fff8d6; --conf-fg:#7a5c00; --conf-border:#f1d57a;
  --insight-bg:linear-gradient(180deg,#eef6ff,#f6fbff);
  --insight-border:#0969da;
  --label-bg:#eef4ff; --label-fg:#0a3d91; --label-border:#cfe3ff;
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#0d1117; --surface:#161b22; --fg:#e6edf3; --muted:#8b949e;
    --border:#30363d; --accent:#4493f8; --accent-2:#388bfd; --accent-soft:#15283b;
    --quote-bg:#0d1117; --code-bg:#0d1117; --tag-bg:#21262d;
    --card-shadow:0 1px 2px rgba(0,0,0,.4),0 8px 22px rgba(0,0,0,.45);
    --card-hover-shadow:0 10px 28px rgba(68,147,248,.22),0 2px 6px rgba(0,0,0,.5);
    --src-bg:#1f6feb; --src-fg:#ffffff;
    --conf-bg:#3a2f12; --conf-fg:#ffd75e; --conf-border:#5a4716;
    --insight-bg:linear-gradient(180deg,#0d1f33,#101a2b);
    --insight-border:#4493f8;
    --label-bg:#16243a; --label-fg:#9ec5ff; --label-border:#23395e;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; padding:0; background:var(--bg); color:var(--fg);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",
    "Hiragino Sans GB","Microsoft YaHei","Helvetica Neue",Helvetica,Arial,sans-serif;
  font-size:16px; line-height:1.75; word-wrap:break-word; overflow-wrap:anywhere;
  -webkit-font-smoothing:antialiased;
}
.wrap{
  max-width:860px; margin:32px auto; padding:40px 44px;
  background:var(--surface); border:1px solid var(--border); border-radius:16px;
  box-shadow:var(--card-shadow);
}
.report-meta{
  background:var(--accent-soft); border:1px solid var(--border);
  border-left:4px solid var(--accent); border-radius:10px;
  padding:14px 18px; margin:0 0 22px; color:var(--fg); font-size:.95em;
}
.report-meta p{margin:0 0 6px;} .report-meta p:last-child{margin-bottom:0;}
h1{font-size:2em; margin:.2em 0 .5em; font-weight:750; line-height:1.25;
  border-bottom:2px solid var(--border); padding-bottom:.3em; letter-spacing:-.01em;}
/* 模块标题：左侧 5px 蓝色竖条 */
h2.module-title{
  font-size:1.45em; margin:1.8em 0 1em; font-weight:700; line-height:1.3;
  padding:.25em 0 .25em .7em; border-left:5px solid var(--accent);
  background:linear-gradient(90deg,var(--accent-soft),transparent);
  border-radius:0 8px 8px 0;
}
h2{font-size:1.45em; margin:1.8em 0 1em; font-weight:700;}
h3{font-size:1.18em; margin:1.3em 0 .6em; font-weight:650;}
p{margin:0 0 14px;}
a{color:var(--accent); text-decoration:none;}
a:hover{text-decoration:underline;}
strong{font-weight:680;}
hr{height:1px; border:0; background:var(--border); margin:2em 0;}
code{font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;
  font-size:.88em; background:var(--code-bg); padding:.15em .4em; border-radius:5px;
  color:var(--fg); word-break:break-word;}
pre{background:var(--code-bg); border:1px solid var(--border); border-radius:8px;
  padding:14px 16px; overflow:auto; margin:0 0 16px;}
pre code{background:none; padding:0; font-size:.85em; line-height:1.5;}
table{border-collapse:collapse; width:100%; margin:0 0 16px; display:block; overflow:auto;}
table th,table td{border:1px solid var(--border); padding:8px 12px; text-align:left;}
table th{background:var(--quote-bg); font-weight:680;}
ul,ol{margin:0 0 14px; padding-left:1.6em;} li{margin:3px 0;}
img{max-width:100%;}

/* 新闻卡片 */
.news-card{
  position:relative; background:var(--surface); border:1px solid var(--border);
  border-radius:12px; padding:18px 20px 16px; margin:0 0 18px; overflow:hidden;
  box-shadow:var(--card-shadow); transition:transform .18s ease, box-shadow .18s ease;
}
.news-card::before{
  content:""; position:absolute; top:0; left:0; right:0; height:4px;
  background:var(--bar-grad);
}
.news-card:hover{transform:translateY(-3px); box-shadow:var(--card-hover-shadow);}
.news-header{font-size:1.06em; font-weight:700; line-height:1.45; margin:2px 0 12px;
  color:var(--fg);}
.news-body p{margin:0 0 12px;}
.news-body p:last-child{margin-bottom:0;}
/* 标签徽章 */
.label-badge{display:inline-block; font-size:.82em; font-weight:650;
  background:var(--label-bg); color:var(--label-fg);
  border:1px solid var(--label-border); padding:3px 10px; border-radius:999px;
  margin:0 0 10px; letter-spacing:.02em;}
/* 页脚 meta */
.news-meta{margin-top:6px;}
.badges{display:flex; flex-wrap:wrap; gap:8px; margin-top:4px;}
.badge{display:inline-flex; align-items:center; font-size:.8em; font-weight:650;
  padding:4px 12px; border-radius:999px; line-height:1.4; word-break:break-word;}
.badge-source{background:var(--src-bg); color:var(--src-fg);}
.badge-conf{background:var(--conf-bg); color:var(--conf-fg); border:1px solid var(--conf-border);}

/* 维度补充说明 / note-card */
.note-card{
  background:var(--accent-soft); border:1px dashed var(--border);
  border-left:4px solid var(--accent); border-radius:10px;
  padding:12px 16px; margin:0 0 20px;
}
.note-title{font-weight:700; margin-bottom:6px; color:var(--fg);}
.note-body p{margin:0 0 8px;} .note-body p:last-child{margin-bottom:0;}

/* 趋势点评洞察区：淡蓝渐变背景 + 左侧 5px 蓝色粗边框 */
.insight-section{
  background:var(--insight-bg); border:1px solid var(--border);
  border-left:5px solid var(--insight-border); border-radius:12px;
  padding:18px 22px; margin-top:1.6em;
}
.insight-section h2{margin-top:.2em;}
.insight-section h3{color:var(--accent-2);}

.foot{margin-top:28px; padding-top:16px; border-top:1px solid var(--border);
  font-size:.82em; color:var(--muted); text-align:center;}

@media (max-width:768px){
  .wrap{margin:0; padding:22px 16px; border-radius:0; box-shadow:none;}
  h1{font-size:1.55em;}
  h2,h2.module-title{font-size:1.2em;}
  .news-card{padding:16px 14px;}
  .news-header{font-size:1em;}
  .insight-section{padding:14px 14px;}
  .badge{font-size:.74em;}
  pre,table{max-width:100%;}
}
"""

html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
{html_body}
  <div class="foot">Generated from <code>2026-07-03-AI-Daily.md</code> · AI Daily Briefing · Week-27</div>
</div>
</body>
</html>
"""

HTML_PATH.write_text(html_doc, encoding="utf-8")
print(f"OK HTML written: {HTML_PATH} ({len(html_doc)} bytes)")
