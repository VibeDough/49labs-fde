#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全站设计系统与统一导航（v5.0）
================================
零第三方依赖、零外部请求。所有变量与类名使用 --sx- / .sx- / .pt- / .ov- 前缀，
与两册阅读器原有的 CSS 变量完全隔离，可安全注入任意页面。

对外接口：
  SITE_CSS / SITE_JS          全站共享样式与脚本
  site_bar(active, crumbs, px) 顶部导航 + 面包屑
  site_footer(px, full)        页脚站点地图
  inject(html, ...)            把导航外壳注入既有 HTML（阅读器 / 词典 / 题库 / 笔记）
  page_shell(...)              生成带完整外壳的新页面（门户 / 介绍 / 站点地图）
"""

import re
import html as ihtml

VERSION = "v5.0"

# 一级栏目：(key, 名称, 目标文件)
NAV_ITEMS = [
    ("home",      "门户",     "index.html"),
    ("intro",     "介绍",     "手册展示页.html"),
    ("learn",     "学习",     "01_主手册.html"),
    ("reading",   "精读",     "03_开源课程解读.html"),
    ("lookup",    "查阅",     "02_速查手册.html"),
    ("ask",       "追问",     "细节追问提示词库.html"),
    ("exam",      "考核",     "FDE工程师考核题库.html"),
    ("resources", "资料",     "站点地图.html"),
]

# 页脚站点地图分组
FOOT_GROUPS = [
    ("认识", [("入口门户", "index.html"), ("手册介绍", "手册展示页.html"),
             ("站点地图", "站点地图.html")]),
    ("学习", [("主手册（十四篇）", "01_主手册.html"), ("速查手册 A–Q", "02_速查手册.html"),
             ("开源课程精读", "03_开源课程解读.html"),
             ("19 节笔记", "参考资料/逐节笔记索引.html"),
             ("分步学习路径", "01_主手册.html#anchor-learning-path")]),
    ("查阅与追问", [("术语词典（291 条 / 11 类）", "术语词典.html"),
                ("细节追问提示词库", "细节追问提示词库.html"),
                ("自测题库（凭码进入）", "FDE工程师考核题库.html"),
                ("项目图示索引", "01_主手册.html#anchor-figures"),
                ("模型选型矩阵", "01_主手册.html#anchor-model"),
                ("语音 TTS 选型", "01_主手册.html#anchor-tts"),
                ("国内方案选型", "01_主手册.html#anchor-selection")]),
    ("资料", [("离线使用说明", "离线使用说明.md"), ("核验报告", "核验报告.md"),
             ("缺口清单", "01_主手册.html#anchor-reading")]),
]

SITE_CSS = r"""
/* ================= 全站设计系统（前缀 sx-，与阅读器变量隔离） ================= */
:root{
  --sx-bg:#f6f8fc; --sx-bg2:#eef3fb; --sx-card:#ffffff; --sx-ink:#101a2f;
  --sx-ink2:#3f4c63; --sx-mute:#72809a; --sx-line:#e2e9f4; --sx-line2:#cfdaeb;
  --sx-a1:#2f6bff; --sx-a2:#00a9bd; --sx-grad:linear-gradient(135deg,#2f6bff 0%,#00a9bd 100%);
  --sx-soft:#eaf1ff; --sx-ok:#0a8f4a; --sx-warn:#9a6508;
  --sx-sh1:0 2px 8px rgba(16,36,74,.05),0 12px 34px rgba(16,36,74,.07);
  --sx-sh2:0 6px 18px rgba(16,36,74,.09),0 24px 60px rgba(16,36,74,.12);
  --sx-r:18px; --sx-h:58px;
}
html[data-theme="dark"]{
  --sx-bg:#0a1020; --sx-bg2:#0d1528; --sx-card:#131d33; --sx-ink:#eef4ff;
  --sx-ink2:#bfcbe0; --sx-mute:#8797b2; --sx-line:#23304a; --sx-line2:#33425f;
  --sx-a1:#6ea0ff; --sx-a2:#3fd0dd; --sx-grad:linear-gradient(135deg,#6ea0ff 0%,#3fd0dd 100%);
  --sx-soft:#17294a; --sx-ok:#5ed39a; --sx-warn:#e7bd6a;
  --sx-sh1:0 2px 8px rgba(0,0,0,.28),0 12px 34px rgba(0,0,0,.34);
  --sx-sh2:0 6px 18px rgba(0,0,0,.34),0 24px 60px rgba(0,0,0,.46);
}
.sx-wrap{max-width:1180px;margin:0 auto;padding:0 26px}
.sx-a{color:var(--sx-a1);text-decoration:none}
.sx-a:hover{text-decoration:underline}

/* ---------- 顶部统一导航 ---------- */
.sx-bar{position:sticky;top:0;z-index:120;background:var(--sx-card);
  background:color-mix(in srgb,var(--sx-card) 86%,transparent);
  -webkit-backdrop-filter:saturate(180%) blur(18px);backdrop-filter:saturate(180%) blur(18px);
  border-bottom:1px solid var(--sx-line);transition:box-shadow .2s ease}
.sx-bar.on{box-shadow:0 6px 24px rgba(16,36,74,.10)}
.sx-bar-in{height:var(--sx-h);display:flex;align-items:center;gap:22px}
.sx-brand{display:flex;align-items:center;gap:10px;flex:none;color:var(--sx-ink);
  font-size:14.5px;font-weight:800;letter-spacing:-.01em;text-decoration:none;white-space:nowrap}
.sx-brand:hover{text-decoration:none}
.sx-mark{width:30px;height:30px;flex:none;display:block}
.sx-brand small{display:block;font-size:10px;font-weight:600;color:var(--sx-mute);
  letter-spacing:.12em;margin-top:-2px}
.sx-nav{display:flex;align-items:center;gap:4px;flex:1;min-width:0}
.sx-nav a{position:relative;padding:8px 13px;border-radius:10px;font-size:13.3px;font-weight:600;
  color:var(--sx-ink2);text-decoration:none;white-space:nowrap;transition:.16s}
.sx-nav a:hover{background:var(--sx-soft);color:var(--sx-a1);text-decoration:none}
.sx-nav a.cur{color:var(--sx-a1);background:var(--sx-soft)}
.sx-nav a.cur::after{content:"";position:absolute;left:13px;right:13px;bottom:2px;height:2px;
  border-radius:2px;background:var(--sx-grad)}
.sx-act{display:flex;align-items:center;gap:8px;flex:none}
.sx-ico{width:34px;height:34px;border:1px solid var(--sx-line);border-radius:10px;
  background:var(--sx-card);color:var(--sx-ink2);display:inline-flex;align-items:center;
  justify-content:center;font-size:15px;cursor:pointer;font-family:inherit}
.sx-ico:hover{border-color:var(--sx-a1);color:var(--sx-a1)}
.sx-btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;
  padding:11px 20px;border-radius:11px;font-size:13.5px;font-weight:700;
  font-family:inherit;cursor:pointer;text-decoration:none;border:1px solid transparent;transition:.18s}
.sx-btn.pri{background:var(--sx-grad);color:#fff;box-shadow:0 8px 22px rgba(47,107,255,.28)}
.sx-btn.pri:hover{color:#fff;text-decoration:none;transform:translateY(-2px);
  box-shadow:0 12px 28px rgba(47,107,255,.36)}
.sx-btn.gho{background:var(--sx-card);color:var(--sx-ink);border-color:var(--sx-line2)}
.sx-btn.gho:hover{color:var(--sx-a1);border-color:var(--sx-a1);text-decoration:none;transform:translateY(-2px)}
.sx-btn.sm{padding:9px 15px;font-size:12.8px;border-radius:10px}
.sx-burger{display:none}
.sx-panel{display:none}
@media(max-width:960px){
  .sx-nav{display:none}
  .sx-burger{display:inline-flex}
  .sx-panel{position:absolute;left:0;right:0;top:100%;background:var(--sx-card);
    border-bottom:1px solid var(--sx-line);box-shadow:var(--sx-sh2);padding:10px 20px 16px;
    display:none;grid-template-columns:repeat(2,1fr);gap:7px}
  .sx-panel.open{display:grid}
  .sx-panel a{font-size:13.5px;color:var(--sx-ink2);padding:10px 12px;border-radius:10px;
    background:var(--sx-bg2);text-decoration:none;font-weight:600}
  .sx-panel a.cur{color:var(--sx-a1);background:var(--sx-soft)}
  .sx-brand small{display:none}
}
@media(max-width:600px){
  :root{--sx-h:54px}
  .sx-wrap{padding:0 16px}
  .sx-bar-in{height:54px;gap:10px}
  .sx-brand{font-size:13px}
  .sx-mark{width:26px;height:26px}
  .sx-act .sx-btn{display:none}
}

/* ---------- 面包屑 ---------- */
.sx-crumb{background:var(--sx-bg2);border-bottom:1px solid var(--sx-line)}
.sx-crumb-in{display:flex;align-items:center;gap:8px;min-height:40px;flex-wrap:wrap;
  font-size:12.2px;color:var(--sx-mute)}
.sx-crumb a{color:var(--sx-mute);text-decoration:none}
.sx-crumb a:hover{color:var(--sx-a1)}
.sx-crumb .sep{opacity:.5}
.sx-crumb .now{color:var(--sx-ink);font-weight:700}
.sx-crumb .map{margin-left:auto;color:var(--sx-a1);font-weight:650;text-decoration:none}
.sx-crumb .map:hover{text-decoration:underline}

/* ---------- 页脚 ---------- */
.sx-foot{margin-top:64px;background:var(--sx-bg2);border-top:1px solid var(--sx-line);
  padding:44px 0 26px}
.sx-foot-grid{display:grid;grid-template-columns:1.3fr repeat(4,1fr);gap:26px}
.sx-foot .lead{font-size:13px;color:var(--sx-ink2);line-height:1.85;margin:12px 0 0;max-width:260px}
.sx-foot h4{font-size:12px;font-weight:800;letter-spacing:.08em;color:var(--sx-ink);
  margin:0 0 11px;text-transform:uppercase}
.sx-foot ul{list-style:none;margin:0;padding:0}
.sx-foot li{margin:0 0 7px}
.sx-foot li a{font-size:12.6px;color:var(--sx-mute);text-decoration:none}
.sx-foot li a:hover{color:var(--sx-a1)}
.sx-foot-bot{margin-top:32px;padding-top:18px;border-top:1px solid var(--sx-line);
  display:flex;flex-wrap:wrap;gap:10px;justify-content:space-between;
  font-size:11.8px;color:var(--sx-mute);line-height:1.8}
.sx-slim{padding:16px 0 22px;border-top:1px solid var(--sx-line);
  display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center;
  font-size:12px;color:var(--sx-mute)}
.sx-slim a{color:var(--sx-mute);text-decoration:none}
.sx-slim a:hover{color:var(--sx-a1)}
.sx-slim .v{margin-left:auto}
@media(max-width:900px){.sx-foot-grid{grid-template-columns:repeat(2,1fr)}.sx-foot .flead{grid-column:1/-1}}
@media(max-width:520px){.sx-foot-grid{grid-template-columns:1fr 1fr;gap:18px}
  .sx-foot .flead{grid-column:1/-1}.sx-crumb .map{margin-left:0;width:100%}}

/* ---------- 注入到阅读器时的避让 ---------- */
body.has-site .topbar{top:var(--sx-h)}
body.has-site .sidebar{top:calc(var(--sx-h) + var(--topbar-h));
  height:calc(100vh - var(--sx-h) - var(--topbar-h))}
body.has-site .content [id^="sec-"],body.has-site .anchor-flag{
  scroll-margin-top:calc(var(--sx-h) + var(--topbar-h) + 14px)}
@media(max-width:1000px){
  body.has-site .sidebar{top:var(--sx-h);height:calc(100vh - var(--sx-h))}
}
.sx-bar,.sx-crumb,.sx-foot,.sx-slim{-webkit-print-color-adjust:exact;print-color-adjust:exact}
@media print{.sx-bar,.sx-crumb,.sx-panel,.sx-foot,.sx-slim{display:none!important}
  body.has-site .topbar{top:0}body.has-site .sidebar{display:none}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""

SITE_JS = r"""
(function(){
'use strict';
var root=document.documentElement;
/* --sx-h 由 CSS 按断点给定（58px / 54px）。不在此处用 ResizeObserver 回写：
   该变量本身参与 .sx-bar-in 高度计算，回写会形成「观测→改高度→再观测」循环。 */
var bar=document.querySelector('.sx-bar');
function shadow(){if(bar)bar.classList.toggle('on',window.scrollY>8);}
shadow();window.addEventListener('scroll',shadow,{passive:true});
var tb=document.getElementById('sxTheme');
var tb2=document.getElementById('themeBtn');
function paint(){
  var dark=root.getAttribute('data-theme')==='dark';
  var ic=dark?'☀️':'🌙', tt=dark?'切到浅色':'切到深色';
  if(tb){tb.textContent=ic;tb.title=tt;}
  if(tb2){tb2.textContent=ic;tb2.title=tt;}
}
if(tb)tb.addEventListener('click',function(){
  var d=root.getAttribute('data-theme')==='dark';
  root.setAttribute('data-theme',d?'light':'dark');
  try{localStorage.setItem('fde-theme',d?'light':'dark');}catch(e){}
  paint();
});
/* 阅读器 / 题库页各有自己的 themeBtn：任一按钮改变 data-theme 时，两个图标同步 */
if(window.MutationObserver){
  new MutationObserver(paint).observe(root,{attributes:true,attributeFilter:['data-theme']});
}
paint();
var bg=document.getElementById('sxBurger'),pn=document.getElementById('sxPanel');
if(bg&&pn)bg.addEventListener('click',function(){
  var open=pn.classList.toggle('open');bg.setAttribute('aria-expanded',open?'true':'false');
});
document.addEventListener('keydown',function(e){
  if(e.key==='Escape'&&pn&&pn.classList.contains('open')){pn.classList.remove('open');
    if(bg)bg.setAttribute('aria-expanded','false');}
});
})();
"""

MARK_SVG = (
    '<svg class="sx-mark" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg" '
    'role="img" aria-label="站点标志">'
    '<defs><linearGradient id="sxg" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#2f6bff"/><stop offset="1" stop-color="#00a9bd"/>'
    '</linearGradient></defs>'
    '<rect x="2" y="2" width="28" height="28" rx="9" fill="url(#sxg)"/>'
    '<path d="M9 21.5V10.5h12M9 16h9" fill="none" stroke="#fff" stroke-width="2.4" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    '<circle cx="22" cy="21.5" r="2.5" fill="#fff"/></svg>'
)


def esc(s):
    return ihtml.escape(str(s), quote=True)


def site_bar(active, crumbs, px=""):
    links = ''.join(
        '<a class="%s" href="%s">%s</a>'
        % ('cur' if k == active else '', px + href, name)
        for k, name, href in NAV_ITEMS)
    panel = ''.join(
        '<a class="%s" href="%s">%s</a>'
        % ('cur' if k == active else '', px + href, name)
        for k, name, href in NAV_ITEMS)
    crumb = ''
    if crumbs:
        parts = []
        for i, (label, href) in enumerate(crumbs):
            if i:
                parts.append('<span class="sep">/</span>')
            if href:
                parts.append('<a href="%s">%s</a>' % (px + href, label))
            else:
                parts.append('<span class="now">%s</span>' % label)
        crumb = ('<div class="sx-crumb"><div class="sx-wrap sx-crumb-in">%s'
                 '<a class="map" href="%s站点地图.html">🗺 站点地图</a>'
                 '</div></div>') % (''.join(parts), px)
    return (
        '<div class="sx-bar"><div class="sx-wrap sx-bar-in">'
        '<a class="sx-brand" href="%sindex.html">%s'
        '<span>企业智能体交付实战<small>ENTERPRISE AGENT DELIVERY</small></span></a>'
        '<nav class="sx-nav" aria-label="站点主导航">%s</nav>'
        '<div class="sx-act">'
        '<button class="sx-ico" id="sxTheme" type="button" title="切换深浅色" aria-label="切换深浅色">🌙</button>'
        '<a class="sx-btn pri sm" href="%s01_主手册.html">开始学习 →</a>'
        '<button class="sx-ico sx-burger" id="sxBurger" type="button" '
        'aria-label="打开导航菜单" aria-expanded="false">☰</button>'
        '</div></div><div class="sx-panel" id="sxPanel">%s</div></div>%s'
        % (px, MARK_SVG, links, px, panel, crumb))


def site_footer(px="", full=True):
    if not full:
        return ('<div class="sx-wrap"><div class="sx-slim">'
                '<a href="%sindex.html">🏠 返回门户</a>'
                '<a href="%s手册展示页.html">🎯 手册介绍</a>'
                '<a href="%s站点地图.html">🗺 站点地图</a>'
                '<a href="%s01_主手册.html">📖 主手册</a>'
                '<a href="%sFDE工程师考核题库.html">📝 考核题库</a>'
                '<a href="%s细节追问提示词库.html">🔍 细节追问</a>'
                '<span class="v">企业级智能体交付实战手册 · %s · 离线自包含</span>'
                '</div></div>' % (px, px, px, px, px, px, VERSION))
    cols = ''
    for title, items in FOOT_GROUPS:
        lis = ''.join('<li><a href="%s%s">%s</a></li>' % (px, href, esc(label))
                      for label, href in items)
        cols += '<div><h4>%s</h4><ul>%s</ul></div>' % (esc(title), lis)
    mark2 = MARK_SVG.replace('id="sxg"', 'id="sxg2"').replace('url(#sxg)', 'url(#sxg2)')
    return ('<footer class="sx-foot"><div class="sx-wrap"><div class="sx-foot-grid">'
            '<div class="flead"><a class="sx-brand" href="%sindex.html">%s'
            '<span>企业智能体交付实战<small>ENTERPRISE AGENT DELIVERY</small></span></a>'
            '<p class="lead">面向全行业、厂商中立的 FDE 能力体系与实施标准。'
            '门户 → 介绍 → 详细三层导航，全部资源本地存放，不发起任何网络请求。</p></div>'
            '%s</div><div class="sx-foot-bot">'
            '<span>© 企业级智能体交付实战手册 · %s ｜ 独立学习整理，非官方教材 / 非官方题库</span>'
            '<span>产品与开源项目名称均为公开资料举例，不构成推荐、排名、背书或采购建议；'
            '平台功能、许可与规格以当期官方文档为准。</span>'
            '</div></div></footer>' % (px, mark2, cols, VERSION))


def _head_meta(title, description):
    return ('<meta name="description" content="%s">'
            '<meta name="theme-color" content="#2f6bff">'
            '<meta property="og:type" content="website">'
            '<meta property="og:title" content="%s">'
            '<meta property="og:description" content="%s">'
            % (esc(description), esc(title), esc(description)))


def inject(html_text, active, crumbs, px="", full_footer=False,
           title="", description=""):
    """把全站导航注入既有 HTML。不改动原有 DOM 结构，只追加 head 样式、body 首尾片段。"""
    bar = site_bar(active, crumbs, px)
    foot = site_footer(px, full=full_footer)
    js = '<script>%s</script>' % SITE_JS
    css = '<style>%s</style>' % SITE_CSS
    meta = _head_meta(title, description) if title else ''

    if '</head>' in html_text:
        html_text = html_text.replace('</head>', meta + css + '</head>', 1)
    m = re.search(r'<body[^>]*>', html_text)
    if m:
        tag = m.group(0)
        if 'class=' in tag:
            newtag = tag.replace('class="', 'class="has-site ', 1)
        else:
            newtag = tag[:-1] + ' class="has-site">'
        html_text = (html_text[:m.start()] + newtag + bar + html_text[m.end():])
    if '</body>' in html_text:
        html_text = html_text.replace('</body>', foot + js + '</body>', 1)
    return html_text


def page_shell(title, description, active, crumbs, body_html,
               extra_css="", extra_js="", px=""):
    """生成一个带完整站点外壳的新页面。"""
    return (
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="color-scheme" content="light dark">'
        '<title>%s</title>%s'
        '<script>try{var t=localStorage.getItem("fde-theme");if(t)'
        'document.documentElement.setAttribute("data-theme",t);}catch(e){}</script>'
        '<style>%s%s</style></head><body class="has-site">%s%s'
        '<script>%s%s</script></body></html>'
        % (esc(title), _head_meta(title, description), SITE_CSS, extra_css,
           site_bar(active, crumbs, px), body_html + site_footer(px, full=True),
           SITE_JS, extra_js))
