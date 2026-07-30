# -*- coding: utf-8 -*-
"""
将 AI 每日简报 Markdown 转换为带 v2 结构化样式的 HTML。
- 使用 markdown 库转换
- 后处理：把每条新闻 <blockquote> 拆为 <article class="news-card">
- 摘要/来源渲染为 .label-badge；信息来源/置信度渲染为独立 .badge
- 维度补充说明等非新闻引用块升级为 .note-card
- 今日趋势点评包裹为 <section class="insight-section">
- CSS 内嵌：860px 容器、卡片顶部蓝色渐变条、hover 上浮、模块标题蓝色竖条、
  洞察区淡蓝渐变 + 蓝色粗边框、来源徽章蓝底/置信度徽章黄底、暗黑模式、手机自适应
"""
import re
import markdown

MD_PATH = "/workspace/demo1/2026-07/Week-31/2026-07-30-AI-Daily.md"
HTML_PATH = "/workspace/demo1/2026-07/Week-31/2026-07-30-AI-Daily.html"


def parse_card(card_html):
    """解析单条新闻卡片 HTML，返回 (title, body, source, confidence)。"""
    title_m = re.search(r'<p><strong>🔹\s*(.*?)</strong></p>', card_html)
    title = title_m.group(1).strip() if title_m else ''

    body_m = re.search(
        r'<p>📝\s*<strong>摘要</strong></p>(.*?)<p>📰\s*<strong>来源与置信度</strong></p>',
        card_html, re.DOTALL)
    body = body_m.group(1).strip() if body_m else ''

    meta_m = re.search(
        r'<p>📰\s*<strong>来源与置信度</strong></p>(.*)',
        card_html, re.DOTALL)
    meta = meta_m.group(1).strip() if meta_m else ''

    src_m = re.search(r'<code>(.*?)</code>', meta)
    source = src_m.group(1).strip() if src_m else (meta or '')

    conf_m = re.search(r'置信度</strong>：([^<]*)', meta)
    confidence = conf_m.group(1).strip() if conf_m else ''

    return title, body, source, confidence


def build_card(title, body, source, confidence):
    safe_title = title or ''
    return (
        '<article class="news-card">\n'
        '  <header class="news-header"><span class="card-bullet">🔹</span> '
        f'{safe_title}</header>\n'
        '  <div class="news-body">\n'
        '    <span class="label-badge">📝 摘要</span>\n'
        f'    <div class="news-content">{body}</div>\n'
        '  </div>\n'
        '  <footer class="news-meta">\n'
        '    <span class="label-badge">📰 来源与置信度</span>\n'
        '    <div class="badges">\n'
        f'      <span class="badge badge-source">{source}</span>\n'
        f'      <span class="badge badge-confidence">置信度 {confidence}</span>\n'
        '    </div>\n'
        '  </footer>\n'
        '</article>'
    )


def replace_blockquote(m):
    inner = m.group(1)
    if '🔹' in inner:
        # 处理 Python-Markdown 合并相邻引用块：按 🔹 标记拆分
        parts = re.split(r'(?=<p><strong>🔹)', inner)
        cards = []
        for p in parts:
            if '🔹' not in p:
                continue
            title, body, source, confidence = parse_card(p)
            cards.append(build_card(title, body, source, confidence))
        return '\n'.join(cards)
    else:
        # 非新闻引用块（如维度说明/弹性说明/头部说明）升级为 note-card
        return f'<div class="note-card">{inner}</div>'


def main():
    with open(MD_PATH, 'r', encoding='utf-8') as f:
        md_text = f.read()

    html_body = markdown.markdown(md_text, extensions=['sane_lists'])

    # 拆分出“今日趋势点评”洞察区
    insight_marker = '<h2>三、📊 今日趋势点评'
    idx = html_body.find(insight_marker)
    if idx == -1:
        main_part, insight_part = html_body, ''
    else:
        main_part, insight_part = html_body[:idx], html_body[idx:]

    # 处理引用块 -> news-card / note-card
    main_part = re.sub(
        r'<blockquote>(.*?)</blockquote>',
        replace_blockquote,
        main_part,
        flags=re.DOTALL,
    )

    # 模块标题加 class（左侧蓝色竖条）
    main_part = main_part.replace(
        '<h2>🌍 一、国际动态（International）</h2>',
        '<h2 class="module-title">🌍 一、国际动态（International）</h2>')
    main_part = main_part.replace(
        '<h2>🇨🇳 二、国内动态（China）</h2>',
        '<h2 class="module-title">🇨🇳 二、国内动态（China）</h2>')

    # 洞察区包裹
    if insight_part:
        insight_html = f'<section class="insight-section">\n{insight_part}\n</section>'
    else:
        insight_html = ''

    css = """
:root{
  --bg:#f6f8fa;
  --container-bg:#ffffff;
  --text:#1f2328;
  --text-muted:#57606a;
  --border:#d0d7de;
  --card-bg:#ffffff;
  --card-border:#e6e8eb;
  --blue:#2f81f7;
  --blue-dark:#1f6feb;
  --blue-grad:linear-gradient(90deg,#2f81f7,#1f6feb);
  --insight-bg:linear-gradient(180deg,#eef4ff,#f7faff);
  --badge-source-bg:#2f81f7;
  --badge-source-text:#ffffff;
  --badge-conf-bg:#f5c518;
  --badge-conf-text:#3b2f00;
  --label-bg:#eef2f7;
  --label-text:#1f6feb;
  --code-bg:#f6f8fa;
  --shadow:0 6px 24px rgba(31,35,40,.08);
  --shadow-hover:0 14px 34px rgba(31,35,40,.16);
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#0d1117;
    --container-bg:#161b22;
    --text:#e6edf3;
    --text-muted:#8b949e;
    --border:#30363d;
    --card-bg:#161b22;
    --card-border:#30363d;
    --blue:#4493f8;
    --blue-dark:#2f81f7;
    --blue-grad:linear-gradient(90deg,#4493f8,#2f81f7);
    --insight-bg:linear-gradient(180deg,#13203a,#0d1626);
    --badge-source-bg:#2f81f7;
    --badge-source-text:#ffffff;
    --badge-conf-bg:#b7920a;
    --badge-conf-text:#1a1400;
    --label-bg:#21262d;
    --label-text:#79c0ff;
    --code-bg:#21262d;
    --shadow:0 6px 24px rgba(0,0,0,.45);
    --shadow-hover:0 14px 34px rgba(0,0,0,.6);
  }
}
*{box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{
  margin:0;padding:32px 16px 64px;
  background:var(--bg);
  color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",Helvetica,Arial,sans-serif;
  line-height:1.75;
  font-size:16px;
  -webkit-font-smoothing:antialiased;
}
.container{
  max-width:860px;
  margin:0 auto;
  background:var(--container-bg);
  border-radius:16px;
  box-shadow:var(--shadow);
  padding:40px 44px 48px;
  overflow:hidden;
}
h1{
  font-size:1.9rem;line-height:1.35;margin:0 0 18px;
  font-weight:700;color:var(--text);
}
h2{
  font-size:1.32rem;margin:42px 0 18px;font-weight:700;
  padding-bottom:8px;border-bottom:1px solid var(--border);
  color:var(--text);
}
h2.module-title{
  border-left:5px solid var(--blue);
  padding-left:14px;
  border-bottom:none;
  margin-top:46px;
}
h3{
  font-size:1.08rem;margin:26px 0 10px;font-weight:700;color:var(--blue-dark);
}
p{margin:0 0 12px;}
a{color:var(--blue-dark);}
code{
  background:var(--code-bg);padding:2px 6px;border-radius:6px;
  font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;
  font-size:.9em;
}
pre{
  background:var(--code-bg);padding:14px 16px;border-radius:10px;
  overflow:auto;border:1px solid var(--border);
}
pre code{background:none;padding:0;}
hr{border:none;border-top:1px solid var(--border);margin:30px 0;}

/* 顶部说明 note-card */
.note-card{
  background:var(--code-bg);
  border:1px solid var(--border);
  border-radius:12px;
  padding:14px 18px;
  margin:0 0 22px;
  color:var(--text-muted);
  font-size:.95rem;
}
.note-card p{margin:0;}

/* 新闻卡片 */
.news-card{
  position:relative;
  background:var(--card-bg);
  border:1px solid var(--card-border);
  border-radius:12px;
  padding:20px 22px 18px;
  margin:0 0 18px;
  box-shadow:0 1px 2px rgba(31,35,40,.04);
  transition:transform .2s ease, box-shadow .2s ease, border-color .2s ease;
  overflow:hidden;
}
.news-card::before{
  content:"";position:absolute;top:0;left:0;right:0;height:4px;
  background:var(--blue-grad);border-radius:12px 12px 0 0;
}
.news-card:hover{
  transform:translateY(-4px);
  box-shadow:var(--shadow-hover);
  border-color:var(--blue);
}
.news-header{
  font-weight:700;font-size:1.05rem;line-height:1.5;
  color:var(--text);margin-bottom:12px;
}
.card-bullet{margin-right:2px;}
.news-body{margin-bottom:12px;}
.news-content{margin-top:8px;color:var(--text);}
.news-content p{margin:0 0 10px;}
.news-content p:last-child{margin-bottom:0;}
.news-meta{margin-top:6px;}
.badges{margin-top:8px;display:flex;flex-wrap:wrap;gap:8px;}

/* 小标签 */
.label-badge{
  display:inline-block;
  background:var(--label-bg);
  color:var(--label-text);
  font-size:.78rem;font-weight:600;
  padding:3px 10px;border-radius:999px;
  letter-spacing:.02em;
}

/* 圆角徽章 */
.badge{
  display:inline-flex;align-items:center;
  font-size:.8rem;font-weight:600;
  padding:4px 12px;border-radius:999px;
  line-height:1.4;word-break:break-word;
}
.badge-source{background:var(--badge-source-bg);color:var(--badge-source-text);}
.badge-confidence{background:var(--badge-conf-bg);color:var(--badge-conf-text);}

/* 洞察区 */
.insight-section{
  margin-top:42px;
  background:var(--insight-bg);
  border-left:5px solid var(--blue);
  border-radius:0 12px 12px 0;
  padding:22px 26px 26px;
}
.insight-section > h2{
  border:none;padding:0 0 6px;margin-top:0;
}
.insight-section h3{margin-top:22px;}

/* 页脚 */
.doc-footer{
  margin-top:42px;padding-top:18px;
  border-top:1px solid var(--border);
  color:var(--text-muted);font-size:.85rem;text-align:center;
}

/* 手机自适应 */
@media (max-width:640px){
  body{padding:14px 8px 40px;font-size:15px;}
  .container{padding:24px 18px 30px;border-radius:12px;}
  h1{font-size:1.5rem;}
  h2{font-size:1.16rem;margin-top:34px;}
  h2.module-title{padding-left:10px;}
  .news-card{padding:16px 16px 14px;}
  .news-header{font-size:1rem;}
  .insight-section{padding:18px 16px 20px;}
  .badges{gap:6px;}
  .badge{font-size:.74rem;padding:4px 10px;}
}
/* 防止任何元素横向溢出 */
img,table,pre,code{max-width:100%;}
"""

    full_html = (
        '<!DOCTYPE html>\n'
        '<html lang="zh-CN">\n'
        '<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>AI 行业每日热点深度简报 · 2026-07-30</title>\n'
        f'<style>{css}</style>\n'
        '</head>\n'
        '<body>\n'
        '<div class="container">\n'
        f'{main_part}\n'
        f'{insight_html}\n'
        '<footer class="doc-footer">由自动化流程生成 · 数据窗口过去 24–72 小时 · '
        '置信度仅供参考</footer>\n'
        '</div>\n'
        '</body>\n'
        '</html>\n'
    )

    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f'OK -> {HTML_PATH}')
    # 简单校验
    print('news-card count:', full_html.count('class="news-card"'))
    print('badge-source count:', full_html.count('badge-source'))
    print('badge-confidence count:', full_html.count('badge-confidence'))
    print('insight-section:', 'insight-section' in full_html)


if __name__ == '__main__':
    main()
