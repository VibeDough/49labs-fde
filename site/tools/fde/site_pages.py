#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v5.0 三个站点级页面：扁平化入口门户 / 手册介绍 / 站点地图
=====================================================
全部使用 site_chrome.py 的统一设计系统，零外部资源，可直接静态托管上线。

信息架构（三层）：
  L0 门户 index.html            品牌、价值、导航总览、来意分流
  L1 介绍 手册展示页.html       是什么、能力体系、结构、节奏、适用与边界
  L2 详细 学习/查阅/考核/资料   主手册、速查、题库、词典、笔记、说明、报告
  L2 第三册 开源课程精读        独立模块，逐章解读开源 FDE 商业交付方法论
  横切能力 细节追问            每个学习点 × 5 个角度 → 可复制到任意 AI 的提示词库
"""

import site_chrome as sc

# ---------------------------------------------------------------- 共享页面样式
PAGE_CSS = r"""
body{background:var(--sx-bg);color:var(--sx-ink);
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","PingFang SC","Microsoft YaHei",sans-serif;
  font-size:15px;line-height:1.75;-webkit-font-smoothing:antialiased;
  -webkit-text-size-adjust:100%;margin:0}
*{box-sizing:border-box}
a{color:var(--sx-a1);text-decoration:none}a:hover{text-decoration:underline}
.pt-main,.ov-main,.sm-main{display:block}

/* ---------- Hero ---------- */
.pt-hero{position:relative;overflow:hidden;padding:74px 0 62px;
  background:radial-gradient(900px 460px at 78% -8%,rgba(47,107,255,.16),transparent 62%),
             radial-gradient(680px 400px at 4% 92%,rgba(0,169,189,.13),transparent 64%),
             var(--sx-bg)}
.pt-hero::before{content:"";position:absolute;inset:0;pointer-events:none;opacity:.5;
  background-image:linear-gradient(var(--sx-line) 1px,transparent 1px),
                   linear-gradient(90deg,var(--sx-line) 1px,transparent 1px);
  background-size:46px 46px;
  -webkit-mask-image:linear-gradient(180deg,rgba(0,0,0,.75),transparent 82%);
  mask-image:linear-gradient(180deg,rgba(0,0,0,.75),transparent 82%)}
.pt-hero .sx-wrap{position:relative}
.pt-grid{display:grid;grid-template-columns:1.08fr .92fr;gap:52px;align-items:center}
.pt-kicker{display:inline-flex;align-items:center;gap:9px;font-size:11.5px;font-weight:800;
  letter-spacing:.14em;color:var(--sx-a1);background:var(--sx-card);
  border:1px solid var(--sx-line);border-radius:999px;padding:7px 14px;box-shadow:var(--sx-sh1)}
.pt-kicker i{width:7px;height:7px;border-radius:50%;background:var(--sx-grad);display:block}
.pt-h1{font-size:clamp(36px,5vw,60px);line-height:1.13;letter-spacing:-.042em;
  font-weight:800;margin:22px 0 18px}
.pt-grad{background:var(--sx-grad);-webkit-background-clip:text;background-clip:text;
  color:transparent;-webkit-text-fill-color:transparent}
.pt-sub{font-size:16.5px;line-height:1.9;color:var(--sx-ink2);margin:0 0 26px;max-width:560px}
.pt-cta{display:flex;flex-wrap:wrap;gap:11px;margin-bottom:18px}
.pt-note{font-size:12.5px;color:var(--sx-mute);display:flex;flex-wrap:wrap;gap:8px 18px}
.pt-note span::before{content:"✓";color:var(--sx-a2);font-weight:800;margin-right:6px}
.pt-visual{background:var(--sx-card);border:1px solid var(--sx-line);border-radius:24px;
  padding:22px;box-shadow:var(--sx-sh2);position:relative}
.pt-visual::after{content:"";position:absolute;inset:-1px;border-radius:24px;pointer-events:none;
  background:linear-gradient(135deg,rgba(47,107,255,.10),transparent 55%,rgba(0,169,189,.10))}
.pt-visual svg{width:100%;height:auto;display:block}
.pt-vhead{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:12px}
.pt-vhead b{font-size:13.5px;letter-spacing:-.01em}
.pt-vhead span{font-size:10.5px;font-weight:800;letter-spacing:.1em;color:var(--sx-mute)}
.pt-vfoot{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:14px}
.pt-vfoot div{background:var(--sx-bg2);border:1px solid var(--sx-line);border-radius:11px;
  padding:9px 10px;text-align:center}
.pt-vfoot b{display:block;font-size:18px;color:var(--sx-a1);line-height:1.3}
.pt-vfoot span{font-size:10.5px;color:var(--sx-mute)}

/* ---------- 数据条 ---------- */
.pt-stats{display:grid;grid-template-columns:repeat(6,1fr);gap:0;
  background:var(--sx-card);border:1px solid var(--sx-line);border-radius:var(--sx-r);
  box-shadow:var(--sx-sh1);overflow:hidden;margin-top:-2px;position:relative}
.pt-stats div{padding:20px 12px;text-align:center;border-right:1px solid var(--sx-line)}
.pt-stats div:last-child{border-right:0}
.pt-stats b{display:block;font-size:29px;font-weight:800;letter-spacing:-.03em;line-height:1.2;
  background:var(--sx-grad);-webkit-background-clip:text;background-clip:text;
  color:transparent;-webkit-text-fill-color:transparent}
.pt-stats span{font-size:11.8px;color:var(--sx-mute)}

/* ---------- 通用区块 ---------- */
.pt-sec,.ov-sec-wrap,.sm-sec{padding-top:64px}
.pt-sec-head{display:flex;align-items:flex-start;gap:16px;margin-bottom:22px}
.pt-sec-num{font-size:34px;font-weight:800;line-height:1;letter-spacing:-.04em;
  background:var(--sx-grad);-webkit-background-clip:text;background-clip:text;
  color:transparent;-webkit-text-fill-color:transparent;flex:none;padding-top:2px}
.pt-sec-head h2,.sm-sec h2{font-size:25px;letter-spacing:-.025em;margin:0 0 4px;font-weight:800}
.pt-sec-head p,.sm-sec p.lead{font-size:13.5px;color:var(--sx-mute);margin:0;line-height:1.75}

/* ---------- 卡片 ---------- */
.sx-cards{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.sx-card{display:block;background:var(--sx-card);border:1px solid var(--sx-line);
  border-radius:16px;padding:20px 21px;color:var(--sx-ink);box-shadow:var(--sx-sh1);
  transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease;position:relative}
.sx-card:hover{transform:translateY(-3px);box-shadow:var(--sx-sh2);
  border-color:var(--sx-a1);text-decoration:none;color:var(--sx-ink)}
.sx-card .ic{width:38px;height:38px;border-radius:11px;display:flex;align-items:center;
  justify-content:center;font-size:19px;background:var(--sx-soft);margin-bottom:12px}
.sx-card h3{font-size:16px;margin:0 0 7px;font-weight:750;letter-spacing:-.015em}
.sx-card p{font-size:12.9px;line-height:1.8;color:var(--sx-mute);margin:0 0 13px}
.sx-card .go{font-size:12.5px;font-weight:750;color:var(--sx-a1)}
.sx-card .badge{font-size:9.5px;font-weight:800;letter-spacing:.06em;color:#fff;
  background:var(--sx-grad);border-radius:999px;padding:2px 8px;margin-left:7px;vertical-align:2px}
.sx-card.wide{grid-column:1/-1}
.sx-card.hl{background:linear-gradient(135deg,var(--sx-soft),var(--sx-card) 72%);
  border-color:var(--sx-a1)}

/* ---------- 三层路径 ---------- */
.pt-layers{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;position:relative}
.pt-layer{background:var(--sx-card);border:1px solid var(--sx-line);border-radius:18px;
  padding:24px 22px;box-shadow:var(--sx-sh1);position:relative;overflow:hidden}
.pt-layer::before{content:"";position:absolute;left:0;top:0;right:0;height:3px;background:var(--sx-grad)}
.pt-layer .lv{font-size:10.5px;font-weight:800;letter-spacing:.14em;color:var(--sx-a1)}
.pt-layer h3{font-size:19px;margin:9px 0 9px;letter-spacing:-.02em}
.pt-layer p{font-size:13px;color:var(--sx-mute);line-height:1.85;margin:0 0 16px;min-height:72px}
.pt-layer ul{margin:0 0 18px;padding-left:18px;font-size:12.5px;color:var(--sx-ink2);line-height:1.9}
.pt-layer .arw{position:absolute;right:-13px;top:50%;transform:translateY(-50%);z-index:2;
  width:26px;height:26px;border-radius:50%;background:var(--sx-card);border:1px solid var(--sx-line);
  display:flex;align-items:center;justify-content:center;color:var(--sx-a1);font-size:13px}

/* ---------- IA 图 ---------- */
.ia-box{background:var(--sx-card);border:1px solid var(--sx-line);border-radius:var(--sx-r);
  padding:18px;box-shadow:var(--sx-sh1)}
.ia-box svg{width:100%;height:auto;display:block}
.ia-box .n1{fill:var(--sx-soft);stroke:var(--sx-a1);stroke-width:1.5}
.ia-box .n2{fill:var(--sx-card);stroke:var(--sx-line2);stroke-width:1.4}
.ia-box .t{fill:var(--sx-ink);font-size:13px;font-weight:750}
.ia-box .s{fill:var(--sx-mute);font-size:10.5px}
.ia-box .lbl{fill:var(--sx-a1);font-size:10px;font-weight:800;letter-spacing:.1em}
.ia-box .ln{stroke:var(--sx-line2);stroke-width:1.4;fill:none}
.ia-box .cap{fill:var(--sx-mute);font-size:10.5px}

/* ---------- 来意分流 ---------- */
.pt-intents{display:grid;grid-template-columns:repeat(3,1fr);gap:13px}
.pt-intent{background:var(--sx-card);border:1px solid var(--sx-line);border-radius:15px;
  padding:18px 19px;box-shadow:var(--sx-sh1)}
.pt-intent b{display:block;font-size:14px;margin-bottom:6px}
.pt-intent p{font-size:12.5px;color:var(--sx-mute);margin:0 0 11px;line-height:1.8}
.pt-intent a{font-size:12.5px;font-weight:700}

/* ---------- 介绍页 ---------- */
.ov-hero{padding:48px 0 34px;background:radial-gradient(700px 300px at 82% 0%,rgba(47,107,255,.14),transparent 60%),
  var(--sx-bg2);border-bottom:1px solid var(--sx-line)}
.ov-hero h1{font-size:clamp(30px,4.2vw,46px);line-height:1.2;letter-spacing:-.035em;
  margin:14px 0 12px;font-weight:800}
.ov-hero p{font-size:15.5px;color:var(--sx-ink2);line-height:1.9;margin:0;max-width:760px}
.ov-hero .meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}
.ov-hero .meta span{font-size:11.8px;background:var(--sx-card);border:1px solid var(--sx-line);
  border-radius:999px;padding:5px 12px;color:var(--sx-ink2)}
.ov-layout{display:grid;grid-template-columns:212px 1fr;gap:44px;padding-top:38px}
.ov-toc{position:sticky;top:calc(var(--sx-h) + 22px);align-self:start}
.ov-toc .tt{font-size:10.5px;font-weight:800;letter-spacing:.13em;color:var(--sx-mute);margin-bottom:12px}
.ov-toc a{display:flex;gap:9px;align-items:baseline;padding:8px 10px;border-radius:9px;
  font-size:12.8px;color:var(--sx-mute);text-decoration:none;border-left:2px solid transparent}
.ov-toc a:hover{background:var(--sx-soft);color:var(--sx-a1);text-decoration:none}
.ov-toc a.on{background:var(--sx-soft);color:var(--sx-a1);font-weight:700;border-left-color:var(--sx-a1)}
.ov-toc a i{font-style:normal;font-size:10.5px;font-weight:800;color:var(--sx-a1)}
.ov-sec{padding:0 0 40px;margin-bottom:38px;border-bottom:1px solid var(--sx-line);
  scroll-margin-top:calc(var(--sx-h) + 24px)}
.ov-sec:last-of-type{border-bottom:0}
.ov-sec .nn{font-size:11.5px;font-weight:800;letter-spacing:.14em;color:var(--sx-a1)}
.ov-sec h2{font-size:27px;letter-spacing:-.028em;margin:8px 0 14px;font-weight:800}
.ov-sec p{font-size:14.3px;color:var(--sx-ink2);line-height:1.95;margin:0 0 14px}
.ov-sec p b{color:var(--sx-ink)}
.ov-box{background:var(--sx-card);border:1px solid var(--sx-line);border-radius:15px;
  padding:20px 22px;box-shadow:var(--sx-sh1);margin:14px 0}
.ov-grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0}
.ov-grid2{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:16px 0}
.ov-mini{background:var(--sx-card);border:1px solid var(--sx-line);border-radius:13px;padding:16px 17px}
.ov-mini .n{font-size:10.5px;font-weight:800;letter-spacing:.1em;color:var(--sx-a1)}
.ov-mini b{display:block;font-size:14.5px;margin:6px 0 6px}
.ov-mini p{font-size:12.4px;color:var(--sx-mute);line-height:1.8;margin:0}
.ov-tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:16px 0}
.ov-tile{background:var(--sx-card);border:1px solid var(--sx-line);border-radius:13px;
  padding:15px 10px;text-align:center}
.ov-tile b{display:block;font-size:25px;font-weight:800;letter-spacing:-.03em;
  background:var(--sx-grad);-webkit-background-clip:text;background-clip:text;
  color:transparent;-webkit-text-fill-color:transparent;line-height:1.25}
.ov-tile span{font-size:11.4px;color:var(--sx-mute)}
.ov-tbl{width:100%;border-collapse:collapse;font-size:13px;background:var(--sx-card);
  border:1px solid var(--sx-line);border-radius:13px;overflow:hidden;margin:14px 0}
.ov-tbl th,.ov-tbl td{border-bottom:1px solid var(--sx-line);padding:10px 12px;text-align:left;vertical-align:top}
.ov-tbl th{background:var(--sx-bg2);color:var(--sx-mute);font-size:11.4px;letter-spacing:.05em}
.ov-tbl td:first-child{font-weight:700;color:var(--sx-a1);white-space:nowrap}
.ov-bound{background:linear-gradient(135deg,rgba(154,101,8,.09),transparent 70%);
  border:1px solid rgba(154,101,8,.35);border-radius:14px;padding:18px 20px}
.ov-bound ul{margin:8px 0 0;padding-left:20px;font-size:13px;color:var(--sx-ink2);line-height:1.95}
.chips{display:flex;flex-wrap:wrap;gap:7px;margin:12px 0}
.chips span{font-size:12.2px;border:1px solid var(--sx-line);border-radius:999px;
  padding:5px 12px;background:var(--sx-card);color:var(--sx-ink2)}
.ov-pager{display:grid;grid-template-columns:1fr 1fr;gap:13px;margin:8px 0 20px}
.ov-pager a{display:block;background:var(--sx-card);border:1px solid var(--sx-line);
  border-radius:15px;padding:18px 20px;color:var(--sx-ink);box-shadow:var(--sx-sh1)}
.ov-pager a:hover{border-color:var(--sx-a1);text-decoration:none;transform:translateY(-2px)}
.ov-pager span{font-size:11px;color:var(--sx-mute);font-weight:700;letter-spacing:.08em}
.ov-pager b{display:block;font-size:16px;margin-top:6px}
.ov-pager a.next{text-align:right}
.ov-fig{background:var(--sx-card);border:1px solid var(--sx-line);border-radius:15px;
  padding:14px;box-shadow:var(--sx-sh1);margin:16px 0}
.ov-fig svg{width:100%;height:auto;display:block}
.ov-fig .b{fill:var(--sx-soft);stroke:var(--sx-a1);stroke-width:1.4}
.ov-fig .ba{fill:var(--sx-card);stroke:var(--sx-a1);stroke-width:1.8}
.ov-fig .t{fill:var(--sx-ink);font-size:13px;font-weight:700}
.ov-fig .s{fill:var(--sx-mute);font-size:10.5px}
.ov-fig .ln{stroke:var(--sx-line2);stroke-width:1.5;fill:none}
.ov-fig .ar{stroke:var(--sx-a1);stroke-width:1.6;fill:none}
.ov-fig .cap{fill:var(--sx-mute);font-size:11px}

/* ---------- 站点地图 ---------- */
.sm-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:16px 0}
.sm-card{background:var(--sx-card);border:1px solid var(--sx-line);border-radius:15px;
  padding:18px 20px;box-shadow:var(--sx-sh1)}
.sm-card h3{font-size:15px;margin:0 0 8px}
.sm-card p{font-size:12.6px;color:var(--sx-mute);line-height:1.85;margin:0 0 10px}
.sm-card .lv{font-size:10.2px;font-weight:800;letter-spacing:.1em;color:var(--sx-a1)}
.sm-card a{font-size:12.6px}

@media(max-width:1000px){
  .pt-grid{grid-template-columns:1fr;gap:30px}
  .pt-visual{max-width:560px}
  .pt-stats{grid-template-columns:repeat(3,1fr)}
  .pt-stats div:nth-child(3){border-right:0}
  .pt-stats div:nth-child(n+4){border-top:1px solid var(--sx-line)}
  .ov-layout{grid-template-columns:1fr;gap:14px}
  .ov-toc{position:sticky;top:var(--sx-h);z-index:20;background:var(--sx-bg);
    display:flex;gap:6px;overflow-x:auto;padding:10px 0;margin:0 -4px;
    border-bottom:1px solid var(--sx-line)}
  .ov-toc .tt{display:none}
  .ov-toc a{white-space:nowrap;border-left:0;border:1px solid var(--sx-line);
    border-radius:999px;padding:6px 12px;background:var(--sx-card)}
  .ov-toc a.on{border-color:var(--sx-a1)}
  .ov-tiles{grid-template-columns:repeat(2,1fr)}
  .ov-grid3,.sm-grid{grid-template-columns:1fr 1fr}
}
@media(max-width:700px){
  .pt-hero{padding:44px 0 40px}
  .pt-h1{font-size:34px}
  .pt-sub{font-size:14.5px}
  .pt-sec,.ov-sec-wrap,.sm-sec{padding-top:44px}
  .sx-cards,.pt-layers,.pt-intents,.ov-grid3,.ov-grid2,.sm-grid,.ov-pager{grid-template-columns:1fr}
  .pt-layer .arw{display:none}
  .pt-layer p{min-height:0}
  .pt-sec-head h2,.sm-sec h2{font-size:21px}
  .ov-sec h2{font-size:23px}
  .sx-card.wide{grid-column:auto}
  .ov-pager a.next{text-align:left}
}
@media(max-width:420px){.pt-stats{grid-template-columns:repeat(2,1fr)}
  .pt-stats div:nth-child(2n){border-right:0}
  .pt-stats div:nth-child(n+3){border-top:1px solid var(--sx-line)}
  .ov-tiles{grid-template-columns:repeat(2,1fr)}}
@media print{.pt-hero::before,.pt-visual::after{display:none}
  .sx-card,.pt-layer,.ov-box,.sm-card{box-shadow:none;page-break-inside:avoid}
  .pt-hero{background:#fff}.ov-toc{display:none}}
"""

TOC_JS = r"""
(function(){
var links=[].slice.call(document.querySelectorAll('.ov-toc a'));
if(!links.length)return;
var secs=links.map(function(a){return document.querySelector(a.getAttribute('href'));});
function upd(){
  var y=window.scrollY+140,idx=0;
  secs.forEach(function(s,i){if(s&&s.offsetTop<=y)idx=i;});
  links.forEach(function(a,i){a.classList.toggle('on',i===idx);});
}
upd();window.addEventListener('scroll',upd,{passive:true});
})();
"""

# ---------------------------------------------------------------- SVG 图示
# ---------------------------------------------------------------- v5.1 声明式图表
# 站点级三张图改由 chart_engine 编译：自动布局 + 字体测量 + 正交连线，
# 不再手写坐标；输出仍是零 JS / 零外链的静态 SVG，颜色走 --sx-* 主题变量。
import chart_engine as _chart_engine

JOURNEY_SVG = _chart_engine.build_journey()
IA_SVG = _chart_engine.build_ia()
CAPABILITY_SVG = _chart_engine.build_capability()




# ---------------------------------------------------------------- v5.0 扁平化首页组件
PORTAL_CSS = r"""
/* ================= v5.0 扁平化入口门户（f5- 前缀，只作用于首页） ================= */
html{scroll-behavior:smooth;scroll-padding-top:calc(var(--sx-h) + 56px)}
.f5{color:var(--sx-ink);font-family:"SF Pro Display",-apple-system,BlinkMacSystemFont,
  "PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  font-variant-numeric:tabular-nums;letter-spacing:0;display:block}
.f5 *,.f5 *::before,.f5 *::after{box-sizing:border-box}
.f5 a{color:inherit;text-decoration:none}
.f5 a:focus-visible,.f5 button:focus-visible{outline:2px solid var(--sx-a1);outline-offset:3px}
.f5 h1,.f5 h2,.f5 h3,.f5 p,.f5 ul{margin:0}
.f5 .sx-wrap{max-width:1180px}

/* 顶部阅读进度（扁平 2px 实色线） */
.f5-progress{position:fixed;top:0;left:0;right:0;height:2px;z-index:130;
  pointer-events:none;background:transparent}
.f5-progress i{display:block;height:100%;width:0;background:var(--sx-a1);
  transition:width .08s linear}
html[data-theme="dark"] .f5-progress{background:var(--sx-line)}

/* 吸顶分区导航 */
.f5-rail{position:sticky;top:var(--sx-h);z-index:100;background:var(--sx-card);
  border-bottom:1px solid var(--sx-line);display:flex;gap:0;overflow-x:auto;
  scrollbar-width:none;-ms-overflow-style:none}
.f5-rail::-webkit-scrollbar{display:none}
.f5-rail-in{display:flex;align-items:stretch;min-width:100%}
.f5-rail a{display:flex;align-items:center;gap:8px;padding:13px 18px;font-size:12.6px;
  font-weight:700;color:var(--sx-mute);white-space:nowrap;
  border-bottom:2px solid transparent;transition:color .16s,border-color .16s,background .16s}
.f5-rail a i{font-style:normal;font-size:10.5px;font-weight:800;letter-spacing:.08em;opacity:.65}
.f5-rail a:hover{color:var(--sx-a1);background:var(--sx-soft);text-decoration:none}
.f5-rail a.on{color:var(--sx-a1);border-bottom-color:var(--sx-a1)}
.f5-rail .rsp{flex:1}
.f5-rail .rl{display:flex;align-items:center;padding-right:4px;font-size:11.5px;
  color:var(--sx-mute);white-space:nowrap;font-weight:700;letter-spacing:.06em}

/* Hero：纯色块 + 细线，无渐变无阴影 */
.f5-hero{background:var(--sx-card);border-bottom:1px solid var(--sx-line)}
.f5-hero-in{display:grid;grid-template-columns:1.12fr .88fr;gap:56px;align-items:center;
  padding:78px 0 66px}
.f5-eyebrow{display:inline-flex;align-items:center;gap:9px;font-size:11px;font-weight:800;
  letter-spacing:.16em;color:var(--sx-a1);border:1px solid var(--sx-line2);
  padding:7px 13px;border-radius:2px;text-transform:uppercase}
.f5-eyebrow i{width:7px;height:7px;background:var(--sx-a1);display:block;border-radius:1px}
.f5-h1{font-size:clamp(40px,5.6vw,70px);line-height:1.08;letter-spacing:-.055em;
  font-weight:800;margin:24px 0 20px}
.f5-h1 em{font-style:normal;color:var(--sx-a1);border-bottom:5px solid var(--sx-soft)}
.f5-lede{font-size:16.5px;line-height:1.9;color:var(--sx-ink2);max-width:600px;margin-bottom:26px}
.f5-lede b{color:var(--sx-ink)}
.f5-cta{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:22px}
.f5-cta .sx-btn{border-radius:3px;box-shadow:none!important;font-weight:750;letter-spacing:-.01em;
  padding:12px 22px;transition:background .18s,border-color .18s,color .18s,transform .18s}
.f5-cta .sx-btn.pri{background:var(--sx-a1);color:#fff;border-color:var(--sx-a1)}
.f5-cta .sx-btn.pri:hover{background:var(--sx-ink);border-color:var(--sx-ink);transform:translateY(-2px)}
.f5-cta .sx-btn.gho{background:transparent;color:var(--sx-ink);border-color:var(--sx-line2)}
.f5-cta .sx-btn.gho:hover{border-color:var(--sx-a1);color:var(--sx-a1);transform:translateY(-2px)}
.f5-note{display:flex;flex-wrap:wrap;gap:8px 20px;font-size:12.2px;color:var(--sx-mute)}
.f5-note span{display:inline-flex;align-items:center;gap:7px}
.f5-note span::before{content:"";width:5px;height:5px;background:var(--sx-a1);display:block}
.f5-panel{background:var(--sx-bg2);border:1px solid var(--sx-line);padding:24px;
  border-top:4px solid var(--sx-a1)}
.f5-panel-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px}
.f5-panel-head b{font-size:13.5px;letter-spacing:-.01em}
.f5-panel-head span{font-size:10.2px;font-weight:800;letter-spacing:.14em;color:var(--sx-mute)}
.f5-panel svg{width:100%;height:auto;display:block}
.f5-panel-foot{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:16px}
.f5-panel-foot div{border-top:1px solid var(--sx-line2);padding-top:10px}
.f5-panel-foot b{display:block;font-size:21px;font-weight:800;letter-spacing:-.03em;color:var(--sx-a1)}
.f5-panel-foot span{font-size:10.8px;color:var(--sx-mute)}

/* 数据条：扁平表格化 */
.f5-stats{display:grid;grid-template-columns:repeat(6,1fr);border-left:1px solid var(--sx-line)}
.f5-stats div{border-right:1px solid var(--sx-line);border-bottom:1px solid var(--sx-line);
  padding:22px 16px;background:var(--sx-card)}
.f5-stats b{display:block;font-size:31px;font-weight:800;letter-spacing:-.04em;line-height:1.15;
  color:var(--sx-ink)}
.f5-stats b.hl{color:var(--sx-a1)}
.f5-stats span{font-size:11.8px;color:var(--sx-mute);font-weight:650}

/* 区块与标题 */
.f5-sec{padding:76px 0;border-bottom:1px solid var(--sx-line);
  scroll-margin-top:calc(var(--sx-h) + 54px)}
.f5-sec:last-of-type{border-bottom:0}
.f5-sec-head{display:grid;grid-template-columns:64px 1fr;gap:24px;align-items:start;margin-bottom:30px}
.f5-num{width:52px;height:52px;border:2px solid var(--sx-a1);color:var(--sx-a1);
  display:flex;align-items:center;justify-content:center;font-size:17px;font-weight:800}
.f5-sec h2{font-size:clamp(24px,3vw,33px);line-height:1.25;font-weight:800;
  letter-spacing:-.038em;margin:0 0 9px}
.f5-sec .lead{font-size:14px;line-height:1.85;color:var(--sx-mute);max-width:820px}
.f5-eyeline{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.f5-eyeline span{font-size:10.8px;font-weight:800;letter-spacing:.16em;color:var(--sx-a1);
  text-transform:uppercase}
.f5-eyeline i{display:block;width:26px;height:2px;background:var(--sx-a1)}

/* 卡片：纯色、1px 边、悬停只换边色与位移 */
.f5-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.f5-grid.two{grid-template-columns:repeat(2,1fr)}
.f5-card{display:flex;flex-direction:column;min-height:176px;background:var(--sx-card);
  border:1px solid var(--sx-line);padding:22px 22px 18px;position:relative;
  transition:transform .22s cubic-bezier(.2,.7,.2,1),border-color .2s,background .2s}
.f5-card::before{content:"";position:absolute;left:0;top:0;width:0;height:2px;
  background:var(--sx-a1);transition:width .24s ease}
.f5-card:hover{transform:translateY(-4px);border-color:var(--sx-a1);background:var(--sx-soft);
  text-decoration:none;color:var(--sx-ink)}
.f5-card:hover::before{width:100%}
.f5-card .k{font-size:10.6px;font-weight:800;letter-spacing:.14em;color:var(--sx-a1);
  text-transform:uppercase;margin-bottom:12px}
.f5-card h3{font-size:17px;font-weight:780;letter-spacing:-.022em;line-height:1.35;margin-bottom:9px}
.f5-card p{font-size:12.9px;line-height:1.85;color:var(--sx-mute);margin-bottom:16px}
.f5-card .go{margin-top:auto;display:flex;align-items:center;gap:8px;font-size:12.4px;
  font-weight:800;color:var(--sx-a1)}
.f5-card .go i{font-style:normal;transition:transform .2s ease}
.f5-card:hover .go i{transform:translateX(5px)}
.f5-card.feat{border-left:4px solid var(--sx-a1)}
.f5-card .tag{position:absolute;right:16px;top:18px;font-size:9.5px;font-weight:800;
  letter-spacing:.06em;color:#fff;background:var(--sx-a1);padding:3px 8px}
html[data-theme="dark"] .f5-card .tag{color:var(--sx-bg)}

/* 三层路径 */
.f5-layers{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.f5-layer{background:var(--sx-card);border:1px solid var(--sx-line);border-top:4px solid var(--sx-a1);
  padding:24px 22px;transition:border-color .2s,transform .2s}
.f5-layer:nth-child(2){border-top-color:var(--sx-a2)}
.f5-layer:hover{transform:translateY(-3px);border-color:var(--sx-a1)}
.f5-layer .lv{font-size:10.6px;font-weight:800;letter-spacing:.14em;color:var(--sx-a1)}
.f5-layer h3{font-size:19px;margin:10px 0 10px;letter-spacing:-.02em}
.f5-layer p{font-size:13px;color:var(--sx-mute);line-height:1.85;min-height:70px;margin-bottom:14px}
.f5-layer ul{list-style:none;padding:0;font-size:12.4px;color:var(--sx-ink2);line-height:2}
.f5-layer li::before{content:"—";color:var(--sx-a1);margin-right:8px;font-weight:800}

/* IA 图与来意分流 */
.f5-ia{background:var(--sx-card);border:1px solid var(--sx-line);padding:18px}
.f5-ia .n1{fill:var(--sx-soft);stroke:var(--sx-a1);stroke-width:1.5}
.f5-ia .n2{fill:var(--sx-card);stroke:var(--sx-line2);stroke-width:1.4}
.f5-ia .t{fill:var(--sx-ink);font-size:13px;font-weight:750}
.f5-ia .s{fill:var(--sx-mute);font-size:10.5px}
.f5-ia .lbl{fill:var(--sx-a1);font-size:10px;font-weight:800;letter-spacing:.1em}
.f5-ia .ln{stroke:var(--sx-line2);stroke-width:1.4;fill:none}
.f5-ia .cap{fill:var(--sx-mute);font-size:10.5px}
.f5-ia svg{width:100%;height:auto;display:block}
.f5-intents{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:16px}
.f5-intent{border:1px solid var(--sx-line);background:var(--sx-card);padding:18px 20px;
  transition:border-color .2s,background .2s}
.f5-intent:hover{border-color:var(--sx-a1);background:var(--sx-soft)}
.f5-intent b{display:block;font-size:14px;margin-bottom:7px}
.f5-intent p{font-size:12.6px;color:var(--sx-mute);line-height:1.8;margin-bottom:11px}
.f5-intent a{font-size:12.6px;font-weight:800;color:var(--sx-a1)}

/* 结尾行动区 */
.f5-end{background:var(--sx-bg2);border-top:1px solid var(--sx-line);
  border-bottom:1px solid var(--sx-line);padding:56px 0}
.f5-end-in{display:flex;align-items:center;justify-content:space-between;gap:28px;flex-wrap:wrap}
.f5-end h2{font-size:28px;font-weight:800;letter-spacing:-.035em;line-height:1.3}
.f5-end p{font-size:13.6px;color:var(--sx-mute);margin-top:8px;line-height:1.8}

/* 滚动进场 + 回到顶部 */
html.f5-ready .f5-reveal{opacity:0;transform:translateY(18px);
  transition:opacity .55s ease,transform .55s cubic-bezier(.2,.7,.2,1)}
html.f5-ready .f5-reveal.in{opacity:1;transform:none}
.f5-top{position:fixed;right:22px;bottom:22px;width:42px;height:42px;border:1px solid var(--sx-line2);
  background:var(--sx-card);color:var(--sx-a1);font-size:18px;font-weight:800;cursor:pointer;
  border-radius:3px;opacity:0;pointer-events:none;z-index:110;
  transition:opacity .2s,transform .2s,border-color .2s}
.f5-top.on{opacity:1;pointer-events:auto}
.f5-top:hover{border-color:var(--sx-a1);transform:translateY(-3px)}

@media(max-width:1000px){
  .f5-hero-in{grid-template-columns:1fr;gap:34px;padding:56px 0 50px}
  .f5-panel{max-width:620px}
  .f5-stats{grid-template-columns:repeat(3,1fr)}
  .f5-grid{grid-template-columns:repeat(2,1fr)}
  .f5-layers,.f5-intents{grid-template-columns:1fr 1fr}
}
@media(max-width:700px){
  .f5-hero-in{padding:42px 0 40px}
  .f5-h1{font-size:37px;letter-spacing:-.045em}
  .f5-lede{font-size:14.6px}
  .f5-sec{padding:52px 0}
  .f5-sec-head{grid-template-columns:1fr;gap:14px}
  .f5-num{width:44px;height:44px;font-size:14px}
  .f5-grid,.f5-grid.two,.f5-layers,.f5-intents{grid-template-columns:1fr}
  .f5-card{min-height:0}
  .f5-layer p{min-height:0}
  .f5-rail a{padding:11px 13px;font-size:12px}
  .f5-rail .rl{display:none}
  .f5-ia{padding:10px}
  .f5-end h2{font-size:23px}
}
@media(max-width:420px){.f5-stats{grid-template-columns:repeat(2,1fr)}}
@media(prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  html.f5-ready .f5-reveal{opacity:1;transform:none;transition:none}
  .f5-card:hover,.f5-layer:hover,.f5-top:hover,.f5-cta .sx-btn:hover{transform:none}
}
@media print{
  .f5-progress,.f5-rail,.f5-top{display:none!important}
  html.f5-ready .f5-reveal{opacity:1!important;transform:none!important}
  .f5-hero-in{padding:20px 0}
  .f5-card,.f5-layer,.f5-intent{break-inside:avoid;transform:none!important}
  .f5-sec{padding:24px 0}
}
"""

PORTAL_JS = r"""
(function(){
'use strict';
var root=document.documentElement;
var prog=document.getElementById('f5Prog');
var top=document.getElementById('f5Top');
var rail=[].slice.call(document.querySelectorAll('.f5-rail a[href^="#"]'));
var secs=rail.map(function(a){return document.querySelector(a.getAttribute('href'));});
var rev=[].slice.call(document.querySelectorAll('.f5-reveal'));
var reduced=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* 逐项错峰进场 */
rev.forEach(function(el,i){if(!reduced)el.style.transitionDelay=((i%4)*55)+'ms';});
if('IntersectionObserver' in window){
  var io=new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}
    });
  },{rootMargin:'0px 0px -6% 0px',threshold:.06});
  rev.forEach(function(el){io.observe(el);});
  var spy=new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(!e.isIntersecting)return;
      var id='#'+e.target.id;
      rail.forEach(function(a){a.classList.toggle('on',a.getAttribute('href')===id);});
    });
  },{rootMargin:'-28% 0px -62% 0px',threshold:0});
  secs.forEach(function(s){if(s)spy.observe(s);});
}else{
  rev.forEach(function(el){el.classList.add('in');});
}
/* 兜底：某些浏览器 / 无头渲染环境里 IntersectionObserver 虽存在却不派发回调，
   900ms 后把已在视口内的元素直接显示，避免首屏内容长期处于 opacity:0。
   视口外的元素仍保留滚动进场效果；减少动效与打印由 CSS 直接放行。 */
setTimeout(function(){
  var vh=window.innerHeight||800;
  rev.forEach(function(el){
    if(el.classList.contains('in'))return;
    var r=el.getBoundingClientRect();
    if(r.top<vh*0.94&&r.bottom>0)el.classList.add('in');
  });
},900);

/* 数字滚动（仅在进场时、且未开启减少动效）
   兜底：无头渲染 / 后台标签页 / 打印 / rAF 被节流时，动效可能永不推进，
   必须靠定时器写回最终数值，绝不能把首页数据条停在 0。 */
var counts=[].slice.call(document.querySelectorAll('[data-count]'));
function runCount(el){
  var final=el.getAttribute('data-count');
  var target=parseInt(final,10);
  if(isNaN(target)||reduced){el.textContent=final;return;}
  if(el.getAttribute('data-counted'))return;
  el.setAttribute('data-counted','1');
  var t0=null,dur=900,done=false;
  function step(ts){
    if(done)return;
    if(t0===null)t0=ts;
    var p=Math.min(1,(ts-t0)/dur),ease=1-Math.pow(1-p,3);
    el.textContent=String(Math.round(target*ease));
    if(p<1){requestAnimationFrame(step);}else{done=true;el.textContent=final;}
  }
  requestAnimationFrame(step);
  setTimeout(function(){done=true;el.textContent=final;},1300);
}
if('IntersectionObserver' in window&&counts.length){
  var co=new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(e.isIntersecting){runCount(e.target);co.unobserve(e.target);}
    });
  },{threshold:.4});
  counts.forEach(function(el){co.observe(el);});
}else{counts.forEach(runCount);}

/* 阅读进度 + 回到顶部 + 吸顶栏状态 */
function tick(){
  var h=document.documentElement.scrollHeight-window.innerHeight;
  var p=h>0?Math.min(100,Math.max(0,window.scrollY/h*100)):0;
  if(prog)prog.style.width=p.toFixed(2)+'%';
  if(top)top.classList.toggle('on',window.scrollY>480);
  var bar=document.querySelector('.sx-bar');
  if(bar)bar.classList.toggle('on',window.scrollY>12);
}
tick();window.addEventListener('scroll',tick,{passive:true});
window.addEventListener('resize',tick,{passive:true});
if(top)top.addEventListener('click',function(){
  window.scrollTo({top:0,behavior:reduced?'auto':'smooth'});
});

/* 分区导航：点击后主动高亮，兼容平滑滚动 */
rail.forEach(function(a){
  a.addEventListener('click',function(){
    rail.forEach(function(x){x.classList.remove('on');});
    a.classList.add('on');
  });
});
})();
"""

def _crumbs(*items):
    return [(label, href) for label, href in items]


# ---------------------------------------------------------------- 入口门户
def portal_doc(img_n=265, q_total=208, terms=291, figs=8, must=38, rows=40,
               ask_n=485, domains=14, cats=11):
    """v5.0 扁平化入口门户：纯色块 / 清晰字体层级 / 滚动进场 / 吸顶分区导航。"""
    crumbs = _crumbs(("门户", None))
    H = []
    H.append('<script>document.documentElement.classList.add("f5-ready")</script>')
    H.append('<div class="f5-progress" aria-hidden="true"><i id="f5Prog"></i></div>')

    def card(href, kicker, title, desc, go='打开 →', feat=False, tag=None):
        cls = 'f5-card f5-reveal' + (' feat' if feat else '')
        mk = '<span class="tag">%s</span>' % tag if tag else ''
        return (f'<a class="{cls}" href="{href}">{mk}'
                f'<span class="k">{kicker}</span><h3>{title}</h3><p>{desc}</p>'
                f'<span class="go">{go} <i>→</i></span></a>')

    def sec(num, sid, eyebrow, title, lead, inner):
        return (f'<section class="f5-sec" id="{sid}"><div class="sx-wrap">'
                f'<div class="f5-sec-head f5-reveal"><div class="f5-num">{num}</div><div>'
                f'<div class="f5-eyeline"><span>{eyebrow}</span><i></i></div>'
                f'<h2>{title}</h2><p class="lead">{lead}</p></div></div>'
                f'{inner}</div></section>')

    # ---------------------------------------------------------------- Hero
    H.append('<main class="f5" id="f5top">')
    H.append('<section class="f5-hero" id="pt-start"><div class="sx-wrap f5-hero-in"><div>'
             '<div class="f5-eyebrow"><i></i>ENTERPRISE AGENT DELIVERY · ' + sc.VERSION + ' · OFFLINE FIRST</div>'
             '<h1 class="f5-h1">把智能体交付<br>做成一门<em>可验收的工程</em></h1>'
             '<p class="f5-lede">面向全行业、厂商中立的 <b>前沿部署工程师（FDE）</b> 能力体系与实施标准。'
             '从判断场景值不值得做，到用评测集证明效果、用权限与审计管住风险，'
             '把「能用」做成「可验收、可上线、可治理」。</p>'
             '<div class="f5-cta">'
             '<a class="sx-btn pri" href="01_主手册.html#anchor-learning-path">开始门店实训 →</a>'
             '<a class="sx-btn gho" href="制造业学习指南.html">制造业三级学习指南</a>'
             '<a class="sx-btn gho" href="FDE工程师考核题库.html">解锁自测题库</a>'
             '</div>'
             '<div class="f5-note"><span>手册公开 · 题库凭码</span>'
             '<span>手机 / 电脑双端</span><span>无需安装与账号</span>'
             '<span>可直接静态托管上线</span>'
             + (f'<span>{ask_n} 个可追问学习点</span>') +
             '</div></div><div class="f5-panel f5-reveal"><div class="f5-panel-head">'
             '<b>能力旅程 · 从判断到治理</b><span>LEARNING JOURNEY</span></div>'
             + JOURNEY_SVG +
             '<div class="f5-panel-foot"><div><b>14</b><span>步学习路径</span></div>'
             '<div><b>4</b><span>个阶段</span></div>'
             '<div><b>15+</b><span>份交付物</span></div></div>'
             '</div></div></section>')

    # ---------------------------------------------------------------- 数据条
    stats = [("19", "个知识单元", False), ("14", "步学习路径", False),
             (str(q_total), "道考核题 · 两类选择题", True),
             (str(terms), "条可点术语", False), (str(figs), "张离线图示", False),
             (str(must), "项必背速达", False)]
    H.append('<div class="sx-wrap"><div class="f5-stats">' + ''.join(
        f'<div class="f5-reveal"><b class="{"hl" if hl else ""}" '
        f'data-count="{v}">{v}</b><span>{lab}</span></div>'
        for v, lab, hl in stats) + '</div></div>')

    # ---------------------------------------------------------------- 吸顶分区导航
    rails = [("#pt-path", "01", "从哪开始"), ("#pt-map", "02", "导航分布"),
             ("#pt-learn", "03", "按路径学习"), ("#pt-tools", "04", "查阅与考核"),
             ("#pt-tech", "05", "技术补强"), ("#pt-res", "06", "资料与上线")]
    H.append('<nav class="f5-rail" aria-label="首页分区导航"><div class="sx-wrap f5-rail-in">'
             + ''.join(f'<a class="{"on" if i == 0 else ""}" href="{href}"><i>{n}</i>{label}</a>'
                       for i, (href, n, label) in enumerate(rails))
             + '<span class="rsp"></span><span class="rl">扁平化设计 · 滚动可用</span>'
             '</div></nav>')

    # ---------------------------------------------------------------- 01 从哪开始
    layers = [
        ("L0 · 入口", "这是什么、值不值得读",
         "本页。一分钟看清定位、规模、来意分流与全站导航分布。",
         ["品牌与价值主张", "核心数据一览", "六种来意的分流入口"]),
        ("L1 · 介绍", "体系长什么样",
         "手册介绍页。讲清三项核心能力、十四篇结构、学习节奏、适用行业与明确边界。",
         ["能力体系与五阶段图", "十四篇正文 + 附录 A–F", "跨行业与角色路径"]),
        ("L2 · 详细", "逐章学、随时查、可考核",
         "三册正文与工具：主手册、速查、开源课程精读，加术语词典、题库、笔记与核验报告。",
         [f"{rows} 行科学化最终目录", f"{q_total} 题打乱复习", f"{must} 项必背速达 · 逐点追问"]),
    ]
    H.append(sec("01", "pt-path", "START HERE", "三层阅读路径：先看懂，再深入，再动手",
                  "不要一上来就翻正文。门户 → 介绍 → 详细，每层只解决一个问题；每页都有面包屑、主导航与返回路径。",
                  '<div class="f5-layers">' + ''.join(
                      f'<div class="f5-layer f5-reveal"><div class="lv">{lv}</div><h3>{h}</h3>'
                      f'<p>{p}</p><ul>' + ''.join(f'<li>{x}</li>' for x in li) + '</ul></div>'
                      for lv, h, p, li in layers) + '</div>'))

    # ---------------------------------------------------------------- 02 导航分布
    intents = [
        ("第一次来", "下载门店政策，搭建第一版助手，再用十条验收用例检查结果。", "01_主手册.html#anchor-learning-path", "进入门店实训 →"),
        ("要考核 / 复习", "凭码进入题库组卷，勾选打乱题序与选项，先做 20 题看薄弱能力域。", "FDE工程师考核题库.html", "📝 开始组卷 →"),
        ("要讲给别人听", "用介绍页的一页式结构，配合白板七层图与三种时长话术。", "01_主手册.html#anchor-explain", "🗣 看对外讲解 →"),
    ]
    H.append(sec("02", "pt-map", "INFORMATION ARCHITECTURE", "科学的导航分布",
                  f"L0 门户 → L1 介绍 → L2 四个详细板块；「开源课程精读」是独立第三册，「细节追问」是横切能力。"
                  f"全站统一主导航 + 面包屑 + 页脚站点地图，跨页全部相对路径，离线与线上托管一致。",
                  '<div class="f5-ia f5-reveal">' + IA_SVG + '</div>'
                  '<div class="f5-intents">' + ''.join(
                      f'<div class="f5-intent f5-reveal"><b>{b}</b><p>{p}</p><a href="{h}">{a}</a></div>'
                      for b, p, h, a in intents) + '</div>'))

    # ---------------------------------------------------------------- 03 按路径学习
    learn = [
        card('01_主手册.html#anchor-learning-path', 'STEP 1 → 14', '分步学习路径（14 步）',
             '判断力 → 动手力 → 证明力 → 治理与表达；每步有产出物与完成判据，附速成 / 标准 / 完整三种节奏。', '从第一步开始 →', feat=True),
        card('01_主手册.html#anchor-catalog', 'FINAL CATALOG', f'科学化最终目录总表（{rows} 行）',
             'L0–L5 认知分层、章节依赖链、角色路径、图示索引与一页速用；复习顺序照这张表排。', '排复习顺序 →'),
        card('03_开源课程解读.html', 'NEW · 第三册', '开源课程精读模块',
             '把 fde4.ai/book/ 开源版 13 章逐章消化：7 篇精读、18 张方法论卡片、与 4 章 19 单元及 CS329Z 的双向映射。', '打开第三册 →', feat=True, tag='v5.0'),
        card('02_速查手册.html', 'A–Q · 17 组', '重点速查手册',
             f'名词、易混淆、硬约束、诊断树、FAQ、踩坑、模板、现场命令、指标公式、对外表达、选型、考核与 O/P/Q 技术补强；含 {must} 项必背速达。', '打开阅读 →'),
        card('参考资料/逐节笔记索引.html', '19 LESSONS', '19 节逐节笔记',
             f'课程逐节笔记离线副本，HTML 与 Markdown 双份、{img_n} 张本地截图，用于逐节核验知识点是否遗漏。', '打开索引 →'),
        card('01_主手册.html#anchor-coverage', 'COVERAGE', '19 节覆盖对照与核验',
             '附录 A / C：逐节确认 19 单元、7 项权重、三项核心能力与平台细节命中；附四轮查漏记录。', '看覆盖对照 →'),
    ]
    H.append(sec("03", "pt-learn", "LEARNING", "按路径学习：三册正文，一步一验收",
                  "主手册讲方法、速查手册讲口径、第三册用开源课程补商业交付视角；三者互相引用，不必按顺序通读。",
                  '<div class="f5-grid">' + ''.join(learn) + '</div>'))

    # ---------------------------------------------------------------- 04 查阅与考核
    tools = [
        card('术语词典.html', 'GLOSSARY', f'术语词典 · {terms} 条 / {cats} 类',
             '专业名词 / 英文 / 缩写逐条给全称、分类、定义、交付意义与相关词条；三册正文中的虚线词可直接点击弹窗。', '打开词典 →'),
        card('FDE工程师考核题库.html', 'ASSESSMENT', f'FDE 考核题库 · {q_total} 题',
             f'v5.0 起全部为选择题：单选 + 多选两类、{domains} 个能力域、3 个难度层级；'
             '题序与选项打乱、题型混排、错题优先、练习 / 考试 / 错题三种模式、成绩单与打印答案页。',
             '开始组卷 →', feat=True, tag='全选择题'),
        card('细节追问提示词库.html', 'ASK ANY AI', f'细节追问 · {ask_n} 个学习点 × 5 角度',
             '三册每个标题、19 节笔记都能点「🔍 细节追问」：一段自带资料版本、章节位置、认知层、能力域、关键概念与核心问题的提示词，复制到任意 AI 继续深挖。', '打开提示词库 →'),
        card('01_主手册.html#anchor-examtypes', '10.5', '两类选择题与判分口径',
             '单选唯一正确项；多选全部选对才得分（漏选与错选同等不得分）。附打乱复习法、三种模式与间隔节奏。', '看题型设计 →'),
        card('01_主手册.html#anchor-figures', f'{figs} FIGURES', f'项目图示索引（{figs} 张）',
             '三个实战项目的演进 / 架构 / 合规闸门 / 知识集成，加选型四象限、学习路径、白板七层与认知分层，全部内联 SVG 可打印。', '看图示索引 →'),
        card('01_主手册.html#anchor-explain', 'EXPLAIN', '对外讲解与答辩',
             '一句话定义、三种时长讲法、四类听众话术、术语翻译、白板七层与质疑应答；能把这套方法讲给别人听。', '学会讲清楚 →'),
    ]
    H.append(sec("04", "pt-tools", "LOOKUP & EXAM", "查词、看图、讲清楚、接着问、被提问",
                "复习不是重读，是被提问：先做题，再按薄弱能力域回正文补；想深挖某个学习点，直接把该模块带去问 AI。",
                '<div class="f5-grid">' + ''.join(tools) + '</div>'))

    # ---------------------------------------------------------------- 05 技术补强
    tech = [
        card('01_主手册.html#anchor-model', '第十一篇', '模型类知识与技术选型',
             '三条轴、五维选型矩阵、四笔成本账、推理框架与部署形态、八步选型流程、常见误区；速查 O 组配套。', '看选型矩阵 →'),
        card('01_主手册.html#anchor-agent', '第十二篇 · CS329Z', 'Agent 搭建与测试能力',
             '对照斯坦福公开 CS329Z：从零搭 Agent 八步、评测流水线、优化决策树、与课程作业节奏对齐的自训计划。', '看八步与流水线 →'),
        card('01_主手册.html#anchor-tts', '第十三条', '语音与 TTS 选型方案',
             '全链路拆解、方案谱系、选型决策树、评测指标与验收口径、延迟优化五招、集成降级与合规签字清单；速查 P 组配套。', '看语音链路 →'),
        card('01_主手册.html#anchor-cases', '第十四篇', '跨行业真实案例集',
             '制造 / 金融 / 医疗 / 政务 / 零售 / 能源 / 教育 / 物流 / 法律 / 汽车 / 研发效能 / 媒体共 12 类行业的真实约束、迁移要点与横向对照。', '看行业对照 →'),
        card('01_主手册.html#anchor-selection', '第九篇', '国内方案选型与部署实施',
             '四输入变量、六层能力映射、四类技术选择、四个部署方案包、许可与合规核对、评审 12 问；公开资料举例，非推荐。', '看方案包 →'),
        card('01_主手册.html#anchor-reading', '第十篇', '扩展阅读与还缺什么',
             '诚实回答「还缺什么」：覆盖自评、10 类缺口与补齐方式、六条主题线、资料并入四步法与六项不承诺。', '看缺口清单 →'),
    ]
    H.append(sec("05", "pt-tech", "TECHNICAL DEPTH", "v5.0 技术补强：模型、Agent、语音与行业",
                 "把方法讲到能评审：模型怎么选、Agent 怎么搭与怎么测、语音链路怎么定验收、不同行业的真实约束分别是什么。",
                 '<div class="f5-grid">' + ''.join(tech) + '</div>'))

    # ---------------------------------------------------------------- 06 资料与上线
    res = [
        card('离线使用说明.md', 'OFFLINE', '离线使用说明',
             '手机 / 电脑打开方式、三层导航与速达、题库与错题本、第三册与原文副本、目录结构、静态托管部署与离线自包含技术说明。', '查看说明 →'),
        card('核验报告.md', 'VERIFY', '全面核验报告',
             '覆盖度、术语交互、SVG 图示、选型边界、科学化目录、考核题库、门户与介绍页、全站导航、品牌中立、离线与双端适配的自动复检结论。', '查看报告 →'),
        card('站点地图.html', 'SITEMAP', '站点地图与导航规则',
             '三层信息架构图、全部页面清单、每层导航约定与相对路径规则、上线部署前核对项。', '看导航分布 →'),
        card('01_主手册.html#anchor-checklist', 'GO-LIVE', '上线检查单与验收签字',
             'D.5 上线检查单、指标口径、评测基线、回滚演练、权限矩阵与审计留痕；能签字才算完成。', '看检查单 →'),
    ]
    H.append(sec("06", "pt-res", "RESOURCES", "资料、核验与部署上线",
                 "本目录就是一个完整静态站点：入口设为 index.html，保持子目录相对位置即可上线；本地 file:// 与线上表现一致。",
                 '<div class="f5-grid two">' + ''.join(res) + '</div>'))

    # ---------------------------------------------------------------- 结尾
    H.append('<section class="f5-end"><div class="sx-wrap f5-end-in f5-reveal"><div>'
             '<h2>现在就开始：先读懂，再动手，最后被提问。</h2>'
             f'<p>十四篇正文 · 三册阅读版 · 17 组速查 · {q_total} 道选择题 · {terms} 条可点术语 · 题库在线解锁。</p></div>'
             '<div class="f5-cta" style="margin:0"><a class="sx-btn pri" href="手册展示页.html">先看介绍 →</a>'
             '<a class="sx-btn gho" href="01_主手册.html#anchor-learning-path">从第一步开始</a></div>'
             '</div></section>')
    H.append('</main><button class="f5-top" id="f5Top" type="button" title="回到顶部" aria-label="回到顶部">↑</button>')

    title = '企业级智能体交付实战手册 · FDE 能力体系与实施标准'
    desc = (f'面向全行业、厂商中立的企业级智能体交付 / 前沿部署工程师（FDE）能力体系与实施标准。'
            f'十四篇正文 + 第三册开源课程精读、19 个知识单元、14 步学习路径、{q_total} 道选择题、'
            f'{terms} 条可点击术语、{figs} 张内联 SVG 图示、{ask_n} 个可追问学习点，手册公开阅读，题库凭码解锁。')
    return sc.page_shell(title, desc, 'home', crumbs, ''.join(H),
                         extra_css=PAGE_CSS + PORTAL_CSS, extra_js=PORTAL_JS)

def intro_doc(q_total=208, terms=291, must=38, rows=40, ask_n=485, domains=14, cats=11):
    crumbs = _crumbs(("门户", "index.html"), ("介绍", None))
    secs = [
        ("01", "定位", "这套手册是什么"),
        ("02", "能力", "三项核心能力与五阶段交付"),
        ("03", "结构", "十四篇正文、第三册与附录 A–F"),
        ("04", "规模", "一眼看懂规模"),
        ("05", "特色", "七个产品特色"),
        ("06", "节奏", "14 步四阶段与间隔复习"),
        ("07", "适用", "跨行业适用与五类角色"),
        ("08", "边界", "边界声明"),
        ("09", "下一步", "从这里进入"),
    ]
    toc = ''.join('<a href="#ov-%s"><i>%s</i>%s</a>' % (n, n, name)
                  for n, name, _ in secs)

    H = []
    H.append('<main class="ov-main"><section class="ov-hero" id="anchor-showcase"><div class="sx-wrap">'
             '<div class="pt-kicker"><i></i>L1 · INTRODUCTION · %s</div>'
             '<h1>企业级智能体交付实战手册<br><span class="pt-grad">FDE 能力体系与实施标准</span></h1>'
             '<p>一页看清：这套手册讲什么、怎么学、怎么查、怎么考、怎么讲给别人听，'
             '以及它<b>明确不承诺什么</b>。适用于所有需要把智能体接入真实业务流程的行业，'
             '不绑定任何厂商、不绑定任何行业。</p>'
             '<div class="meta"><span>跨行业通用 / 厂商中立</span><span>十四篇 + 第三册 + 附录 A–F</span>'
             '<span>%d 道考核题</span><span>%d 项必背速达</span><span>零外部资源</span></div>'
             '</div></section>' % (sc.VERSION, q_total, must))

    H.append('<div class="sx-wrap"><div class="ov-layout">'
             '<nav class="ov-toc" aria-label="本页章节目录"><div class="tt">本页章节</div>'
             + toc + '</nav><div class="ov-body">')

    # 01 定位
    H.append('<section class="ov-sec" id="ov-01"><div class="nn">01 / POSITIONING</div>'
             '<h2>这套手册是什么</h2>'
             '<div class="ov-box"><p style="margin:0;font-size:15.5px">'
             '<b>一句话定义：</b>前沿部署工程师（FDE）是把企业级智能体从「能用」做到'
             '「可验收、可上线、可治理」的人：先判断场景值不值得做，再选构建模式把知识和流程接进来，'
             '然后用评测集证明效果，最后用权限、审计与运维把风险管住。</p></div>'
             '<p>这套手册把上述能力拆成 <b>可学、可练、可查、可考、可讲</b> 五件事，'
             '并按「门户 → 介绍 → 详细」三层组织：本页是 L1，往下是 L2 的正文与工具，'
             '往上是 L0 的入口门户。每一层都有统一的主导航、面包屑与站点地图入口。</p>'
             '<div class="ov-grid3">'
             '<div class="ov-mini"><div class="n">CAPABILITY 01</div><b>场景理解与方案设计</b>'
             '<p>需求收敛 7 维度、场景评分卡、能做 / 难做 / 不能做、方案画布、一句话可验收需求、停止条件。</p></div>'
             '<div class="ov-mini"><div class="n">CAPABILITY 02</div><b>交付实施与评测运维</b>'
             '<p>五阶段交付、五种构建模式、评测集与 Badcase 归因、灰度与回滚、监控告警、成本与容量。</p></div>'
             '<div class="ov-mini"><div class="n">CAPABILITY 03</div><b>安全合规与责任 AI</b>'
             '<p>数据分级、RBAC 与最小权限、提示注入与越权检索、L1/L2/L3 操作分级、审计留痕与红队测试。</p></div>'
             '</div></section>')

    # 02 能力
    H.append('<section class="ov-sec" id="ov-02"><div class="nn">02 / CAPABILITY MODEL</div>'
             '<h2>三项核心能力与五阶段交付</h2>'
             '<p>能力骨架参照公开的 FDE 知识域，已抽象为跨行业通用模型；'
             '五阶段每一阶段都绑定可展示、可验收的产出物，没有产出物就不算完成。</p>'
             '<div class="ov-fig">' + CAPABILITY_SVG +
             '<div class="pt-vhead" style="margin:6px 0 0"><span style="font-size:11px;color:var(--sx-mute)">'
             '图｜三项核心能力 → 五阶段交付 → 逐阶段产出物（教学归纳，非厂商方案）</span></div>'
             '</div></section>')

    # 03 结构
    H.append('<section class="ov-sec" id="ov-03"><div class="nn">03 / STRUCTURE</div>'
             '<h2>十四篇正文、第三册与附录 A–F</h2>'
             '<p>从概念地图到企业级治理，按认知层递进；第十一～十四篇补模型选型、Agent 工程与测试、语音 TTS 与跨行业案例，第三册用开源课程补商业交付视角；附录负责核验、复用与复习排序。</p>'
             '<table class="ov-tbl"><thead><tr><th>位置</th><th>讲什么</th><th>解决什么来意</th></tr></thead><tbody>'
             '<tr><td>第零篇 · 使用说明</td><td>14 步分步学习路径、环境准备、适用范围与跨行业映射</td><td>第一次学，照着做</td></tr>'
             '<tr><td>第一篇 · AI 与 Agent 基础</td><td>AI / LLM / Transformer / RAG / Agent 与编排的概念地图</td><td>把名词和边界弄清楚</td></tr>'
             '<tr><td>第二篇 · 平台能力地图</td><td>构建模式 × 核心能力组件 × 模型；知识库、工作流、Multi-Agent</td><td>知道平台能做什么、不能做什么</td></tr>'
             '<tr><td>第三篇 · 五种模式实战</td><td>三个全新演练项目：门店运营、信贷合规问答、设备维修追溯</td><td>完整跑一遍配置与演示</td></tr>'
             '<tr><td>第四篇 · 评测与调优</td><td>评测集、Badcase 归因、Prompt / RAG / 工作流 / Multi-Agent 调优</td><td>把「效果不好」变成可定位的问题</td></tr>'
             '<tr><td>第五篇 · 企业级交付标准</td><td>五阶段、15+ 交付物、验收指标、安全合规与责任 AI</td><td>能签字、能上线</td></tr>'
             '<tr><td>第六篇 · 能力自评与备考</td><td>能力雷达、权重对照、自评表与复习节奏</td><td>知道自己还差什么</td></tr>'
             '<tr><td>第七篇 · 完全版补遗</td><td>工程基底、数据治理、部署运维、项目管理、行业纵深等 12 个专题</td><td>补齐课程之外的企业级细节</td></tr>'
             '<tr><td>第八篇 · 对外表达与讲解</td><td>一句话定义、三种时长讲法、四类听众话术、白板七层</td><td>能跟别人讲明白</td></tr>'
             '<tr><td>第九篇 · 国内技术选型</td><td>四输入变量、六层能力映射、四个部署方案包、评审 12 问</td><td>能解释技术选择与部署方案</td></tr>'
             '<tr><td>第十篇 · 扩展阅读与缺口</td><td>覆盖自评、10 类诚实缺口、六条主题线、考核题型与间隔复习</td><td>知道边界在哪、下一步往哪走</td></tr>'
             '<tr><td>第十一篇 · 模型与技术选型</td><td>三条轴、五维矩阵、四笔成本账、推理框架、八步选型流程</td><td>能解释为什么选这个模型</td></tr>'
             '<tr><td>第十二篇 · Agent 搭建与测试</td><td>对照 CS329Z：八步搭建、评测流水线、优化决策树、自训计划</td><td>能把评测接进 CI</td></tr>'
             '<tr><td>第十三篇 · 语音与 TTS 选型</td><td>全链路、方案谱系、决策树、指标口径、延迟优化与合规清单</td><td>能定语音链路验收线</td></tr>'
             '<tr><td>第十四篇 · 跨行业真实案例</td><td>12 类行业的真实约束、迁移要点与横向对照</td><td>能把案例迁移到本行业</td></tr>'
             '<tr><td>第三册 · 开源课程精读</td><td>开源版 13 章逐章解读、18 张方法卡、双向映射与版权边界</td><td>补齐商业交付与采纳视角</td></tr>'
             '<tr><td>附录 A–F</td><td>19 节覆盖对照、易混淆与模板集、版本改造记录、公开出处、%d 行最终目录总表</td><td>核验、复用与排复习顺序</td></tr>'
             '</tbody></table></section>' % rows)

    # 04 规模
    tiles = [('19', '个知识单元'), ('7', '项能力权重'), ('3', '个全新演练项目'),
             ('14', '步学习路径'), ('%d' % terms, '条可点术语'), ('8', '张内联 SVG'),
             ('%d' % q_total, '道考核题'), ('%d' % must, '项必背速达'),
             ('%d' % rows, '行最终目录'), ('19', '节逐节笔记'), ('265', '张本地截图'),
             ('%d' % ask_n, '个可追问模块'), ('5', '个追问角度'), ('4', '个部署方案包'),
             ('2', '类选择题'), ('%d' % domains, '个能力域'),
             ('%d' % cats, '个术语分类'), ('3', '册阅读版')]
    H.append('<section class="ov-sec" id="ov-04"><div class="nn">04 / BY THE NUMBERS</div>'
             '<h2>一眼看懂规模</h2>'
             '<div class="ov-tiles">' + ''.join(
                 '<div class="ov-tile"><b>%s</b><span>%s</span></div>' % (a, b) for a, b in tiles) +
             '</div></section>')

    # 05 特色
    H.append('<section class="ov-sec" id="ov-05"><div class="nn">05 / WHAT MAKES IT DIFFERENT</div>'
             '<h2>七个产品特色</h2><div class="ov-grid3">'
             '<div class="ov-mini"><div class="n">01</div><b>公开阅读</b><p>阅读材料可在本地构建；在线自测需要输入网站体验码。</p></div>'
             '<div class="ov-mini"><div class="n">02</div><b>手机 + 电脑双端</b><p>电脑侧边栏、手机抽屉目录、目录过滤、阅读进度、深浅主题、字号调节、打印 / PDF。</p></div>'
             '<div class="ov-mini"><div class="n">03</div><b>术语点击即查</b><p>专业名词 / 英文 / 缩写带虚线标记，点击弹出全称、定义、交付意义与相关词条；独立词典页可分类检索。</p></div>'
             '<div class="ov-mini"><div class="n">04</div><b>图示可打印</b><p>8 张内联 SVG 随主题变色，把架构、闸门、集成、选型、路径、认知分层画清楚。</p></div>'
             '<div class="ov-mini"><div class="n">05</div><b>可考核、可打乱</b><p>%d 道题 / 两类选择题 / %d 个能力域；题序与选项乱序、题型混排、错题本、三种复习模式、成绩单与薄弱能力域。</p></div>'
             '<div class="ov-mini"><div class="n">06</div><b>边界诚实</b><p>第十篇如实列出 10 类缺口与六项不承诺；不编造性能数字、价格、合规资质与真实客户成效。</p></div>'
             '<div class="ov-mini"><div class="n">07</div><b>每个学习点可追问</b><p>三册每个标题与 19 节笔记都能点「🔍 细节追问」，生成 %d 个模块 × 5 个角度的自带上下文提示词；复制后粘贴到任意 AI，不会丢掉「我在学哪一节」。提示词要求 AI 区分手册已写明 / 推断 / 需查当期文档，并禁止编造成效数字。</p></div>'
             '</div></section>' % (q_total, domains, ask_n))

    # 06 节奏
    H.append('<section class="ov-sec" id="ov-06"><div class="nn">06 / LEARNING RHYTHM</div>'
             '<h2>14 步四阶段与间隔复习</h2><div class="ov-grid2">'
             '<div class="ov-mini"><div class="n">STAGE 01 · STEP 1–3</div><b>判断力</b><p>概念地图、场景判断、需求收敛；产出场景判断卡与方案画布。</p></div>'
             '<div class="ov-mini"><div class="n">STAGE 02 · STEP 4–7</div><b>动手力</b><p>五种构建模式、知识工程、工作流与工具；产出配置表与变量表。</p></div>'
             '<div class="ov-mini"><div class="n">STAGE 03 · STEP 8–12</div><b>证明力</b><p>评测集、调优、安全合规、灰度上线；产出评测报告与验收基线。</p></div>'
             '<div class="ov-mini"><div class="n">STAGE 04 · STEP 13–14</div><b>治理与表达</b><p>技术选型、对外讲解、复盘与扩展阅读；产出选型说明与复习计划。</p></div>'
             '</div><table class="ov-tbl"><thead><tr><th>时间点</th><th>做什么</th><th>题库动作</th></tr></thead><tbody>'
             '<tr><td>学完当天</td><td>只看产出物清单与最终目录，逐项打勾</td><td>练习模式 · 全库随机 10 题</td></tr>'
             '<tr><td>第 2 天</td><td>闭卷复述一句话定义、五阶段、四环节、八段、白板七层</td><td>单选题专项 · 术语与硬约束</td></tr>'
             '<tr><td>第 7 天</td><td>重做 Badcase 归因与方案画布</td><td>考试模式 · 随机 20 题，记薄弱能力域</td></tr>'
             '<tr><td>第 30 天</td><td>重跑评测集回归，核对当期文档</td><td>错题模式 + 多选题专项</td></tr>'
             '<tr><td>每季度</td><td>复核许可 / 版本 / 价格 / 资质与成本模型</td><td>考试模式 · 模型 / Agent / TTS 能力域专项</td></tr>'
             '<tr><td>每次立项</td><td>重做四输入变量表与评审 12 问</td><td>多选题 · 模型与 TTS 选型两组</td></tr>'
             '</tbody></table></section>')

    # 07 适用
    H.append('<section class="ov-sec" id="ov-07"><div class="nn">07 / APPLICABILITY</div>'
             '<h2>跨行业适用与五类角色</h2>'
             '<p><b>决定成败的是约束类型，不是行业名称。</b>同一个知识问答，在零售是门店制度查询，'
             '在制造是设备维修手册，在金融是信贷合规问答，在医疗是诊疗规范检索——'
             '构建模式、评测方法、安全框架完全共用，变化的只是知识、权限与验收口径。</p>'
             '<div class="chips">' + ''.join('<span>%s</span>' % x for x in
             ['零售', '制造', '金融', '医疗', '教育', '政务', '能源', '物流', '法律', '汽车', '研发效能', '媒体']) + '</div>'
             '<table class="ov-tbl"><thead><tr><th>角色</th><th>优先读</th><th>立刻做的一件事</th></tr></thead><tbody>'
             '<tr><td>业务负责人</td><td>0.4 / 3.0 / 8.1</td><td>写一个带边界与停止条件的一句话需求</td></tr>'
             '<tr><td>前沿部署工程师 FDE</td><td>全册，重点 3 / 4 / 5 / 7 / 9</td><td>按 14 步跑完三个演练项目，补齐交付物</td></tr>'
             '<tr><td>平台 / 运维工程</td><td>7.1 / 7.3 / 7.7 / 9.4</td><td>画部署拓扑与数据流向，做压测与回滚演练</td></tr>'
             '<tr><td>安全 / 合规</td><td>5.5 / 7.6 / 9.6 / 10.2</td><td>出权限矩阵、许可核对清单与红队用例</td></tr>'
             '<tr><td>内训讲师 / 带团队</td><td>0.4 / 第八篇 / 附录 F</td><td>用最终目录排一门课，每节绑定一个产出物</td></tr>'
             '</tbody></table></section>')

    # 08 边界
    H.append('<section class="ov-sec" id="ov-08"><div class="nn">08 / BOUNDARIES</div>'
             '<h2>边界声明</h2><div class="ov-bound"><b>请连同以下边界一起对外使用：</b><ul>'
             '<li>本手册是独立学习整理的能力体系，不隶属、不代言任何厂商，不是任何认证的官方教材；题库亦非官方题库。</li>'
             '<li>第九、十一～十四篇、第三册、附录 E、术语词典与题库中出现的产品与开源项目名称，均为公开资料举例，不构成推荐、排名、背书或采购建议。</li>'
             '<li>三个演练项目、四个部署方案包与第十四篇的行业案例均为教学演练组合 / 公开事实归纳，非真实客户案例或官方实施方案，数据不外推。</li>'
             '<li>第三册是对开源课程的原创解读，原文版权归原权利人；引用数字须区分原书引用 / 公开报道 / 需当期核对。</li>'
             '<li>不提供性能实测数字、价格、合规资质结论或投资回报承诺；平台功能、许可与规格以当期官方文档为准。</li>'
             '<li>题库正确率只用于定位薄弱能力域，不作为能力认证结论。</li></ul></div></section>')

    # 09 下一步
    H.append('<section class="ov-sec" id="ov-09"><div class="nn">09 / NEXT</div>'
             '<h2>从这里进入</h2>'
             '<div class="pt-intents" style="margin:14px 0 20px">'
             '<div class="pt-intent"><b>📖 进正文</b><p>十四篇 + 第三册 + 附录 A–F，19 个知识单元全对应，按 14 步路径逐步打勾。</p>'
             '<a href="01_主手册.html">打开主手册 →</a></div>'
             '<div class="pt-intent"><b>⚡ 现场速查</b><p>A–Q 十七组，名词 / 疑难 / FAQ / 命令 / 公式 / 讲解 / 选型 / 考核 / 模型 / Agent / TTS / 案例。</p>'
             '<a href="02_速查手册.html">打开速查手册 →</a></div>'
             '<div class="pt-intent"><b>📝 检验掌握度</b><p>%d 道题、两类选择题，打乱题序与选项，做完成绩单定位薄弱能力域。</p>'
             '<a href="FDE工程师考核题库.html">开始组卷 →</a></div>'
             '<div class="pt-intent"><b>📗 精读开源课程</b><p>逐章解读 13 章开源版，18 张方法卡与双向映射，补齐商业交付与采纳视角。</p>'
             '<a href="03_开源课程解读.html">打开第三册 →</a></div></div>'
             % q_total)
    H.append('<div class="ov-pager">'
             '<a href="index.html"><span>← 上一站 · L0 入口</span><b>返回门户</b></a>'
             '<a class="next" href="01_主手册.html"><span>下一站 · L2 详细 →</span><b>进入主手册</b></a>'
             '</div></section>')

    H.append('</div></div></div></main>')
    title = '手册介绍 · 企业级智能体交付实战手册'
    desc = ('一页看清企业级智能体交付实战手册的定位、三项核心能力、五阶段交付、'
            '十四篇结构与第三册、规模数据、七个特色、14 步节奏、跨行业适用与边界声明。')
    return sc.page_shell(title, desc, 'intro', crumbs, ''.join(H),
                         extra_css=PAGE_CSS, extra_js=TOC_JS)


# ---------------------------------------------------------------- 站点地图
def sitemap_doc():
    crumbs = _crumbs(("门户", "index.html"), ("资料", None), ("站点地图", None))
    H = []
    H.append('<main class="sm-main"><section class="ov-hero"><div class="sx-wrap">'
             '<div class="pt-kicker"><i></i>SITEMAP · INFORMATION ARCHITECTURE · ' + sc.VERSION + '</div>'
             '<h1>站点地图与<span class="pt-grad">导航规则</span></h1>'
             '<p>这一页把全站的层级、页面清单与跳转约定写清楚：上线部署前先照这张图核对目录，'
             '任何时候都能回答「我在哪、我从哪来、下一步去哪」。</p></div></section>')

    H.append('<div class="sx-wrap"><section class="sm-sec"><div class="pt-sec-head">'
             '<div class="pt-sec-num">01</div><div><h2>三层信息架构</h2>'
             '<p>L0 门户负责分流，L1 介绍负责讲清体系，L2 详细负责学与用；每一层都能回到任意一层。</p>'
             '</div></div><div class="ia-box">' + IA_SVG + '</div></section>')

    H.append('<section class="sm-sec"><div class="pt-sec-head">'
             '<div class="pt-sec-num">02</div><div><h2>页面清单</h2>'
             '<p>共 29 个 HTML 页面 + Markdown 源文与数据文件；全部用相对路径互跳。</p>'
             '</div></div><table class="ov-tbl"><thead><tr>'
             '<th>层级 / 页面</th><th>用途</th><th>入口</th></tr></thead><tbody>'
             '<tr><td>L0 · 入口门户</td><td>品牌、价值主张、核心数据、三层阅读路径、来意分流、IA 图</td><td><a href="index.html">index.html</a></td></tr>'
             '<tr><td>L1 · 手册介绍</td><td>定位、能力体系、十四篇结构与第三册、规模、特色、节奏、适用与边界</td><td><a href="手册展示页.html">手册展示页.html</a></td></tr>'
             '<tr><td>L1 · 站点地图</td><td>本页：三层 IA 图、页面清单、导航规则</td><td><a href="站点地图.html">站点地图.html</a></td></tr>'
             '<tr><td>L2 · 主手册</td><td>十四篇正文 + 附录 A–F，19 个知识单元全对应，8 张内联 SVG</td><td><a href="01_主手册.html">01_主手册.html</a></td></tr>'
             '<tr><td>L2 · 技术补强（主手册 11–14 篇）</td><td>模型选型五维矩阵、Agent 搭建与测试（对照 CS329Z）、语音与 TTS 全链路选型、12 类跨行业案例</td><td><a href="01_主手册.html#anchor-model">第十一篇 →</a></td></tr>'
             '<tr><td>L2 · 速查手册</td><td>A–Q 十七组，38 项必背速达，现场命令与 O/P/Q 技术速查</td><td><a href="02_速查手册.html">02_速查手册.html</a></td></tr>'
             '<tr><td>L2 · 术语词典</td><td>291 条术语按 11 类筛选、关键词检索、相关词条互跳</td><td><a href="术语词典.html">术语词典.html</a></td></tr>'
             '<tr><td>L2 · 开源课程精读</td><td>第三册：开源版 13 章逐章解读、18 张方法卡、双向映射、版权边界</td><td><a href="03_开源课程解读.html">03_开源课程解读.html</a></td></tr>'
             '<tr><td>L2 · 细节追问库</td><td>横切能力：三册每个标题 + 19 节笔记，每个模块 5 个角度，提示词自带上下文可复制</td><td><a href="细节追问提示词库.html">细节追问提示词库.html</a></td></tr>'
             '<tr><td>L2 · 考核题库</td><td>220 题 / 单选 + 多选两类 / 15 个能力域，打乱复习、三种模式、成绩单</td><td><a href="FDE工程师考核题库.html">FDE工程师考核题库.html</a></td></tr>'
             '<tr><td>L2 · 逐节笔记索引</td><td>19 节课程逐节笔记的 HTML / Markdown 双份副本</td><td><a href="参考资料/逐节笔记索引.html">参考资料/逐节笔记索引.html</a></td></tr>'
             '<tr><td>L2 · 19 节笔记</td><td>lesson-01..19.html，265 张本地课程截图，用于对照核验</td><td><a href="参考资料/课程逐节笔记/lesson-01.html">lesson-01.html …</a></td></tr>'
             '<tr><td>L2 · 使用说明</td><td>打开方式、三层导航、题库与追问用法、目录结构、静态托管部署</td><td><a href="离线使用说明.md">离线使用说明.md</a></td></tr>'
             '<tr><td>L2 · 核验报告</td><td>28 组全面复检结论（覆盖度 / 交互 / 追问 / 导航 / 第三册 / 离线 / 双端）</td><td><a href="核验报告.md">核验报告.md</a></td></tr>'
             '</tbody></table></section>')

    H.append('<section class="sm-sec"><div class="pt-sec-head">'
             '<div class="pt-sec-num">03</div><div><h2>导航规则</h2>'
             '<p>这套约定同时保证「本地双击打开」与「静态托管上线」体验一致。</p>'
             '</div></div><div class="sm-grid">'
             '<div class="sm-card"><div class="lv">RULE 01</div><h3>全局导航恒定</h3>'
             '<p>每个页面顶部都有同一条主导航（八栏目：门户 / 介绍 / 学习 / 精读 / 查阅 / 追问 / 考核 / 资料），当前栏目高亮；手机端折叠为菜单。</p></div>'
             '<div class="sm-card"><div class="lv">RULE 02</div><h3>面包屑标明层级</h3>'
             '<p>导航条下方给出「门户 / 当前栏目 / 当前页」，并固定提供站点地图入口，任何时候都能回到 L0。</p></div>'
             '<div class="sm-card"><div class="lv">RULE 03</div><h3>页脚即站点地图</h3>'
             '<p>页脚按「认识 / 学习 / 查阅与追问 / 资料」四组列出主要页面；阅读页用精简页脚条避免干扰正文。</p></div>'
             '<div class="sm-card"><div class="lv">RULE 04</div><h3>相对路径、无域名依赖</h3>'
             '<p>所有互跳均为相对路径并带目录深度前缀（笔记页用 <code>../../</code>），本地 file:// 与线上 HTTP 都能直接工作。</p></div>'
             '<div class="sm-card"><div class="lv">RULE 05</div><h3>稳定锚点速达</h3>'
             '<p>38 个 <code>#anchor-*</code> 稳定锚点在三册、题库页、介绍页、词典页与提示词库之间互跳，生成器与核验脚本逐一验证可达。</p></div>'
             '<div class="sm-card"><div class="lv">RULE 06</div><h3>零外部请求</h3>'
             '<p>CSS / JS / 字体栈 / SVG / 术语 JSON / 题目 JSON / 追问提示词 JSON / 截图全部内嵌或本地存放；深浅主题与进度只写 localStorage。</p></div>'
             '</div></section>')

    H.append('<section class="sm-sec"><div class="pt-sec-head">'
             '<div class="pt-sec-num">04</div><div><h2>上线部署要点</h2>'
             '<p>本目录就是一个完整的静态站点，无需构建、无需服务端、无需数据库。</p>'
             '</div></div><div class="ov-box">'
             '<p style="margin:0 0 10px"><b>直接托管：</b>把整个目录上传到任意静态托管服务，'
             '入口文件设为 <code>index.html</code> 即可；所有子页面与 <code>参考资料/</code> 目录保持原有相对位置。</p>'
             '<p style="margin:0 0 10px"><b>本地预览：</b>在本目录执行 <code>python3 -m http.server 8000</code>，'
             '浏览器访问 <code>http://localhost:8000/index.html</code>；手机连同一 Wi-Fi 访问局域网地址同样可用。</p>'
             '<p style="margin:0"><b>重新生成：</b>执行 <code>python3 build_html.py</code> 重跑全部页面与 zip，'
             '再执行 <code>python3 verify_offline.py</code> 做全面复检；两个脚本都只用 Python 标准库，不需要联网或安装依赖。</p>'
             '</div></section>')

    H.append('<div class="ov-pager" style="margin-top:34px">'
             '<a href="index.html"><span>← 上一站 · L0 入口</span><b>返回门户</b></a>'
             '<a class="next" href="手册展示页.html"><span>相邻页 · L1 介绍 →</span><b>打开手册介绍</b></a>'
             '</div></div></main>')

    title = '站点地图与导航规则 · 企业级智能体交付实战手册'
    desc = '三层信息架构（门户 / 介绍 / 详细）、全站页面清单、六条导航规则与静态托管上线要点。'
    return sc.page_shell(title, desc, 'resources', crumbs, ''.join(H),
                         extra_css=PAGE_CSS)
