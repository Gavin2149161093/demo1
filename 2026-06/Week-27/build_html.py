#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 AI 日报 Markdown 转换为带现代极简 CSS 样式的 HTML（GitHub Markdown 风格）。
依赖：markdown + pygments（代码高亮）
"""
import markdown
from pathlib import Path

MD_PATH = Path(__file__).parent / "2026-06-29-AI-Daily.md"
HTML_PATH = Path(__file__).parent / "2026-06-29-AI-Daily.html"

md_text = MD_PATH.read_text(encoding="utf-8")

# 使用扩展：表格、代码高亮、fenced code、目录锚点、属性列表
html_body = markdown.markdown(
    md_text,
    extensions=[
        "extra",
        "sane_lists",
        "codehilite",
        "fenced_code",
        "toc",
        "md_in_html",
        "nl2br",
    ],
    extension_configs={
        "codehilite": {"guess_lang": False, "noclasses": True},
        "toc": {"permalink": False},
    },
)

CSS = """
:root{
  --bg:#ffffff; --fg:#1f2328; --muted:#656d76; --border:#d0d7de;
  --accent:#0969da; --accent-soft:#ddf4ff; --quote-bg:#f6f8fa;
  --code-bg:#f6f8fa; --tag-bg:#eaeef2; --hover:#f3f4f6;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; padding:0; background:var(--bg); color:var(--fg);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",
    "Hiragino Sans GB","Microsoft YaHei","Helvetica Neue",Helvetica,Arial,
    sans-serif;
  font-size:16px; line-height:1.7; word-wrap:break-word;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:920px; margin:40px auto; padding:40px 56px;
  background:var(--bg); border:1px solid var(--border); border-radius:12px;
  box-shadow:0 1px 3px rgba(0,0,0,.04),0 8px 24px rgba(0,0,0,.04);
}
.markdown-body h1{font-size:2em; margin:.4em 0 .6em; font-weight:700;
  line-height:1.25; border-bottom:2px solid var(--border); padding-bottom:.3em;
  letter-spacing:-.01em;}
.markdown-body h2{font-size:1.5em; margin:1.6em 0 .6em; font-weight:650;
  padding:.3em .6em; border-radius:6px; line-height:1.3;
  background:linear-gradient(90deg,var(--accent-soft),transparent);
  border-left:4px solid var(--accent);}
.markdown-body h3{font-size:1.2em; margin:1.2em 0 .5em; font-weight:600;}
.markdown-body p{margin:0 0 14px;}
.markdown-body a{color:var(--accent); text-decoration:none; border-bottom:1px solid transparent;}
.markdown-body a:hover{border-bottom-color:var(--accent);}
.markdown-body strong{font-weight:650;}
.markdown-body hr{height:1px; border:0; background:var(--border); margin:2em 0;}
/* 引用块 —— 每条新闻卡片 */
.markdown-body blockquote{
  margin:0 0 18px; padding:16px 20px; color:var(--fg);
  background:var(--quote-bg); border:1px solid var(--border);
  border-left:4px solid var(--accent); border-radius:8px;
}
.markdown-body blockquote p{margin:0 0 8px;}
.markdown-body blockquote p:last-child{margin-bottom:0;}
.markdown-body blockquote strong{color:#0a2540;}
/* 代码 */
.markdown-body code{font-family:"SFMono-Regular",Consolas,"Liberation Mono",
  Menlo,monospace; font-size:.88em; background:var(--code-bg);
  padding:.2em .4em; border-radius:5px; color:#24292f;}
.markdown-body pre{background:var(--code-bg); border:1px solid var(--border);
  border-radius:8px; padding:14px 16px; overflow:auto; margin:0 0 16px;}
.markdown-body pre code{background:none; padding:0; font-size:.85em;
  line-height:1.5;}
/* 表格 */
.markdown-body table{border-collapse:collapse; width:100%; margin:0 0 16px;
  display:block; overflow:auto;}
.markdown-body table th,.markdown-body table td{border:1px solid var(--border);
  padding:8px 12px; text-align:left;}
.markdown-body table th{background:var(--quote-bg); font-weight:650;}
.markdown-body table tr:nth-child(2n){background:#fbfcfd;}
.markdown-body ul,.markdown-body ol{margin:0 0 14px; padding-left:1.6em;}
.markdown-body li{margin:3px 0;}
.markdown-body img{max-width:100%;}
/* 元信息头部 */
.meta{display:flex; flex-wrap:wrap; gap:8px; margin:0 0 22px;}
.meta span{font-size:.85em; color:var(--muted); background:var(--tag-bg);
  padding:3px 10px; border-radius:999px; border:1px solid var(--border);}
.foot{margin-top:28px; padding-top:16px; border-top:1px solid var(--border);
  font-size:.82em; color:var(--muted); text-align:center;}
@media (max-width:768px){
  .wrap{margin:0; padding:22px 18px; border:0; border-radius:0;}
  .markdown-body h1{font-size:1.6em;}
  .markdown-body h2{font-size:1.25em;}
}
"""

# 从 Markdown 顶部提取日期/周数作为头部 meta 胶囊（简单解析）
meta_html = ""
first_lines = md_text.splitlines()[:6]
meta_items = []
for ln in first_lines:
    if "日期" in ln and "2026-" in ln:
        meta_items.append("📅 " + ln.split("：",1)[-1].split("｜")[0].strip(" >"))
    if "ISO 周数" in ln:
        meta_items.append("🗂 " + ln.split("周数：",1)[-1].strip(" >"))
if meta_items:
    meta_html = '<div class="meta">' + "".join(
        f"<span>{m}</span>" for m in meta_items) + "</div>"

html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI 行业每日热点深度简报 · 2026-06-29</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="markdown-body">
{meta_html}
{html_body}
  </div>
  <div class="foot">Generated from <code>2026-06-29-AI-Daily.md</code> · AI Daily Briefing · Week-27</div>
</div>
</body>
</html>
"""

HTML_PATH.write_text(html_doc, encoding="utf-8")
print(f"✅ HTML written: {HTML_PATH} ({len(html_doc)} bytes)")
