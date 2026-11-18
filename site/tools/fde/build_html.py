#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业级智能体交付实战手册 · 离线双端阅读器生成器
=====================================================
零第三方依赖，纯 Python 标准库。运行：python3 build_html.py

产出（全部在交付目录内，相对路径互跳，无任何外部资源请求）：
  01_主手册.html                  主手册阅读版（手机 / 电脑）
  02_速查手册.html                速查手册阅读版（手机 / 电脑）
  index.html                      产品级入口门户（三层 IA / Hero / 导航分布图）
  手册展示页.html                  独立介绍页（L1）
  站点地图.html                    三层信息架构与导航规则
  细节追问提示词库.html             每个学习点 × 5 个角度的可复制追问提示词
  FDE工程师考核题库.html            独立考核题库（208 题 / 单选 + 多选 / 打乱复习）
  手册展示页.html                  独立对外展示页
  参考资料/课程逐节笔记/lesson-01..19.md    19 节逐节笔记本地副本
  参考资料/课程逐节笔记/lesson-01..19.html  逐节笔记双端阅读版
  参考资料/逐节笔记索引.html      19 节索引
  离线使用说明.md
  企业智能体FDE交付实战手册_离线资源包.zip   整体离线资源包（在交付目录上一级）
"""
import re
import json
import html as ihtml
import shutil
import zipfile
from pathlib import Path
from urllib.parse import unquote

import glossary_data
import figure_data
import question_bank_data
import exam_pages
import site_chrome
import site_pages
import prompt_data

BASE = Path(__file__).resolve().parent
REF = BASE / "参考资料"
LESSONS = REF / "课程逐节笔记"
SRC_LESSONS = LESSONS
ZIP_PATH = BASE.parent / "企业智能体FDE交付实战手册_离线资源包.zip"

MAIN_MD = "01_主手册_企业智能体FDE交付实战.md"
QUICK_MD = "02_速查手册_名词疑难与FAQ.md"
BOOK3_MD = "03_开源课程解读.md"
BOOK3_HTML = "03_开源课程解读.html"
MAIN_HTML = "01_主手册.html"
QUICK_HTML = "02_速查手册.html"
GLOSS_HTML = "术语词典.html"
QUIZ_HTML = exam_pages.QUIZ_HTML
SHOW_HTML = exam_pages.SHOW_HTML
SITE_MAP_HTML = "站点地图.html"
ASK_HTML = "细节追问提示词库.html"
ASK_PY = "prompt_data.py"
VERSION = "v5.0"
DOC_HTML = {"main": MAIN_HTML, "quick": QUICK_HTML, "book3": BOOK3_HTML,
            "page": GLOSS_HTML, "quiz": QUIZ_HTML, "show": SHOW_HTML, "ask": ASK_HTML}
PREFIX = {"main": "", "quick": "", "book3": "", "lesson": "../../", "page": ""}

DOCS = [
    dict(key="main", md=MAIN_MD, out=MAIN_HTML,
         title="企业级智能体交付实战手册 · FDE 能力体系与实施标准", badge="主手册",
         sub="跨行业通用 · 19 个知识单元 · 十四篇正文 · 14 步学习路径 · 8 张离线图示 · 两类选择题考核 · 模型 / Agent / TTS / 跨行业补强 · 逐点细节追问",
         pills=["跨行业通用 / 厂商中立", "19 个知识单元全对应", "3 个全新实战项目",
                "14 步可勾选学习路径", "8 张内联 SVG 图示", "专业名词点击释义",
                "第九篇选型 / 第十篇缺口清单", "第十一～十四篇技术补强",
                "附录 F 40 行最终目录", "10.5 两类选择题", "v5.0"]),
    dict(key="quick", md=QUICK_MD, out=QUICK_HTML,
         title="企业级智能体交付 · 重点速查手册", badge="速查手册",
         sub="A–Q 十七组速查 · 必背速达 38 项 · 现场命令 · 指标公式 · 对外表达 · 国内选型 · N 组考核 · O/P/Q 技术补强",
         pills=["⚡ 必背速达 38 项", "A–Q 十七组", "名词 / 疑难 / FAQ",
                "J 组现场命令", "K 组指标公式", "L 组对外讲解",
                "M 组选型速查", "N 组考核题型", "O/P/Q 模型 · Agent · TTS · 案例", "v5.0"]),
    dict(key="book3", md=BOOK3_MD, out=BOOK3_HTML,
         title="开源课程精读模块 · 《前线部署工程师》开源版逐章解读与对照", badge="开源精读",
         sub="fde4.ai/book/ 开源版 13 个文档的细致消化 · 7 篇精读 + 附录 Z · 18 张方法论卡片 · 双向映射 · 逐点细节追问",
         pills=["独立模块 · 原创解读非转载", "13 章逐章精读", "18 张方法论卡片",
                "与 4 章 19 单元双向映射", "与 CS329Z 交叉验证",
                "来源清单与版权边界", "专业名词点击释义", "v5.0"]),
]

MAIN_MD_TEXT = (BASE / MAIN_MD).read_text(encoding="utf-8")
QUICK_MD_TEXT = (BASE / QUICK_MD).read_text(encoding="utf-8")
BOOK3_MD_TEXT = (BASE / BOOK3_MD).read_text(encoding="utf-8")
ASK_MODULES = prompt_data.build_modules(
    MAIN_MD_TEXT, QUICK_MD_TEXT, glossary_data.TERM_KEYS, VERSION, BOOK3_MD_TEXT)
ASK_BY_SEC = {(m["book"], m["sec"]): m["id"] for m in ASK_MODULES}
ASK_DATA = prompt_data.payload_obj(ASK_MODULES, VERSION)


def ask_json_for(book=None):
    """按册拆出内嵌数据，避免每个阅读页都背全库体积；
    顶层协议字段（原文标记 / 精简说明 / 会话开场白 / 站点键）必须随每页一起带。"""
    data = dict(ASK_DATA)
    mods = data["modules"]
    if book:
        mods = {k: v for k, v in mods.items() if v["book"] == book}
    data["modules"] = mods
    return prompt_data.dumps(data)


def attach_ask(doc, json_str, btn_html=""):
    """给已生成 HTML 注入追问组件（样式 / 弹窗 / 数据 / 脚本 / 可选入口按钮）。"""
    doc = doc.replace('</head>', '<style>%s</style></head>' % prompt_data.ASK_CSS, 1)
    if btn_html:
        doc = doc.replace('<div class="cover">', btn_html + '<div class="cover">', 1)
    body = (prompt_data.ASK_POP_HTML
            + '<script>window.__FDE_ASK__=%s;</script>' % json_str
            + '<script>%s</script>' % prompt_data.ASK_JS)
    return doc.replace('</body>', body + '</body>', 1)


# 必背速达定义： (稳定锚点, 显示名, 场景分组, 目标册, 用于定位标题的唯一关键词)
MUST = [
    ("anchor-must-numbers",   "必背数字与硬约束",       "考前 10 分钟", "quick", "I 组｜数字与硬约束一览"),
    ("anchor-must-15",        "15 句必背",              "考前 10 分钟", "quick", "G2 一句话必背"),
    ("anchor-exam",           "考试权重与题型",         "考前 10 分钟", "quick", "G1 能力权重与题型"),
    ("anchor-confuse",        "易混淆概念 25 组",       "考前 10 分钟", "quick", "B 组｜易混淆概念对照"),
    ("anchor-traps",          "15 个易错判断",          "考前 10 分钟", "quick", "G3 十五个易错判断"),
    ("anchor-import",         "导入规格与切分参数",     "平台配置前",   "quick", "C1 文档导入规格"),
    ("anchor-vars",           "变量隔离表",             "平台配置前",   "quick", "C3 变量隔离表"),
    ("anchor-mode-quick",     "四种模式速选 + 硬约束",  "平台配置前",   "quick", "C4 四种应用模式速选"),
    ("anchor-canvas",         "方案画布",               "方案评审前",   "main",  "3.0.3 方案画布"),
    ("anchor-five-stage",     "五阶段交付方法论",       "方案评审前",   "main",  "5.2 五阶段交付方法论"),
    ("anchor-diagnose",       "疑难诊断树",             "排障现场",     "quick", "D 组｜疑难问题诊断树"),
    ("anchor-faq",            "常见问题解决方案 FAQ",   "排障现场",     "quick", "E 组｜常见问题解决方案"),
    ("anchor-cheatsheet",     "现场命令与小抄",         "排障现场",     "quick", "J 组｜现场命令与小抄"),
    ("anchor-pitfalls",       "踩坑清单 Top 20",        "上线与验收",   "quick", "F 组｜踩坑清单 Top 20"),
    ("anchor-checklist-quick", "上线检查单（精简版）",  "上线与验收",   "quick", "H6 上线检查单（精简版）"),
    ("anchor-checklist",      "上线检查单（完整版）",   "上线与验收",   "main",  "D.5 上线检查单"),
    ("anchor-security",       "安全合规与责任 AI",      "上线与验收",   "main",  "5.5 安全合规与责任 AI"),
    ("anchor-metrics",        "指标定义与计算口径",     "验收签字",     "main",  "7.5.1 指标定义与计算口径"),
    ("anchor-formulas",       "指标与成本公式速查",     "验收签字",     "quick", "K 组｜指标与成本公式速查"),
    ("anchor-coverage",       "19 节覆盖对照",          "复盘核验",     "main",  "附录 A｜能力框架 19 个知识单元覆盖对照表"),
    ("anchor-learning-path",  "分步学习路径 14 步",     "从零开始学",   "main",  "0.4 分步学习路径"),
    ("anchor-explain",        "一句话定义与三种讲法",   "要讲给别人听", "main",  "8.1 一句话定义与三种时长的讲法"),
    ("anchor-express",        "对外表达速查",           "要讲给别人听", "quick", "L 组｜对外表达与讲解速查"),
    # ---- v4.0 新增 6 项：术语 / 选型 / 缺口 / 图示 / 最终目录 ----
    ("anchor-glossary",       "术语词典（点击释义）",   "从零开始学",   "page",  None),
    ("anchor-catalog",        "科学化最终目录总表",     "从零开始学",   "main",  "F.6 最终目录总表"),
    ("anchor-selection",      "国内方案选型与方案包",   "方案评审前",   "main",  "9.4 四个部署方案包"),
    ("anchor-selection-quick", "选型评审 12 问",        "方案评审前",   "quick", "M3 选型评审 12 问"),
    ("anchor-reading",        "还缺什么 · 缺口清单",    "复盘核验",     "main",  "10.2 明确还缺的 10 类内容"),
    ("anchor-figures",        "项目图示索引",           "要讲给别人听", "main",  "F.7 图示索引"),
    # ---- v4.1 新增 3 项：考核题库 / 题型判分 / 对外展示 ----
    ("anchor-quiz",           "FDE 考核题库（打乱复习）", "考前 10 分钟", "quiz",  None),
    ("anchor-examtypes",      "两类选择题与打乱复习法", "考前 10 分钟", "main",
     "10.5 版本化维护、考核题型与间隔复习节奏"),
    ("anchor-showcase",       "手册展示页（对外介绍）", "从零开始学",   "show",  None),
    # ---- v4.3 新增 1 项：把某个学习点带去问任意 AI ----
    ("anchor-ask",            "细节追问提示词库",       "从零开始学", "ask",   None),
    # ---- v5.0 新增 3 项：开源精读 / 模型选型 / 语音 TTS ----
    ("anchor-openbook",       "开源课程精读 · 全书地图", "从零开始学", "book3", "第 1 篇｜全书地图"),
    ("anchor-model",          "五维模型选型矩阵",       "方案评审前", "main",  "11.3 五维选型矩阵"),
    ("anchor-tts",            "语音 TTS 链路与评测",     "方案评审前", "main",  "13.1 先看清全链路"),
    ("anchor-agent",          "Agent 搭建与测试八步",     "方案评审前", "main",  "12.2 从零搭建 Agent 的八步"),
    ("anchor-cases",          "跨行业真实案例集",         "要讲给别人听", "main", "14.1 制造业"),
]
ANCHOR_DOC = {a: d for a, _, _, d, _ in MUST}
GLOSSARY_JSON = json.dumps(
    {k: {"full": v[0], "cat": v[1], "def": v[2], "why": v[3], "rel": v[4]}
     for k, v in glossary_data.GLOSSARY.items()},
    ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
MUST_GROUPS = ["从零开始学", "考前 10 分钟", "平台配置前", "方案评审前", "要讲给别人听",
               "排障现场", "上线与验收", "验收签字", "复盘核验"]

CSS = r"""
:root{
  --bg:#ffffff; --bg-soft:#f5f5f7; --bg-soft2:#fafafa; --card:#ffffff;
  --text:#1d1d1f; --text-2:#424245; --muted:#6e6e73;
  --line:#e5e5ea; --line-strong:#d2d2d7;
  --accent:#0071e3; --accent-soft:#eaf3ff;
  --warn:#b25000; --warn-bg:#fff6e8;
  --code-bg:#f5f5f7; --code-text:#b25000;
  --zebra:rgba(127,127,127,.045); --shadow:0 6px 24px rgba(0,0,0,.10);
  --radius:14px; --fs:16px; --topbar-h:56px;
}
html[data-theme="dark"]{
  --bg:#16181d; --bg-soft:#20232a; --bg-soft2:#1a1d23; --card:#20232a;
  --text:#f2f2f5; --text-2:#c9ccd3; --muted:#9297a2;
  --line:#2f333c; --line-strong:#3d424d;
  --accent:#63adff; --accent-soft:#172c47;
  --warn:#ffbc74; --warn-bg:#35271a;
  --code-bg:#20232a; --code-text:#ffbc74;
  --zebra:rgba(255,255,255,.035); --shadow:0 6px 24px rgba(0,0,0,.45);
}
*{box-sizing:border-box}
html{scroll-behavior:auto}
body{
  margin:0;background:var(--bg);color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","PingFang SC","Helvetica Neue","Microsoft YaHei",sans-serif;
  font-size:var(--fs);line-height:1.78;-webkit-font-smoothing:antialiased;
  -webkit-text-size-adjust:100%;
}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
#progress{position:fixed;top:0;left:0;height:3px;width:0;background:var(--accent);z-index:120;transition:width .08s linear}
.topbar{
  position:sticky;top:0;z-index:100;min-height:var(--topbar-h);display:flex;align-items:center;gap:8px;
  padding:6px 20px;background:var(--card);border-bottom:1px solid var(--line);flex-wrap:wrap;
}
.topbar .brand{font-weight:700;font-size:14px;white-space:nowrap}
.topbar .sep{color:var(--line-strong)}
.topbar .docname{font-size:13px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:280px}
.topbar .spacer{flex:1}
.topbar .btn{
  font-size:12.5px;color:var(--accent);border:1px solid var(--line);background:var(--bg);
  border-radius:999px;padding:5px 11px;cursor:pointer;white-space:nowrap;font-family:inherit;line-height:1.5;
}
.topbar .btn:hover{border-color:var(--accent);text-decoration:none}
.topbar .btn.on{background:var(--accent-soft);border-color:var(--accent);font-weight:650}
#menuBtn{display:none;font-size:17px;padding:3px 10px}
.layout{display:flex;align-items:flex-start}
.sidebar{
  position:sticky;top:var(--topbar-h);height:calc(100vh - var(--topbar-h));width:308px;flex:0 0 308px;
  overflow-y:auto;border-right:1px solid var(--line);background:var(--bg-soft2);padding:20px 14px 44px;z-index:95;
}
.sidebar::-webkit-scrollbar{width:8px}
.sidebar::-webkit-scrollbar-thumb{background:var(--line-strong);border-radius:8px}
.drawer-head{display:none}
.toc-title{font-size:11px;font-weight:700;letter-spacing:.12em;color:var(--muted);margin:0 8px 10px}
#tocFilter{
  width:100%;padding:8px 12px;border:1px solid var(--line);border-radius:9px;background:var(--card);
  color:var(--text);font-size:13px;outline:none;margin-bottom:12px;font-family:inherit;
}
#tocFilter:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.toc ul{list-style:none;margin:0 0 6px;padding:0}
.toc li{margin:0}
.toc a{
  display:block;padding:5px 10px;border-radius:7px;color:var(--text-2);font-size:12.8px;
  line-height:1.5;border-left:2px solid transparent;
}
.toc a:hover{background:var(--card);color:var(--accent);text-decoration:none}
.toc a.active{background:var(--accent-soft);color:var(--accent);font-weight:650;border-left-color:var(--accent)}
.toc a.lv1{font-weight:700;color:var(--text);margin-top:10px;font-size:13.2px}
.toc a.lv2{padding-left:22px;font-size:12.5px}
.toc a.lv3{padding-left:36px;font-size:12px;color:var(--muted)}
.toc .grp{font-size:11px;font-weight:700;letter-spacing:.08em;color:var(--muted);padding:14px 10px 5px;border-top:1px solid var(--line);margin-top:10px}
.toc .grp:first-child{border-top:0;margin-top:0;padding-top:2px}
.toc a.quick{color:var(--accent);font-size:12.6px;padding-left:18px}
.toc a.quick::before{content:"⚡";margin-right:5px;font-size:11px}
.toc .cross{display:flex;gap:6px;flex-wrap:wrap;padding:4px 8px 10px}
.toc .cross a{font-size:12px;border:1px solid var(--line);border-radius:8px;padding:5px 9px;background:var(--card)}
.drawer-mask{display:none;position:fixed;inset:0;background:rgba(0,0,0,.44);z-index:90}
.main{flex:1;min-width:0;display:flex;justify-content:center;padding:0 36px 110px}
.content{width:100%;max-width:940px;padding-top:30px}
.cover{
  background:linear-gradient(135deg,var(--accent-soft) 0%,var(--bg-soft2) 58%,var(--card) 100%);
  border:1px solid var(--line);border-radius:20px;padding:36px 38px;margin-bottom:26px;
}
.cover .kicker{font-size:11.5px;font-weight:700;letter-spacing:.14em;color:var(--accent)}
.cover h1{font-size:36px;line-height:1.28;margin:12px 0 10px;border:0;padding:0;letter-spacing:-.02em}
.cover .sub{color:var(--muted);font-size:14.5px;margin:0}
.cover .meta{display:flex;flex-wrap:wrap;gap:7px;margin-top:20px}
.cover .pill{font-size:12px;color:var(--text-2);background:var(--card);border:1px solid var(--line);border-radius:999px;padding:5px 12px}
.cover .jump{display:flex;gap:8px;flex-wrap:wrap;margin-top:20px}
.cover .jump a{font-size:12.5px;border:1px solid var(--line);border-radius:9px;padding:6px 12px;background:var(--card);font-weight:600}
.must{
  border:1px solid var(--line);border-radius:16px;padding:20px 22px;margin:0 0 34px;background:var(--bg-soft2);
}
.must h2{font-size:18px;margin:0 0 4px;border:0;padding:0}
.must .hint{color:var(--muted);font-size:12.8px;margin:0 0 14px}
.must .mg{margin-top:12px}
.must .mgt{font-size:12px;font-weight:700;color:var(--muted);letter-spacing:.06em;margin-bottom:6px}
.must .links{display:flex;flex-wrap:wrap;gap:7px}
.must .links a{
  font-size:12.8px;border:1px solid var(--line);border-radius:999px;padding:5px 12px;
  background:var(--card);color:var(--accent);font-weight:600;
}
.must .links a:hover{border-color:var(--accent);text-decoration:none;background:var(--accent-soft)}
.must .links a.cross::after{content:" ↗";font-size:11px;color:var(--muted)}
h1,h2,h3,h4,.anchor-flag{scroll-margin-top:calc(var(--topbar-h) + 14px)}
h1{font-size:29px;line-height:1.36;letter-spacing:-.015em;margin:52px 0 18px;padding-bottom:13px;border-bottom:1px solid var(--line);font-weight:700}
h2{font-size:22.5px;line-height:1.45;margin:38px 0 15px;font-weight:680;letter-spacing:-.01em}
h3{font-size:18px;line-height:1.5;margin:28px 0 11px;font-weight:660}
h4{font-size:16px;margin:22px 0 9px;font-weight:650}
p{margin:12px 0;color:var(--text-2)}
strong{color:var(--text);font-weight:650}
hr{border:0;border-top:1px solid var(--line);margin:34px 0}
blockquote{
  margin:18px 0;padding:13px 18px;background:var(--accent-soft);border-left:3px solid var(--accent);
  border-radius:0 10px 10px 0;color:var(--text-2);
}
blockquote p{margin:5px 0}
ul,ol{padding-left:24px;margin:12px 0;color:var(--text-2)}
li{margin:5px 0}
li::marker{color:var(--muted)}
code{
  font-family:"SF Mono",SFMono-Regular,Menlo,Consolas,monospace;font-size:.86em;
  background:var(--code-bg);border:1px solid var(--line);border-radius:5px;padding:1px 5px;color:var(--code-text);
}
pre{
  background:var(--code-bg);border:1px solid var(--line);border-radius:var(--radius);
  padding:16px 18px;overflow-x:auto;margin:16px 0;line-height:1.62;-webkit-overflow-scrolling:touch;
}
pre code{background:none;border:0;padding:0;color:var(--text-2);font-size:12.8px}
.tablewrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{width:100%;border-collapse:separate;border-spacing:0;margin:16px 0;border:1px solid var(--line);border-radius:12px;overflow:hidden;font-size:14px}
th,td{padding:10px 13px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line);color:var(--text-2)}
th{background:var(--bg-soft);font-weight:650;color:var(--text);white-space:nowrap}
tr:last-child td{border-bottom:0}
tbody tr:nth-child(even){background:var(--zebra)}
tbody tr:hover{background:var(--accent-soft)}
del{color:var(--muted)}
.content img{max-width:100%;height:auto;display:block;margin:15px auto;border:1px solid var(--line);
  border-radius:10px;background:var(--card)}
.img-missing{display:block;font-size:12.5px;color:var(--muted);background:var(--bg-soft);
  border:1px dashed var(--line-strong);border-radius:9px;padding:9px 12px;margin:12px 0}
.totop{
  position:fixed;right:22px;bottom:22px;width:42px;height:42px;border-radius:50%;
  background:var(--card);border:1px solid var(--line);box-shadow:var(--shadow);
  color:var(--accent);font-size:19px;cursor:pointer;display:none;align-items:center;justify-content:center;z-index:80;
}
.footer{margin-top:56px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted);font-size:12.8px}
@media (max-width:1000px){
  /* 窄屏顶部按钮会折成两行，同步抬高锚点跳转的避让距离 */
  :root{--topbar-h:78px}
  #menuBtn{display:inline-flex;align-items:center;justify-content:center}
  .topbar{padding:6px 12px;gap:6px}
  .topbar .docname,.topbar .sep{display:none}
  .topbar .btn.hide-sm{display:none}
  .topbar .btn{padding:5px 9px;font-size:12px}
  .sidebar{
    position:fixed;left:0;top:0;bottom:0;height:100vh;width:86vw;max-width:340px;
    transform:translateX(-103%);transition:transform .24s ease;box-shadow:var(--shadow);
    border-right:1px solid var(--line);z-index:110;padding-top:14px;
  }
  body.drawer-open .sidebar{transform:translateX(0)}
  body.drawer-open .drawer-mask{display:block}
  .drawer-head{display:flex;align-items:center;justify-content:space-between;padding:2px 8px 12px;font-weight:700;font-size:14px}
  .drawer-head button{border:1px solid var(--line);background:var(--card);color:var(--text);border-radius:8px;padding:3px 10px;font-size:13px;cursor:pointer}
  .main{padding:0 15px 88px}
  .content{padding-top:18px}
  .cover{padding:24px 20px;border-radius:16px}
  .cover h1{font-size:27px}
  .cover .sub{font-size:13.5px}
  .must{padding:16px 15px}
  h1{font-size:24px;margin-top:40px}
  h2{font-size:20px}
  h3{font-size:17px}
  table{font-size:13px;min-width:520px}
  th,td{padding:9px 11px}
  pre code{font-size:12px}
}
@media (max-width:420px){
  .topbar .brand{font-size:12.5px}
  .topbar .btn{padding:4px 8px;font-size:11.5px}
}
/* ---- v4.0 专业名词 / 英文 / 缩写：可点击特殊标记与释义弹窗 ---- */
.term{
  font:inherit;color:var(--accent);background:transparent;border:0;padding:0;margin:0;
  border-bottom:1px dashed var(--accent);border-radius:0;cursor:pointer;
  text-decoration:none;line-height:inherit;white-space:normal;text-align:left;
}
.term:hover,.term:focus{background:var(--accent-soft);border-bottom-style:solid;outline:none}
.term::after{content:"▾";font-size:.68em;opacity:.55;margin-left:1px;vertical-align:1px}
h1 .term,h2 .term,h3 .term,h4 .term{font-size:inherit;font-weight:inherit;color:inherit;
  border-bottom:1px dashed var(--accent)}
h1 .term::after,h2 .term::after,h3 .term::after,h4 .term::after{content:""}
.term-mask{position:fixed;inset:0;background:rgba(0,0,0,.36);z-index:200}
.term-pop{
  position:fixed;z-index:210;left:50%;top:50%;transform:translate(-50%,-50%);
  width:min(480px,calc(100vw - 32px));max-height:76vh;overflow-y:auto;
  background:var(--card);border:1px solid var(--line-strong);border-radius:16px;
  box-shadow:0 18px 60px rgba(0,0,0,.28);padding:20px 22px 18px;
}
.tp-head{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.tp-cat{font-size:11.5px;font-weight:700;color:var(--accent);background:var(--accent-soft);
  border-radius:999px;padding:3px 10px;letter-spacing:.03em}
.tp-head .sp{flex:1}
.tp-x{border:1px solid var(--line);background:var(--bg);color:var(--muted);
  border-radius:8px;width:28px;height:28px;cursor:pointer;font-size:14px;line-height:1}
.tp-title{font-size:21px;font-weight:700;margin:2px 0 3px;color:var(--text)}
.tp-full{font-size:12.8px;color:var(--muted);margin-bottom:14px;line-height:1.5}
.tp-sec{margin:12px 0}
.tp-sec b{display:block;font-size:11.5px;letter-spacing:.06em;color:var(--muted);margin-bottom:3px}
.tp-sec p{margin:0;font-size:14px;color:var(--text-2);line-height:1.7}
.tp-rel{display:flex;flex-wrap:wrap;gap:6px}
.tp-rel button{font:inherit;font-size:12.5px;border:1px solid var(--line);border-radius:999px;
  padding:4px 11px;background:var(--bg-soft2);color:var(--accent);cursor:pointer}
.tp-rel button:hover{border-color:var(--accent);background:var(--accent-soft)}
.tp-more{display:inline-block;margin-top:12px;font-size:12.8px;font-weight:650}
/* ---- v4.0 内联 SVG 图示（零外部资源，颜色跟随主题） ---- */
.figure{margin:20px 0;padding:14px;border:1px solid var(--line);border-radius:14px;background:var(--card)}
.figsvg{display:block;width:100%;height:auto;font-family:inherit}
.figsvg .b{fill:var(--bg-soft2);stroke:var(--line-strong);stroke-width:1.2}
.figsvg .ba{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1.4}
.figsvg .band{fill:var(--bg-soft);stroke:var(--line);stroke-width:1}
.figsvg .t{fill:var(--text);font-size:13.5px;font-weight:650}
.figsvg .t2{fill:var(--text);font-size:12.5px;font-weight:700}
.figsvg .s{fill:var(--muted);font-size:11.5px}
.figsvg .cap{fill:var(--accent);font-size:12px;font-weight:700}
.figsvg .h1{fill:var(--text);font-size:16px;font-weight:800}
.figsvg .k{fill:var(--accent);font-size:11px;font-weight:800;letter-spacing:.06em}
.figsvg .n{fill:#fff;font-size:11px;font-weight:800}
.figsvg .chip{fill:var(--accent);stroke:none}
.figsvg .rail{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1}
.figsvg .soft{fill:var(--bg-soft2);stroke:var(--line);stroke-width:1}
.figsvg .ghost{fill:none;stroke:var(--line-strong);stroke-width:1.2}
.figsvg .rail-ln{stroke:var(--accent);stroke-width:2;fill:none}
.figsvg .ln{stroke:var(--accent);stroke-width:1.6;fill:none}
.figsvg .axis{stroke:var(--line-strong);stroke-width:1.2;stroke-dasharray:4 4}
.figsvg marker path{fill:var(--accent)}
.figure figcaption{font-size:12.8px;color:var(--muted);margin-top:10px;line-height:1.65}
@media (max-width:1000px){
  .figure{padding:9px}
  .term-pop{left:0;top:auto;bottom:0;transform:none;width:100%;max-height:78vh;
    border-radius:18px 18px 0 0;border-bottom:0}
}
@media print{
  :root{--fs:11.5px}
  .topbar,.sidebar,.drawer-mask,.totop,#progress,.cover .jump,.must .links,
  .term-mask,.term-pop,.tp-x{display:none!important}
  .term{border-bottom:0;color:var(--text)}
  .term::after{content:""}
  .figure,.figsvg,.figsvg rect,.figsvg text{-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .figure{page-break-inside:avoid}
  .main{padding:0;display:block}
  .content{max-width:none;padding:0}
  h1{page-break-before:auto;page-break-after:avoid;font-size:21px;margin-top:24px}
  h2,h3,h4{page-break-after:avoid}
  table,pre,blockquote,.must{page-break-inside:avoid}
  .cover{background:#fff;border:0;padding:0 0 18px}
  .cover h1{font-size:25px}
  th{background:#f0f0f2!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  a{color:var(--text)}
  body{background:#fff;color:#000}
}
"""

JS = r"""
(function(){
  var body=document.body, root=document.documentElement;
  var links=[].slice.call(document.querySelectorAll('.toc a[href^="#"]'));
  var heads=links.map(function(a){return document.getElementById(a.getAttribute('href').slice(1));});
  function onScroll(){
    var st=window.scrollY||document.documentElement.scrollTop;
    var h=document.documentElement.scrollHeight-window.innerHeight;
    document.getElementById('progress').style.width=(h>0?(st/h*100):0)+'%';
    document.getElementById('totop').style.display=st>480?'flex':'none';
    var idx=-1;
    for(var i=0;i<heads.length;i++){ if(heads[i] && heads[i].getBoundingClientRect().top<150) idx=i; }
    links.forEach(function(a,i){a.classList.toggle('active',i===idx);});
  }
  window.addEventListener('scroll',onScroll,{passive:true}); onScroll();
  var flt=document.getElementById('tocFilter');
  if(flt) flt.addEventListener('input',function(e){
    var q=e.target.value.trim().toLowerCase();
    document.querySelectorAll('.toc li[data-s]').forEach(function(li){
      li.style.display=(!q||li.getAttribute('data-s').toLowerCase().indexOf(q)>-1)?'block':'none';
    });
  });
  document.getElementById('totop').addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'});});
  document.getElementById('printBtn').addEventListener('click',function(){window.print();});
  function closeDrawer(){body.classList.remove('drawer-open');}
  var mb=document.getElementById('menuBtn');
  if(mb) mb.addEventListener('click',function(){body.classList.toggle('drawer-open');});
  var mask=document.getElementById('drawerMask');
  if(mask) mask.addEventListener('click',closeDrawer);
  var dc=document.getElementById('drawerClose');
  if(dc) dc.addEventListener('click',closeDrawer);
  document.addEventListener('keydown',function(e){if(e.key==='Escape'){closeDrawer();hideTerm();}});
  document.querySelectorAll('.toc a').forEach(function(a){
    a.addEventListener('click',function(){ if(window.innerWidth<=1000) setTimeout(closeDrawer,80); });
  });
  var tb=document.getElementById('themeBtn');
  function paintTheme(){
    var d=root.getAttribute('data-theme')==='dark';
    if(tb){tb.textContent=d?'☀️':'🌙';tb.title=d?'切到浅色':'切到深色';}
  }
  if(tb) tb.addEventListener('click',function(){
    var d=root.getAttribute('data-theme')==='dark';
    root.setAttribute('data-theme',d?'light':'dark');
    try{localStorage.setItem('fde-theme',d?'light':'dark');}catch(e){}
    paintTheme();
  });
  paintTheme();
  var fs=parseFloat(getComputedStyle(root).getPropertyValue('--fs'))||16;
  function applyFs(){root.style.setProperty('--fs',fs+'px');
    try{localStorage.setItem('fde-fs',String(fs));}catch(e){}}
  var fp=document.getElementById('fsPlus'), fm=document.getElementById('fsMinus');
  if(fp) fp.addEventListener('click',function(){fs=Math.min(23,fs+1);applyFs();});
  if(fm) fm.addEventListener('click',function(){fs=Math.max(13,fs-1);applyFs();});
  var mq=document.getElementById('mustQuick');
  var mqb=document.getElementById('mustBtn');
  if(mqb&&mq) mqb.addEventListener('click',function(){
    mq.scrollIntoView({behavior:'smooth',block:'start'});
    mq.style.transition='box-shadow .3s';mq.style.boxShadow='0 0 0 3px var(--accent-soft)';
    setTimeout(function(){mq.style.boxShadow='';},1600);
  });

  /* ---- v4.0 专业名词 / 英文 / 缩写：点击弹释义，相关词条互跳 ---- */
  var G=__GLOSSARY_DATA__;
  var tmask=document.getElementById('termMask'), tpop=document.getElementById('termPop');
  function hideTerm(){if(tmask)tmask.hidden=true;if(tpop)tpop.hidden=true;}
  function showTerm(k){
    var d=G[k]; if(!d) return;
    document.getElementById('termCat').textContent=d.cat;
    document.getElementById('termTitle').textContent=k;
    document.getElementById('termFull').textContent=d.full;
    document.getElementById('termDef').textContent=d.def;
    document.getElementById('termWhy').textContent=d.why;
    var rel=document.getElementById('termRel'); rel.innerHTML='';
    (d.rel||'').split(/[,，、]/).forEach(function(x){
      x=x.trim(); if(!x||!G[x]) return;
      var b=document.createElement('button'); b.type='button'; b.textContent=x;
      b.addEventListener('click',function(){showTerm(x);});
      rel.appendChild(b);
    });
    if(!rel.children.length){var s=document.createElement('span');
      s.style.cssText='font-size:12.5px;color:var(--muted)';s.textContent='（暂无相关词条，可在术语词典中按分类浏览）';rel.appendChild(s);}
    tmask.hidden=false; tpop.hidden=false; tpop.scrollTop=0;
  }
  document.addEventListener('click',function(e){
    var t=e.target;
    while(t && t!==document && !(t.classList && t.classList.contains('term'))) t=t.parentNode;
    if(t && t!==document && t.getAttribute('data-term')){
      showTerm(t.getAttribute('data-term')); e.preventDefault();
    }
  });
  var tx=document.getElementById('termClose');
  if(tx) tx.addEventListener('click',hideTerm);
  if(tmask) tmask.addEventListener('click',hideTerm);
})();
"""

TERM_POP_HTML = ('<div class="term-mask" id="termMask" hidden></div>'
                 '<div class="term-pop" id="termPop" hidden role="dialog" aria-modal="true" '
                 'aria-labelledby="termTitle">'
                 '<div class="tp-head"><span class="tp-cat" id="termCat"></span><span class="sp"></span>'
                 '<button class="tp-x" id="termClose" title="关闭">✕</button></div>'
                 '<div class="tp-title" id="termTitle"></div><div class="tp-full" id="termFull"></div>'
                 '<div class="tp-sec"><b>是什么</b><p id="termDef"></p></div>'
                 '<div class="tp-sec"><b>交付里为什么重要</b><p id="termWhy"></p></div>'
                 '<div class="tp-sec"><b>相关词条（点击继续看）</b><div class="tp-rel" id="termRel"></div></div>'
                 '<a class="tp-more" href="__GLOSS_HREF__">📖 在术语词典中检索全部词条 →</a>'
                 '</div>')

HEAD_SCRIPT = ("<script>try{var t=localStorage.getItem('fde-theme');if(t)"
               "document.documentElement.setAttribute('data-theme',t);"
               "var f=localStorage.getItem('fde-fs');if(f)"
               "document.documentElement.style.setProperty('--fs',f+'px');}catch(e){}</script>")


def esc(s):
    return ihtml.escape(s, quote=True)


def attr(s):
    """s 已做过 html.escape(quote=False)，只需再处理双引号即可安全放进属性。"""
    return s.replace('"', '&quot;')


def rewrite_href(href, doc_key):
    """把 #anchor-xxx 稳定锚点按目标册改写为相对路径；外部链接保持原样。"""
    if href.startswith("#anchor-"):
        a = href[1:]
        target = ANCHOR_DOC.get(a)
        if target and target != doc_key:
            return PREFIX[doc_key] + DOC_HTML[target] + "#" + a
        return href
    return href


def _term_alt(k):
    """英文 / 缩写加边界，避免短词吞掉长词、避免命中单词内部。
    正文已做 HTML 转义，& 会变成 &amp;，这里兼容两种写法。"""
    p = re.escape(k).replace(r'\&', r'&(?:amp;)?')
    if k.isascii():
        return r'(?<![A-Za-z0-9_])' + p + r'(?![A-Za-z0-9_])'
    return p


# 按长度降序，一次扫描完成全部词条标记
_TERM_RE = re.compile('|'.join(_term_alt(k) for k in glossary_data.TERM_KEYS))


def mark_terms(t):
    """只在文本节点上做特殊标记；代码块、链接、图片整体原样保留。"""
    saved = []

    def keep(m):
        saved.append(m.group(0))
        return '\x00T%d\x00' % (len(saved) - 1)

    t = re.sub(r'<code\b[\s\S]*?</code>|<a\b[\s\S]*?</a>|<img\b[^>]*>', keep, t)
    parts = re.split(r'(<[^>]+>|&[A-Za-z#0-9]+;|\x00T\d+\x00)', t)
    for i, p in enumerate(parts):
        if not p or p.startswith('<') or p.startswith('&') or re.match(r'^\x00T\d+\x00$', p):
            continue
        parts[i] = _TERM_RE.sub(
            lambda m: '<button type="button" class="term" data-term="%s">%s</button>'
                      % (attr(ihtml.unescape(m.group(0))), m.group(0)), p)
    return re.sub(r'\x00T(\d+)\x00',
                  lambda m: saved[int(m.group(1))], ''.join(parts))


def inline(t, doc_key):
    stash = []

    def keep(m):
        stash.append(m.group(1))
        return "\x00C%d\x00" % (len(stash) - 1)

    t = re.sub(r'`([^`]+)`', keep, t)
    t = ihtml.escape(t, quote=False)

    def image(m):
        alt, src = m.group(1), m.group(2)
        if src.startswith(('http://', 'https://')):
            return '<img src="%s" alt="%s" loading="lazy">' % (attr(src), attr(alt))
        base_dir = LESSONS if doc_key == 'lesson' else BASE
        try:
            exists = (base_dir / unquote(src)).resolve().exists()
        except Exception:
            exists = False
        if exists:
            return '<img src="%s" alt="%s" loading="lazy">' % (attr(src), attr(alt))
        # 离线包未收录该截图时降级为文字说明，绝不留下死链
        return '<span class="img-missing">［图：%s｜原课程截图，当前离线包未收录］</span>' % alt

    t = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', image, t)

    def link(m):
        label, href = m.group(1), rewrite_href(m.group(2), doc_key)
        if href.startswith("#") or re.match(r"^[\w./%\-]+\.html", href) or href.endswith(".md"):
            return '<a href="%s">%s</a>' % (attr(href), label)
        return '<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>' % (attr(href), label)

    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'~~([^~]+)~~', r'<del>\1</del>', t)
    t = re.sub(r'\x00C(\d+)\x00',
               lambda m: '<code>%s</code>' % ihtml.escape(stash[int(m.group(1))], quote=False), t)
    return mark_terms(t)


def is_sep(line):
    return bool(re.match(r'^\s*\|[\s:\-\|]+\|\s*$', line)) and '-' in line


def split_row(line):
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    return [c.strip() for c in s.split('|')]


def must_href(anchor, doc_key):
    d = ANCHOR_DOC[anchor]
    if d == doc_key:
        return "#" + anchor
    return PREFIX[doc_key] + DOC_HTML[d] + "#" + anchor


def must_cards(doc_key):
    parts = ['<section class="must" id="mustQuick"><h2>⚡ 必背速达 · %d 个必要知识点</h2>' % len(MUST),
             '<p class="hint">按场景点击直达；带 ↗ 的条目会跳到另一册（相对路径，离线可用）。'
             '左侧目录 / 手机抽屉目录顶部也有同一份速达清单，可边看边过滤。</p>']
    for g in MUST_GROUPS:
        items = [x for x in MUST if x[2] == g]
        if not items:
            continue
        parts.append('<div class="mg"><div class="mgt">%s</div><div class="links">' % esc(g))
        for a, label, _, d, _ in items:
            cls = ' class="cross"' if d != doc_key else ''
            parts.append('<a%s href="%s">%s</a>' % (cls, esc(must_href(a, doc_key)), esc(label)))
        parts.append('</div></div>')
    parts.append('</section>')
    return ''.join(parts)


def toc_block(doc_key, toc):
    h = ['<div class="toc-title">目录 · 点击跳转 / 可过滤</div>',
         '<input id="tocFilter" placeholder="过滤目录、速达项、章节…" autocomplete="off">',
         '<nav class="toc"><ul>',
         '<li class="grp">⚡ 必背速达（背诵 / 随时要查）</li>']
    for a, label, scene, d, _ in MUST:
        h.append('<li data-s="%s %s 必背速达"><a class="quick" href="%s">%s</a></li>'
                 % (esc(label), esc(scene), esc(must_href(a, doc_key)), esc(label)))
    h.append('<li class="grp">📖 正文目录</li>')
    for lvl, hid, txt in toc:
        h.append('<li data-s="%s"><a class="lv%d" href="#%s">%s</a></li>'
                 % (esc(txt), lvl, hid, esc(txt)))
    h.append('</ul><div class="grp">🔗 离线册页互跳</div><div class="cross">')
    px = PREFIX[doc_key]
    h.append('<a href="%sindex.html">总入口</a>' % px)
    h.append('<a href="%s%s">主手册</a>' % (px, MAIN_HTML))
    h.append('<a href="%s%s">速查手册</a>' % (px, QUICK_HTML))
    h.append('<a href="%s%s">开源课程精读</a>' % (px, BOOK3_HTML))
    h.append('<a href="%s%s">术语词典</a>' % (px, GLOSS_HTML))
    h.append('<a href="%s%s">📝 考核题库</a>' % (px, QUIZ_HTML))
    h.append('<a href="%s%s">🎯 手册展示</a>' % (px, SHOW_HTML))
    h.append('<a href="%s%s#anchor-examtypes">🧾 两类选择题</a>' % (px, MAIN_HTML))
    h.append('<a href="%s%s#anchor-selection">国内选型</a>' % (px, MAIN_HTML))
    h.append('<a href="%s%s#anchor-model">模型选型</a>' % (px, MAIN_HTML))
    h.append('<a href="%s%s#anchor-tts">语音 TTS</a>' % (px, MAIN_HTML))
    h.append('<a href="%s%s#anchor-openbook">开源精读</a>' % (px, BOOK3_HTML))
    h.append('<a href="%s%s#anchor-reading">扩展阅读</a>' % (px, MAIN_HTML))
    h.append('<a href="%s%s#anchor-figures">图示索引</a>' % (px, MAIN_HTML))
    h.append('<a href="%s%s#anchor-catalog">最终目录</a>' % (px, MAIN_HTML))
    h.append('<a href="%s参考资料/逐节笔记索引.html">19 节笔记</a>' % px)
    h.append('</div></nav>')
    return ''.join(h)


def render(md_text, doc_key, title, badge, subtitle, pills, expect_must=True):
    lines = md_text.split('\n')
    out, toc, cover_lines = [], [], []
    i, n, sec, first_h1 = 0, len(lines), 0, True
    ask_on = doc_key in ('main', 'quick', 'book3')
    injected = set()
    expected = {a for a, _, _, d, _ in MUST if d == doc_key} if expect_must else set()

    while i < n:
        line = lines[i]
        s = line.strip()

        if s.startswith('<!--FIGURE:'):
            key = s[len('<!--FIGURE:'):].split('-->')[0].strip()
            if key in figure_data.FIGURES:
                svg, cap = figure_data.FIGURES[key]
                out.append('<figure class="figure">%s<figcaption>%s</figcaption></figure>'
                           % (svg, esc(cap)))
            else:
                out.append('<p class="img-missing">［图示 %s 未收录］</p>' % esc(key))
            i += 1
            continue

        if s.startswith('```'):
            lang = s[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith('```'):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append('<pre><code>%s</code></pre>' % ihtml.escape('\n'.join(buf), quote=False))
            continue

        m = re.match(r'^(#{1,4})\s+(.*)$', s)
        if m:
            lvl = len(m.group(1))
            raw = m.group(2)
            txt = inline(raw, doc_key)
            plain = re.sub(r'<[^>]+>', '', raw)
            plain = re.sub(r'[*`\[\]]', '', plain)
            if lvl == 1 and first_h1:
                first_h1 = False
                cover_lines.append(plain.strip())
                i += 1
                continue
            sec += 1
            hid = 'sec-%d' % sec
            extra = ''
            if expect_must:
                for a, _, _, d, key in MUST:
                    if d == doc_key and a not in injected and key in plain:
                        extra += '<span class="anchor-flag" id="%s"></span>' % a
                        injected.add(a)
            ask_btn = ''
            if ask_on:
                mid = ASK_BY_SEC.get((doc_key, sec))
                if mid:
                    ask_btn = ('<button type="button" class="ask-btn" data-ask="%s" '
                               'title="生成一段自带上下文的追问提示词，复制后可粘贴到任意 AI">'
                               '细节追问</button>' % mid)
            out.append('%s<h%d id="%s">%s%s</h%d>'
                       % (extra, lvl, hid, txt, ask_btn, lvl))
            if lvl <= 3:
                toc.append((lvl, hid, plain.strip()))
            i += 1
            continue

        if s.startswith('> '):
            buf = []
            while i < n and lines[i].strip().startswith('>'):
                buf.append(lines[i].strip().lstrip('>').strip())
                i += 1
            body = ''.join('<p>%s</p>' % inline(x, doc_key) for x in buf if x)
            out.append('<blockquote>%s</blockquote>' % body)
            continue

        if re.match(r'^-{3,}$', s):
            out.append('<hr>')
            i += 1
            continue

        if s.startswith('|') and i + 1 < n and is_sep(lines[i + 1]):
            head = split_row(lines[i])
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith('|'):
                rows.append(split_row(lines[i]))
                i += 1
            th = ''.join('<th>%s</th>' % inline(c, doc_key) for c in head)
            tb = ''
            for r in rows:
                cells = (r + [''] * len(head))[:len(head)]
                tb += '<tr>' + ''.join('<td>%s</td>' % inline(c, doc_key) for c in cells) + '</tr>'
            out.append('<div class="tablewrap"><table><thead><tr>%s</tr></thead>'
                       '<tbody>%s</tbody></table></div>' % (th, tb))
            continue

        if re.match(r'^\s*(-|\*|\d+\.)\s+', line):
            ordered = bool(re.match(r'^\s*\d+\.\s+', line))
            items = []
            while i < n and re.match(r'^\s*(-|\*|\d+\.)\s+', lines[i]):
                it = re.sub(r'^\s*(-|\*|\d+\.)\s+', '', lines[i]).rstrip()
                it = re.sub(r'^\[ \]\s*', '☐ ', it)
                it = re.sub(r'^\[x\]\s*', '☑ ', it)
                items.append('<li>%s</li>' % inline(it, doc_key))
                i += 1
            tag = 'ol' if ordered else 'ul'
            out.append('<%s>%s</%s>' % (tag, ''.join(items), tag))
            continue

        if s == '':
            i += 1
            continue

        out.append('<p>%s</p>' % inline(s, doc_key))
        i += 1

    missing = expected - injected
    if missing:
        print('  WARN %s 速达锚点未命中标题: %s' % (doc_key, ', '.join(sorted(missing))))

    cover_title = cover_lines[0] if cover_lines else title
    px = PREFIX[doc_key]
    pill_html = ''.join('<span class="pill">%s</span>' % esc(p) for p in pills)
    jump = ('<div class="jump"><a href="%sindex.html">📚 离线总入口</a>'
            '<a href="%s%s">📖 主手册</a><a href="%s%s">⚡ 速查手册</a>'
            '<a href="%s%s">📗 开源精读</a>'
            '<a href="%s%s">🔤 术语词典</a>'
            '<a href="%s%s#anchor-quiz">📝 考核题库</a>'
            '<a href="%s%s#anchor-showcase">🎯 手册展示</a>'
            '<a href="%s%s">🔍 细节追问</a>'
            '<a href="%s%s#anchor-catalog">🗂 最终目录</a>'
            '<a href="%s参考资料/逐节笔记索引.html">📚 19 节笔记</a></div>'
            % (px, px, MAIN_HTML, px, QUICK_HTML, px, BOOK3_HTML, px, GLOSS_HTML,
               px, QUIZ_HTML, px, SHOW_HTML, px, ASK_HTML,
               px, MAIN_HTML, px))
    cover = ('<div class="cover"><div class="kicker">%s · ENTERPRISE AGENT DELIVERY · %s</div>'
             '<h1>%s</h1><p class="sub">%s</p><div class="meta">%s</div>%s</div>'
             % (esc(badge), VERSION, esc(cover_title), esc(subtitle), pill_html, jump))

    top = ('<div class="topbar">'
           '<button class="btn" id="menuBtn" title="打开目录">☰</button>'
           '<span class="brand">企业智能体交付 · FDE</span><span class="sep">/</span>'
           '<span class="docname">%s</span><span class="spacer"></span>'
           '<a class="btn hide-sm" href="%sindex.html">总入口</a>'
           '<a class="btn hide-sm" href="%s%s">主手册</a>'
           '<a class="btn hide-sm" href="%s%s">速查</a>'
           '<a class="btn hide-sm" href="%s术语词典.html">📖 术语</a>'
           '<a class="btn hide-sm" href="%s%s">📝 题库</a>'
           '<button class="btn on" id="mustBtn" title="跳到必背速达">⚡ 速达</button>'
           '<button class="btn" id="themeBtn" title="切换深浅色">🌙</button>'
           '<button class="btn" id="fsMinus" title="缩小字号">A−</button>'
           '<button class="btn" id="fsPlus" title="放大字号">A＋</button>'
           '<button class="btn" id="printBtn">打印 / PDF</button></div>'
           % (esc(title), px, px, MAIN_HTML, px, QUICK_HTML, px, px, QUIZ_HTML))

    layout = ('<div class="layout">'
              '<aside class="sidebar" id="sidebar"><div class="drawer-head"><span>目录 / 速达</span>'
              '<button id="drawerClose">关闭 ✕</button></div>%s</aside>'
              '<div class="drawer-mask" id="drawerMask"></div>'
              '<div class="main"><article class="content">%s%s%s'
              '<div class="footer">本手册为独立学习整理，非官方题库；'
              '正文中出现的产品与开源项目名称仅为公开资料举例，不构成推荐或采购建议；'
              '平台功能、许可与规格以当期官方文档为准。'
              '本页为离线自包含 HTML：样式、脚本、术语数据与全部图示均内嵌，无 CDN、无外部图片、无网络请求；'
              '正文中的资料出处链接不自动加载。</div>'
              '</article></div></div>'
              % (toc_block(doc_key, toc), cover, must_cards(doc_key), '\n'.join(out)))

    pop_html = TERM_POP_HTML.replace('__GLOSS_HREF__', px + GLOSS_HTML + '#anchor-glossary')
    tpl = ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
           '<meta name="color-scheme" content="light dark">'
           '<title>__TITLE__</title>' + HEAD_SCRIPT + '<style>__CSS__</style></head><body>'
           '<div id="progress"></div>__TOP____LAYOUT____TERMPOP____ASKPOP__'
           '<button class="totop" id="totop" title="回到顶部">↑</button>'
           '<script>__JS__</script></body></html>')
    ask_js = ('\nwindow.__FDE_ASK__=%s;\n%s'
              % (ask_json_for(doc_key), prompt_data.ASK_JS)) if ask_on else ''
    doc = (tpl.replace('__TITLE__', esc(title))
              .replace('__CSS__', CSS + (prompt_data.ASK_CSS if ask_on else ''))
              .replace('__JS__', JS.replace('__GLOSSARY_DATA__', GLOSSARY_JSON) + ask_js)
              .replace('__TOP__', top)
              .replace('__LAYOUT__', layout)
              .replace('__TERMPOP__', pop_html)
              .replace('__ASKPOP__', prompt_data.ASK_POP_HTML if ask_on else ''))
    return doc, toc, injected


# ---------------- 术语词典.html（独立可检索页） ----------------
GLOSS_CSS = r"""
:root{--bg:#f5f5f7;--card:#fff;--text:#1d1d1f;--text-2:#424245;--muted:#6e6e73;
--line:#e5e5ea;--line-2:#d2d2d7;--accent:#0071e3;--accent-soft:#eaf3ff;--soft:#fafafa;
--fs:16px;--shadow:0 8px 30px rgba(0,0,0,.07)}
html[data-theme="dark"]{--bg:#16181d;--card:#20232a;--text:#f2f2f5;--text-2:#c9ccd3;
--muted:#9297a2;--line:#2f333c;--line-2:#3d424d;--accent:#63adff;--accent-soft:#172c47;
--soft:#1a1d23;--shadow:0 8px 30px rgba(0,0,0,.45)}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font-size:var(--fs);line-height:1.7;
font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","PingFang SC","Microsoft YaHei",sans-serif;
-webkit-font-smoothing:antialiased;-webkit-text-size-adjust:100%}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1000px;margin:0 auto;padding:24px 20px 70px}
.hero{background:linear-gradient(135deg,var(--accent-soft) 0%,var(--soft) 60%,var(--card) 100%);
border:1px solid var(--line);border-radius:22px;padding:32px 34px;margin-bottom:20px}
.hero .k{font-size:11.5px;font-weight:700;letter-spacing:.14em;color:var(--accent)}
.hero h1{font-size:31px;line-height:1.3;margin:11px 0 9px;letter-spacing:-.02em}
.hero p{color:var(--muted);margin:0;font-size:14px}
.pills{display:flex;flex-wrap:wrap;gap:7px;margin-top:18px}
.pills span{font-size:12px;background:var(--card);border:1px solid var(--line);border-radius:999px;padding:5px 12px;color:var(--text-2)}
.nav{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px}
.nav a,.nav button{font-size:12.5px;border:1px solid var(--line);border-radius:9px;padding:6px 12px;
background:var(--card);color:var(--text-2);font-family:inherit;cursor:pointer}
.nav a:hover,.nav button:hover{border-color:var(--accent);color:var(--accent);text-decoration:none}
.tools{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 18px;margin-bottom:18px;box-shadow:var(--shadow)}
#q{width:100%;padding:10px 14px;border:1px solid var(--line);border-radius:10px;background:var(--bg);
color:var(--text);font-size:14px;outline:none;font-family:inherit}
#q:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.cats{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
.cats button{font-size:12.2px;border:1px solid var(--line);border-radius:999px;padding:5px 11px;
background:var(--bg);color:var(--text-2);cursor:pointer;font-family:inherit}
.cats button:hover{border-color:var(--accent)}
.cats button.on{background:var(--accent-soft);border-color:var(--accent);color:var(--accent);font-weight:700}
.count{font-size:12.5px;color:var(--muted);margin-top:11px}
.list{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.gcard{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;box-shadow:var(--shadow)}
.gh{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px}
.gk{font-size:17px;font-weight:700;color:var(--accent);letter-spacing:-.01em}
.gc{font-size:11px;color:var(--muted);background:var(--bg);border:1px solid var(--line);border-radius:999px;padding:2px 9px}
.gfull{font-size:12.5px;color:var(--muted);margin-bottom:10px}
.gsec{font-size:13.3px;color:var(--text-2);margin:6px 0}
.gsec b{font-size:11.3px;color:var(--muted);letter-spacing:.05em;display:block;margin-bottom:1px;font-weight:700}
.grel{margin-top:11px;padding-top:9px;border-top:1px solid var(--line);font-size:12.3px;color:var(--muted)}
.grel button{font:inherit;font-size:12px;margin:3px 4px 0 0;border:1px solid var(--line);border-radius:999px;
padding:3px 9px;background:var(--bg);color:var(--accent);cursor:pointer}
.grel button:hover{border-color:var(--accent);background:var(--accent-soft)}
.grel span{margin-right:6px}
.foot{margin-top:28px;color:var(--muted);font-size:12.5px;text-align:center;line-height:1.8}
@media(max-width:760px){.wrap{padding:14px 12px 50px}.hero{padding:24px 18px}.hero h1{font-size:24px}
.list{grid-template-columns:1fr}.tools{padding:13px}}
@media print{.nav,.tools,.cats,#q{display:none!important}.list{grid-template-columns:repeat(2,1fr)}
.gcard{box-shadow:none;page-break-inside:avoid}.hero{background:#fff}}
"""

GLOSS_JS = r"""
(function(){
  var root=document.documentElement, q=document.getElementById('q'),
      list=document.getElementById('list'), count=document.getElementById('count'),
      cards=[].slice.call(list.querySelectorAll('.gcard')), cur='全部';
  function run(){
    var v=(q.value||'').trim().toLowerCase(), n=0;
    cards.forEach(function(c){
      var ok=(cur==='全部'||c.getAttribute('data-cat')===cur) &&
             (!v||c.getAttribute('data-s').toLowerCase().indexOf(v)>-1);
      c.style.display=ok?'block':'none'; if(ok)n++;
    });
    count.textContent='显示 '+n+' / '+cards.length+' 条词条';
  }
  q.addEventListener('input',run);
  var box=document.getElementById('cats');
  box.addEventListener('click',function(e){
    var b=e.target; while(b&&b!==box&&b.tagName!=='BUTTON')b=b.parentNode;
    if(!b||b.tagName!=='BUTTON')return;
    cur=b.getAttribute('data-cat');
    box.querySelectorAll('button').forEach(function(x){x.classList.toggle('on',x===b);});
    run();
  });
  function jump(key){
    cur='全部';q.value='';
    box.querySelectorAll('button').forEach(function(x){x.classList.toggle('on',x.getAttribute('data-cat')==='全部');});
    run();
    var t=null;
    cards.forEach(function(c){if(c.getAttribute('data-key')===key)t=c;});
    if(t){t.scrollIntoView({behavior:'smooth',block:'center'});
      t.style.transition='box-shadow .3s';t.style.boxShadow='0 0 0 3px var(--accent-soft)';
      setTimeout(function(){t.style.boxShadow='';},1800);}
  }
  list.addEventListener('click',function(e){
    var b=e.target; while(b&&b!==list&&b.tagName!=='BUTTON')b=b.parentNode;
    if(b&&b.tagName==='BUTTON'&&b.getAttribute('data-jump'))jump(b.getAttribute('data-jump'));
  });
  var tb=document.getElementById('themeBtn');
  function paint(){var d=root.getAttribute('data-theme')==='dark';if(tb)tb.textContent=d?'☀️':'🌙';}
  if(tb)tb.addEventListener('click',function(){
    var d=root.getAttribute('data-theme')==='dark';
    root.setAttribute('data-theme',d?'light':'dark');
    try{localStorage.setItem('fde-theme',d?'light':'dark');}catch(e){}
    paint();
  });
  paint(); run();
  if(location.hash.indexOf('#term-')===0){
    var el=document.getElementById(location.hash.slice(1));
    if(el)setTimeout(function(){el.scrollIntoView({block:'center'});},60);
  }
})();
"""


def build_glossary_page():
    cats = glossary_data.CATEGORIES
    order = {c: i for i, c in enumerate(cats)}
    pairs = sorted(glossary_data.GLOSSARY.items(),
                   key=lambda kv: (order.get(kv[1][1], 99), kv[0]))
    cards = []
    for idx, (k, v) in enumerate(pairs, 1):
        full, cat, definition, why, related = v
        rel = []
        for r in re.split(r'[,，、]', related):
            r = r.strip()
            if not r:
                continue
            if r in glossary_data.GLOSSARY:
                rel.append('<button type="button" data-jump="%s">%s</button>' % (esc(r), esc(r)))
            else:
                rel.append('<span>%s</span>' % esc(r))
        search = ' '.join([k, full, cat, definition, why, related]).lower()
        cards.append(
            '<article class="gcard" id="term-%d" data-key="%s" data-cat="%s" data-s="%s">'
            '<div class="gh"><span class="gk">%s</span><span class="gc">%s</span></div>'
            '<div class="gfull">%s</div>'
            '<div class="gsec"><b>是什么</b>%s</div>'
            '<div class="gsec"><b>交付里为什么重要</b>%s</div>'
            '<div class="grel">相关词条：%s</div></article>'
            % (idx, esc(k), esc(cat), esc(search), esc(k), esc(cat),
               esc(full), esc(definition), esc(why), ''.join(rel)))

    cat_counts = {}
    for k, v in glossary_data.GLOSSARY.items():
        cat_counts[v[1]] = cat_counts.get(v[1], 0) + 1
    btns = ['<button class="on" data-cat="全部">全部 %d</button>' % len(pairs)]
    for c in cats:
        btns.append('<button data-cat="%s">%s %d</button>' % (esc(c), esc(c), cat_counts.get(c, 0)))

    doc = ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
           '<meta name="color-scheme" content="light dark">'
           '<title>术语词典 · 专业名词 / 英文 / 英文缩写 | 企业级智能体交付</title>'
           + HEAD_SCRIPT + '<style>' + GLOSS_CSS + '</style></head><body><div class="wrap">'
           '<div class="hero" id="anchor-glossary"><div class="k">GLOSSARY · OFFLINE · %s</div>'
           '<h1>术语词典｜专业名词 · 英文 · 英文缩写</h1>'
           '<p>三册正文中带<b>虚线标记</b>的词条，点击即可查看：英文全称 / 中文全称、所属分类、定义、'
           '在企业交付里为什么重要、相关词条。本页可离线检索全部词条，也可按分类逐类背诵。</p>'
           '<div class="pills"><span>共 %d 条</span><span>%d 个分类</span>'
           '<span>逐条给出英文 / 缩写全称</span><span>相关词条可互跳</span>'
           '<span>零外部资源 · 深浅主题</span><span>手机 / 电脑可读</span></div></div>'
           '<div class="nav"><a href="index.html">📚 总入口</a>'
           '<a href="01_主手册.html">📖 主手册</a><a href="02_速查手册.html">⚡ 速查手册</a>'
           '<a href="%s">📗 开源精读</a>'
           '<a href="01_主手册.html#anchor-catalog">🗂 科学化最终目录</a>'
           '<a href="01_主手册.html#anchor-selection">🧭 国内方案选型</a>'
           '<a href="%s">📝 考核题库</a>'
           '<a href="%s">🎯 手册展示</a>'
           '<button id="themeBtn" title="切换深浅色">🌙</button></div>'
           '<div class="tools"><input id="q" placeholder="搜索词条 / 英文全称 / 释义关键词，例如 RAG、幂等、越权、许可…" autocomplete="off">'
           '<div class="cats" id="cats">%s</div><div class="count" id="count"></div></div>'
           '<div class="list" id="list">%s</div>'
           '<div class="foot">本词典为独立学习整理，词条定义用于本手册语境下的理解与讲解；'
           '产品规格、许可条款与合规资质以所选用产品的当期官方文档为准。<br>'
           '产品与开源项目名称仅为公开资料举例，不构成推荐、排名或采购建议。</div>'
           '</div><script>%s</script></body></html>'
           % (VERSION, len(pairs), len(cats), BOOK3_HTML, QUIZ_HTML, SHOW_HTML,
              ''.join(btns), ''.join(cards), GLOSS_JS))
    doc = site_chrome.inject(
        doc, 'lookup',
        [('门户', 'index.html'), ('介绍', '手册展示页.html'),
         ('查阅', None), ('术语词典', None)],
        title='术语词典 | 专业名词 / 英文 / 英文缩写',
        description='%d 条专业名词、英文与英文缩写，含全称、分类、定义、交付意义与相关词条。'
                    % len(glossary_data.GLOSSARY))
    (BASE / GLOSS_HTML).write_text(doc, encoding='utf-8')
    return len(pairs)


# ---------------- index.html ----------------
INDEX_CSS = r"""
:root{--bg:#f5f5f7;--card:#fff;--text:#1d1d1f;--text-2:#424245;--muted:#6e6e73;
--line:#e5e5ea;--accent:#0071e3;--accent-soft:#eaf3ff;--fs:16px;--shadow:0 8px 30px rgba(0,0,0,.07)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-size:var(--fs);line-height:1.7;
font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","PingFang SC","Microsoft YaHei",sans-serif;
-webkit-font-smoothing:antialiased;-webkit-text-size-adjust:100%}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1000px;margin:0 auto;padding:28px 20px 70px}
.hero{background:linear-gradient(135deg,#eaf3ff 0%,#fafafa 60%,#fff 100%);
border:1px solid var(--line);border-radius:22px;padding:38px 36px;margin-bottom:24px}
.hero .k{font-size:11.5px;font-weight:700;letter-spacing:.14em;color:var(--accent)}
.hero h1{font-size:34px;line-height:1.28;margin:12px 0 10px;letter-spacing:-.02em}
.hero p{color:var(--muted);margin:0;font-size:14.5px}
.hero .pills{display:flex;flex-wrap:wrap;gap:7px;margin-top:20px}
.hero .pills span{font-size:12px;background:#fff;border:1px solid var(--line);border-radius:999px;padding:5px 12px;color:var(--text-2)}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.card{display:block;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:22px 22px 20px;
box-shadow:var(--shadow);color:var(--text)}
.card:hover{border-color:var(--accent);text-decoration:none;transform:translateY(-1px);transition:.15s}
.card .ic{font-size:26px}.card h2{font-size:18px;margin:8px 0 6px}.card p{font-size:13px;color:var(--muted);margin:0 0 12px}
.card .go{font-size:12.5px;color:var(--accent);font-weight:650}
.card.wide{grid-column:1/-1}
h2.sec{font-size:20px;margin:34px 0 12px;padding-bottom:10px;border-bottom:1px solid var(--line)}
.tocstrip{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 20px;
margin-bottom:22px;box-shadow:var(--shadow)}
.tocstrip .k{font-size:11.5px;font-weight:700;letter-spacing:.12em;color:var(--accent);margin-bottom:9px}
.tocstrip .row{display:flex;flex-wrap:wrap;gap:8px}
.tocstrip a{font-size:12.8px;border:1px solid var(--line);border-radius:999px;padding:6px 13px;
background:var(--bg);color:var(--text-2)}
.tocstrip a:hover{border-color:var(--accent);color:var(--accent);text-decoration:none}
.sect{margin-top:30px;scroll-margin-top:16px}
.sect>.sh{display:flex;align-items:baseline;gap:10px;margin:0 0 5px}
.sect>.sh .num{font-size:22px;font-weight:800;color:var(--accent);letter-spacing:-.02em}
.sect>.sh h2{font-size:20px;margin:0;padding:0;border:0}
.sect>.si{font-size:13px;color:var(--muted);margin:0 0 13px}
.card.hl{border-color:var(--accent);background:linear-gradient(135deg,var(--accent-soft),var(--card) 70%)}
.card .badge{display:inline-block;font-size:10.5px;font-weight:700;color:#fff;background:var(--accent);
border-radius:999px;padding:2px 8px;margin-left:7px;vertical-align:2px}
.note{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px 24px;box-shadow:var(--shadow)}
.note ul{padding-left:20px;color:var(--text-2);font-size:14px}.note li{margin:6px 0}
.note code{background:var(--accent-soft);border-radius:5px;padding:1px 5px;font-size:.88em;color:var(--accent)}
.lessons{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px}
.lessons a{display:block;font-size:12.5px;background:var(--card);border:1px solid var(--line);
border-radius:9px;padding:8px 11px;color:var(--text-2)}
.lessons a:hover{border-color:var(--accent);text-decoration:none;color:var(--accent)}
.files{font-size:13px;color:var(--text-2);line-height:1.9}
.files b{color:var(--text)}
.foot{margin-top:34px;color:var(--muted);font-size:12.5px;text-align:center}
@media(max-width:720px){.wrap{padding:16px 13px 50px}.hero{padding:26px 20px}.hero h1{font-size:25px}
.grid{grid-template-columns:1fr}.card.wide{grid-column:auto}.lessons{grid-template-columns:repeat(2,1fr)}}
@media(max-width:420px){.lessons{grid-template-columns:1fr}}
@media print{.card{box-shadow:none}.hero{background:#fff}}
"""


def lesson_key(p):
    m = re.match(r'^(\d+)\.(\d+)', p.name)
    if not m:
        return (99, 99, 0)
    tail = p.name[m.end():m.end() + 1]
    return (int(m.group(1)), int(m.group(2)), {'上': 1, '中': 2, '下': 3}.get(tail, 0))


def prepare_lessons():
    """把 19 节逐节笔记复制为本地副本，并生成双端 HTML + 索引。"""
    if not SRC_LESSONS.exists():
        print('WARN 未找到逐节笔记源目录 %s，跳过本地化' % SRC_LESSONS)
        return []
    LESSONS.mkdir(parents=True, exist_ok=True)
    srcs = sorted([p for p in SRC_LESSONS.glob('*.md')], key=lambda p: p.name)
    rows = []
    for idx, p in enumerate(srcs, 1):
        stem = 'lesson-%02d' % idx
        dst_md = LESSONS / (stem + '.md')
        raw = p.read_text(encoding='utf-8')
        title = re.sub(r'^#\s*', '', raw.split('\n', 1)[0]).strip() or p.stem
        # 索引页/封面标题做厂商中立化；笔记正文保留原始资料表述（见离线使用说明）
        title = (title.replace('ADP', '智能体平台').replace('腾讯云', '')
                     .replace('Tencent Cloud', '').replace('智能体平台平台', '智能体平台'))
        doc, _, _ = render(raw, 'lesson', title, '逐节笔记',
                           '课程逐节笔记离线副本 · %s' % p.stem,
                           ['第 %d / %d 节' % (idx, len(srcs)), '离线自包含', '双端可读'],
                           expect_must=False)
        doc = site_chrome.inject(
            doc, 'learn',
            [('门户', 'index.html'), ('介绍', '手册展示页.html'),
             ('学习', '01_主手册.html'), ('逐节笔记', '参考资料/逐节笔记索引.html'),
             (title, None)], px='../../',
            title=title + ' | 逐节笔记',
            description='课程逐节笔记离线副本，用于对照主手册核验知识点。')
        lm = prompt_data.lesson_module(stem, title, VERSION, body=raw)
        btn = ('<div class="ask-entry"><button type="button" class="ask-btn" '
               'data-ask="%s" title="把这一节拿去问任意 AI">细节追问：拿这一节去问 AI'
               '</button></div>' % lm['id'])
        doc = attach_ask(doc, prompt_data.payload([lm], VERSION), btn)
        (LESSONS / (stem + '.html')).write_text(doc, encoding='utf-8')
        rows.append((idx, title, stem, p.name))
    return rows


def build_lesson_index(rows):
    items = ''.join('<a href="课程逐节笔记/lesson-%02d.html">%02d · %s</a>' % (i, i, esc(t))
                    for i, t, _, _ in rows)
    doc = ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width,initial-scale=1">'
           '<title>19 节课程逐节笔记 · 离线索引</title><style>%s</style></head><body>'
           '<div class="wrap"><div class="hero"><div class="k">OFFLINE REFERENCE</div>'
           '<h1>19 节课程逐节笔记 · 离线索引</h1>'
           '<p>课程 4 章 19 节的逐节学习笔记本地副本。点击任意一节进入双端阅读版；'
           '同目录另有 <code>.md</code> 原文，可离线检索与复制。</p>'
           '<div class="pills"><span>4 章 19 节</span><span>HTML + Markdown 双份</span>'
           '<span>无外部资源</span><span>手机 / 电脑可读</span></div></div>'
           '<h2 class="sec">逐节目录</h2><div class="lessons">%s</div>'
           '<h2 class="sec">返回</h2><div class="note"><ul>'
           '<li><a href="../index.html">📚 离线总入口</a></li>'
           '<li><a href="../01_主手册.html">📖 主手册</a> ｜ '
           '<a href="../02_速查手册.html">⚡ 速查手册</a></li>'
           '<li>原文路径：<code>参考资料/课程逐节笔记/lesson-01.md … lesson-19.md</code></li>'
           '</ul></div><div class="foot">逐节笔记为公开学习资料本地副本，版权归原权利人所有；'
           '仅用于本手册对照核验，不替代官方课程。</div></div></body></html>'
           % (INDEX_CSS, items))
    doc = site_chrome.inject(
        doc, 'learn',
        [('门户', 'index.html'), ('介绍', '手册展示页.html'),
         ('学习', '01_主手册.html'), ('逐节笔记索引', None)], px='../',
        title='19 节课程逐节笔记索引 | 企业级智能体交付实战手册',
        description='4 章 19 节逐节笔记的离线索引，HTML 与 Markdown 双份。')
    (REF / '逐节笔记索引.html').write_text(doc, encoding='utf-8')


def build_index(rows):
    """产品级入口门户：委托 site_pages.portal_doc（L0）。"""
    img_n = len(list((REF / 'images').rglob('*.png'))) if (REF / 'images').exists() else 0
    doc = site_pages.portal_doc(
        img_n=img_n,
        q_total=question_bank_data.STATS['total'],
        terms=len(glossary_data.GLOSSARY),
        figs=len(figure_data.FIGURES),
        must=len(MUST),
        rows=40,
        ask_n=len(ASK_MODULES),
        domains=len(question_bank_data.DOMAINS),
        cats=len(glossary_data.CATEGORIES))
    (BASE / 'index.html').write_text(doc, encoding='utf-8')


OFFLINE_GUIDE = """# 离线使用说明 · 企业级智能体交付实战手册 v5.0

> 本资源包的目标：**不联网、不安装、不登录，手机和电脑都能完整阅读、检索、追问与自测。**
> 内容是**跨行业、厂商中立**的企业级智能体交付能力体系，适用于零售 / 制造 / 金融 / 医疗 / 教育 / 政务 / 能源 / 物流 / 法律 / 汽车 / 媒体等所有需要把智能体接入真实业务流程的行业。

---

## 1. 最快开始

| 设备 / 来意 | 做法 |
| --- | --- |
| 电脑（Windows / macOS / Linux） | 双击 `index.html`。v5.0 首页为**扁平化设计**：大字号标题、纯色块、无渐变阴影，带滚动进场、吸顶分区导航、阅读进度与回到顶部。 |
| Android 手机 | 整个文件夹拷进手机存储，文件管理器点 `index.html` → 用 Chrome 等浏览器打开（`file://` 可直接运行）。 |
| iPhone / iPad | 文件夹存进「文件」App，用支持本地 HTML 的 App 打开；或只拷单个 `.html` 文件预览。 |
| 只想看一册 | 三册阅读版 HTML 都是**单文件自包含**，单独拷走 `01_主手册.html` / `02_速查手册.html` / `03_开源课程解读.html` 也能完整阅读（跨册与笔记链接此时失效，其余功能都在）。 |
| 只想做题 | `FDE工程师考核题库.html` 单文件自包含；进度与错题本只写本地浏览器。 |
| 想打印 | 任一册右上角「打印 / PDF」；题库页「打印 / PDF（含答案页）」生成带答案页的纸质试卷；门户与介绍页打印时自动隐藏导航与动效。 |

如果手机浏览器限制本地文件互跳，可在电脑上于本目录执行 `python3 -m http.server 8000`，手机连同一 Wi-Fi 访问 `http://电脑IP:8000/index.html` —— 走局域网，仍不依赖公网。

---

## 2. 三层信息架构、全站导航与「必背速达」

**三层信息架构**：`L0 入口门户 → L1 手册介绍 → L2 详细内容`。门户负责品牌、价值、导航分布与来意分流；介绍页讲清能力体系与边界；L2 分为「学习 / 查阅 / 考核 / 资料」四个板块，「细节追问」是横切在每个学习点上的能力。三层图见 `站点地图.html`。

各层页面都带**同一条顶部主导航 + 面包屑 + 站点地图入口 + 页脚站点地图**，当前栏目高亮；手机端主导航折叠为 ☰ 菜单。v5.0 首页另加**吸顶分区导航**（滚动时自动高亮当前分区）与**顶部阅读进度条**。

| 分区 | 解决什么来意 | 主要入口 |
| --- | --- | --- |
| 01 认识 | 第一次打开、要向别人介绍 | 手册展示页、主手册、数据条 |
| 02 从哪开始 | 我下一步该做什么 | 14 步路径、40 行最终目录、19 节笔记、第三册精读 |
| 03 导航分布 | 这套资料怎么组织、怎么找 | IA 图、站点地图、八种来意分流 |
| 04 按路径学习 | 逐章学、逐节核验 | 主手册、速查、开源课程精读 |
| 05 查阅与考核 | 查词、看图、讲清、做题 | 术语词典、图示索引、题库、追问库 |
| 06 技术补强 | 模型 / Agent / 语音 / 行业怎么选 | 第十一～十四篇、M/O/P/Q 速查组 |
| 07 资料与上线 | 是否完整、怎么部署 | 离线说明、核验报告、站点地图、缺口清单 |

本包给了八条内容入口，覆盖「从零开始学」到「查词、看图、评审、讲清、考核、复盘、追问」：

1. **分步学习路径**：主手册 0.4 的 **14 步四阶段**清单，照着 Step 1 → Step 14 打勾，每步有产出物与完成判据；排复习顺序用**附录 F 的 40 行最终目录总表**。
2. **术语点击释义**：三册正文中带**虚线下划线**的专业名词 / 英文 / 英文缩写，点一下弹出「英文全称 / 分类 / 定义 / 交付里为什么重要 / 相关词条」，相关词条可继续点；完整 **__TERMS__ 条 / 11 个分类**见独立《术语词典.html》，可离线检索。v5.0 新增模型推理、Agent 工程、语音 TTS 与开源课程相关词条。
3. **8 张内联图示 + 站点 3 张图**：0.4 学习路径、3.1 项目 A 演进与架构、5.7 项目 B 合规闸门、5.8 项目 C 知识集成、8.4 白板七层、9.4 选型四象限、附录 F.2 认知分层；门户 / 介绍 / 站点地图另有 3 张。全部由 `chart_engine.py` **声明式编译**：只描述节点与关系，坐标由布局器推导，用真实中文字体测量自动换行、自动定框高与 viewBox、正交连线不穿节点；零 JS / 零外链，随深浅主题变色、可打印；窄屏保持整图完整可见（等比缩放），不裁切。
4. **顶部 ⚡ 速达按钮**：直接滚到封面下的「必背速达 · **__MUST__ 个必要知识点**」网格，按九个场景分组（从零开始学 / 考前 10 分钟 / 平台配置前 / 方案评审前 / 要讲给别人听 / 排障现场 / 上线与验收 / 验收签字 / 复盘核验）。
5. **目录第一个分组**：电脑左侧栏与手机抽屉目录顶部都是同一份速达清单；目录底部有「考核题库 / 手册介绍 / 题型判分 / 术语词典 / 开源精读 / 国内选型 / 模型选型 / TTS 选型 / 扩展阅读 / 图示索引 / 最终目录」互跳链接。
6. **考核题库**：独立做题，支持打乱、筛选、三种模式、错题本与成绩单；判分口径见主手册 10.5.1、速查 N1。
7. **细节追问**：三册每个标题、19 节笔记都能点「🔍 细节追问」，复制一段自带上下文的提示词到任意 AI 继续深挖（见第 10 节）。
8. **目录过滤框**：输入关键词（如 `题型`、`模型`、`TTS`、`Agent`、`开源`、`行业`、`变量`、`导入`、`诊断`、`上线`、`公式`、`覆盖`、`选型`、`缺口`、`许可`）即时过滤目录与速达项。

带 **↗** 的速达项属于另一册 / 另一页，点击通过相对路径跨页跳转，离线同样有效。全站顶部栏目导航由 `site_chrome.py` 统一注入。

---

## 3. 阅读器功能

| 功能 | 位置 | 说明 |
| --- | --- | --- |
| 深浅色主题 | 🌙 / ☀️ | 全站 CSS 变量切换，暗色下文字与代码块均保证可读；设置记在浏览器本地。 |
| 字号 | A− / A＋ | 13–23px 无级调节，同样记住上次设置。 |
| 阅读进度 | 页面最顶部细条 | 随滚动显示；门户另有一条扁平化进度线与分区高亮。 |
| 回到顶部 | 右下角 ↑ | 滚动超过一屏后出现。 |
| 表格 / 代码 | 内容区 | 手机上横向滑动，不撑破版面。 |
| 打印 / PDF | 顶部按钮 | 隐藏交互控件，避免分页截断表格与代码块。 |
| ESC | 键盘 | 关闭手机抽屉目录与术语弹窗。 |
| 术语弹窗 | 点击正文中虚线标记的词 | 显示全称 / 分类 / 定义 / 交付意义 / 相关词条；相关词条可继续点，手机端为底部抽屉。 |
| 术语词典 | 顶部「📖 术语」或目录底部 | 独立页，**__TERMS__ 条按 11 个分类**筛选、按词条 / 全称 / 释义关键词检索。 |
| 内联图示 | 正文中的 `<figure>` | 8 张 SVG 全部内嵌，随主题变色，打印时保留填充色。 |

---

## 4. 考核题库：全部是选择题

打开 `FDE工程师考核题库.html`（或从首页「查阅与考核」分区进入），题库共 **__Q_TOTAL__ 道题 / 单选 + 多选两类 / __DOMAINS__ 个能力域 / 3 个难度层级**，每题都标出处、能力域、难度与解析。

| 想做什么 | 怎么设置 |
| --- | --- |
| 防止背题序 | 勾选「题序打乱（Fisher–Yates）」，同一套筛选两次做题顺序不同 |
| 防止背选项位置 | 勾选「选项乱序」，**单选与多选一律参与**，答案索引自动重映射 |
| 让题型交叉出现 | 勾选「题型混排」，单选 / 多选跨能力域交叉出现 |
| 定点补强 | 「能力域」下拉选一个域（含 v5.0 新增的模型 / Agent 工程 / TTS / 跨行业 / 开源课程五域），配合题型与题量；错题按次数降序优先注入 |
| 逐题学 | 练习模式：提交本题即出正确 / 错误、正确答案、解析与出处 |
| 模拟考核 | 考试模式：全程隐藏答案，交卷后一次出总分、正确率、按能力域的薄弱项与逐题回看 |
| 只补漏洞 | 错题模式：只取错题本；连续答对 2 次自动移出 |
| 打印纸质卷 | 「打印 / PDF（含答案页）」生成题目页 + 独立答案页 |
| 保存进度 | 自动写浏览器 `localStorage`；换设备不迁移，「继续上次进度」可回到原组卷 |

**判分口径速记**：单选唯一正确项；多选全部选对才得分（漏选与错选同等不得分）。**v5.0 起题库统一为选择题**，原判断题 / 填空题 / 排序题 / 场景自评题已改写为单选或多选；开放性问题转到每个学习点的「🔍 细节追问」，不计入分数。全部题目自动判分，正确率只用来定位薄弱能力域，**不作为能力认证结论**，详见主手册 10.5.1–10.5.3 与速查 N1–N6。

间隔复习节奏：学完当天练习模式随机 10 题 → 第 2 天单选题（术语与硬约束）专项 → 第 7 天考试模式随机 20 题 → 第 30 天错题模式 + 多选题专项 → 每季度模型 / Agent 工程 / 语音 TTS 能力域专项 → 每次立项做模型与 TTS 选型两组多选题。

---

## 5. 第三册｜开源课程精读模块（v5.0 新增）

`03_开源课程解读.html`（源文件 `03_开源课程解读.md`）是对 **fde4.ai/book/**《前线部署工程师》开源版 13 个文档的**逐章解读与对照**，不是原文转载。

| 第几篇 | 解决什么 |
| --- | --- |
| 第 1 篇 全书地图 | 来源、作者、13 个文档结构与全书的因果链 |
| 第 2–4 篇 逐章精读 | 自序与第 1–3 章、第 4–6 章、第 7–8 章 + 后记与附录，逐章给「主张 / 证据 / 可迁移做法 / 边界」 |
| 第 5 篇 方法论卡片 | 把全书压缩成 18 张可带走的卡 |
| 第 6 篇 双向映射 | 这本书补我们什么、我们补它什么、与 4 章 19 单元 / 五阶段 / CS329Z 的交叉验证 |
| 第 7 篇 怎么用 | 学习路径、讲解稿、考核对齐 |
| 附录 Z | 来源清单与版权边界 |

**使用纪律**：原文版权归原权利人，本模块是原创分析；引用数字须区分「原书引用 / 公开报道 / 需当期核对」；原书中的商业组织方式不能直接照搬到本企业的交付制度，迁移前要按行业与公司规模重写判断条件。

---

## 6. v5.0 技术补强（第十一～十四篇）

| 篇章 | 补什么 | 速查配套 |
| --- | --- | --- |
| 第十一篇 模型类知识与技术选型 | 三条轴、五维矩阵、四笔成本账、推理框架与部署形态、八步选型流程、常见误区 | O 组 |
| 第十二篇 Agent 搭建与测试｜对照 CS329Z | 课程大纲对照、从零搭 Agent 八步、评测流水线、优化决策树、自训计划 | O 组 |
| 第十三篇 语音与 TTS 选型 | 全链路、方案谱系、选型决策树、评测指标与验收口径、延迟优化五招、集成降级、合规清单 | P 组 |
| 第十四篇 跨行业真实案例集 | 12 类行业的真实约束、迁移要点、横向对照表与案例使用四条纪律 | Q 组 |
| 第三册 开源课程精读 | 商业交付、激活、续约、扩张、规模化复制与产品化 | Q 组 |

**边界**：涉及模型、框架、语音服务与开源课程的名称均为**公开资料举例**，用于说明「这一类能力由谁承担」，不构成推荐、排名、背书或采购建议；所有价格、时延、成效数字均标注为公开 / 厂商 / 原书引用口径，落地前需按当期官方文档与客户环境核对。

---

## 7. 离线自包含的技术说明

- 所有 CSS、JavaScript **全部内嵌**在 HTML 里；没有 `<link>`、没有 `<script src>`、没有 `@import`、没有远程字体、没有外部图片。
- 术语词典数据（**__TERMS__ 条**）以 JSON 内嵌在三册与《术语词典.html》的脚本里；8 张图示以内联 `<svg>` 写入正文；**__Q_TOTAL__ 道考核题以 JSON 内嵌在题库页**，介绍页与门户页的能力体系图同样是内联 SVG，**没有任何外链图片或图标字体**。
- 字体使用系统字体栈（`-apple-system / SF Pro Display / PingFang SC / Microsoft YaHei`），无需下载；v5.0 首页用 `font-variant-numeric: tabular-nums` 保证数字对齐。
- 主题、字号、题库进度与错题本只使用浏览器 `localStorage`，不发起网络请求；不可用时自动降级，不影响阅读与做题。
- 三册之间、册页与 19 节笔记、题库页、介绍页、站点地图之间全部用**相对路径**互跳，不依赖任何域名。
- 19 节逐节笔记引用的**课程截图已全部本地化**到 `参考资料/images/`，HTML 用本地 `<img>` 引用并懒加载；生成器若发现某张截图未收录，会降级为文字说明，**绝不留下死链**。
- v5.0 首页的滚动进场、分区高亮、进度条、数字动画均为**原生 JS + IntersectionObserver**，无第三方库；系统开启「减少动态效果」时自动关闭动画，全部内容仍然可见可用。

> **轻量使用**：三册手册、题库页、介绍页、术语词典页、门户页各自完全自包含，单独拷走即可阅读 / 做题，不需要 `参考资料/` 目录。图片体积主要来自 19 节笔记的课程截图，只在你想对照原课程图解时才需要保留整个 `参考资料/` 文件夹。

---

## 8. 目录结构

```
企业智能体FDE交付实战手册/
├── index.html                      v5.0 扁平化入口门户（L0 · 吸顶分区导航）
├── 站点地图.html                    三层 IA 图 / 页面清单 / 导航规则 / 部署要点
├── 手册展示页.html                  L1 手册介绍页（sticky 章节目录，单文件自包含）
├── 细节追问提示词库.html            每个学习点 × 5 个角度的可复制追问提示词
├── 01_主手册.html                  主手册阅读版（十四篇 + 附录 A–F）
├── 01_主手册_企业智能体FDE交付实战.md   主手册源文件
├── 02_速查手册.html                速查手册阅读版（A–Q 十七组）
├── 02_速查手册_名词疑难与FAQ.md      速查源文件
├── 03_开源课程解读.html            第三册：开源课程精读模块（7 篇 + 附录 Z）
├── 03_开源课程解读.md              第三册源文件
├── FDE工程师考核题库.html          v5.0 独立考核题库（__Q_TOTAL__ 题 / 单选 + 多选）
├── 术语词典.html                   __TERMS__ 条 / 11 类可检索词条（独立页）
├── glossary_data.py                术语词典数据（__TERMS__ 条）
├── figure_data.py                  8 张主手册图示的声明式定义（无手工坐标）
├── chart_engine.py                 声明式 SVG 图表引擎（字体测量 / 自动布局 / 正交连线）
├── question_bank_data.py           __Q_TOTAL__ 道考核题数据（题库页 / 核验脚本共用）
├── prompt_data.py                  三册追问模块数据 / 提示词模板 / 交互组件
├── exam_pages.py                   题库页生成器（旧展示页保留但不再调用）
├── site_chrome.py                  全站设计系统与统一导航组件
├── site_pages.py                   门户 / 介绍 / 站点地图三个站点级页面生成器
├── 参考资料/
│   ├── 逐节笔记索引.html
│   ├── 课程逐节笔记/                lesson-01..19 的 HTML + MD
│   ├── 开源课程原文/                开源书 13 章 Markdown 本地副本（对照用）
│   └── images/                      19 个章节子目录，全部本地截图
├── 离线使用说明.md                 本文件
├── 核验报告.md                    __GROUPS__ 组全面复检结论
├── build_html.py                   生成器（Python 标准库，零依赖，可离线重跑）
└── verify_offline.py                全面核验脚本（可离线重跑）
```

同级目录还有 `企业智能体FDE交付实战手册_离线资源包.zip`，即本目录的完整压缩包，拷到另一台设备解压即可用。

重新生成：在本目录执行 `python3 build_html.py`，会按当前 Markdown 源文件与数据文件重跑门户、介绍页、站点地图、提示词库、三册 HTML、题库页、笔记副本、索引与 zip（不需要联网、不需要 pip 安装任何东西）。核验用 `python3 verify_offline.py`。

---

## 9. 内容与版权边界

- 三册手册、考核题库与介绍页为**独立学习整理的能力体系**，不隶属、不代言任何厂商，不是任何认证的官方教材；**题库非官方题库**。
- 能力骨架参照公开的 FDE 知识域，已抽象为跨行业通用模型；平台功能、参数与规格**以所选用产品的当期文档为准**。
- 第九、十一、十二、十三、十四篇与附录 E、术语词典、题库、介绍页中出现的**产品与开源项目名称，均为公开资料举例**，用于说明「这一类能力由谁承担」，不构成推荐、排名、背书或采购建议；不含未经核实的成效数字、价格、合规资质结论与客户实测数据。
- `参考资料/课程逐节笔记/` 与 `参考资料/开源课程原文/` 为公开学习资料的本地副本，版权归原权利人，仅用于对照核验；手册正文与第三册精读均已做厂商中立化 / 原创分析处理，第三册对原书数字一律标注引用口径并要求当期核对。
- 手册中的三个项目（星澜零售 / 岚江城商行 / 恒岳精密）、四个部署方案包与第十四篇的行业案例均为**教学演练场景 / 公开事实归纳**，非真实客户案例或官方实施方案；性能与成效数据不外推。
- 第十篇「扩展阅读与缺口清单」如实列出本手册不覆盖、未实测、需客户确认的内容；引用本手册对外汇报时，请一并说明边界。
- **题库正确率只用于定位薄弱能力域，不作为能力认证结论**；能否交付仍以 0.4 的产出物与项目验收报告为准。

---

## 10. 细节追问：把每个学习点带去问任意 AI

三册正文的**每个标题旁**都有一个「🔍 细节追问」按钮（19 节逐节笔记页在封面下方也有一个）。
点开后会得到一段**自带本模块手册原文摘录**的提示词：不只是写明「这是我的手册」，
而是把这一节实际写了什么一起粘贴给 AI，因此**不需要部署网站、不需要联网、不需要先上传文件**。

| 步骤 | 做法 |
| --- | --- |
| 1 建立整册上下文（可选） | 在《细节追问提示词库.html》点「📋 复制会话开场白」先发一次，告诉 AI 这套手册是什么、怎么组织、怎么问 |
| 2 找到模块 | 正文标题旁的「🔍 细节追问」，或在提示词库页按资料 / 章节 / 概念 / 能力域检索 |
| 3 选角度 | 五个：🧩 概念澄清 / 🛠 落地做法 / 📐 验收与评测 / ⚠️ 风险与治理 / 🗣 对外讲解；与 L0–L5 认知分层呼应 |
| 4 复制并提问 | 点「📋 复制完整上下文包」（默认）：手册原文摘录 + 模块元数据 + 追问问题 + 输出要求一起复制，粘贴到任意 AI 即可 |

**三种复制模式**

| 模式 | 适用 | 说明 |
| --- | --- | --- |
| 完整上下文包（默认） | 任意 AI，包括不能联网、不能读文件的 | 提示词里用 `<<<FDE_MODULE_EXCERPT_BEGIN>>>` / `END` 包住该模块的原文摘录；AI 被要求以这段原文为第一依据 |
| 精简版 | 已把本包三册 Markdown 上传到会话 / 知识库的 AI | 去掉原文摘录以缩短长度，并明确要求「原文未加载就先索要，不要凭书名猜」 |
| 带链接版 | 明确支持联网浏览，且已把本目录部署到公网 | 在完整包后附一个公开回查地址；链接只是辅助，**不替代粘贴的原文**，无法访问时必须依据原文作答 |

**需要部署上线吗？** 不需要。部署解决的是「人能访问、能贴链接回查」，不解决「外部 AI 自动知道手册内容」。
除非目标 AI 明确支持联网浏览 / 文件问答 / 知识库，并且你主动给了 URL 或文件，否则它看不到本包任何内容。
因此本包把「定位一个上下文的内容」做成了默认能力：复制出去的文字本身就是一段自足的资料。
部署后若想附链接，可在提示词库页「部署地址（可选）」填入公开地址（存本地浏览器，不上传），
再用「带链接版」；不填也完全不影响使用。

**AI 被要求的作答规范**：

- 优先依据粘贴的原文，对齐其中的定义、口径、步骤编号与验收判据；原文没覆盖的先索要，不要假装读过本地文件；
- 区分【手册已写明】【AI 的推断】【需查当期官方文档或客户确认】三类信息；
- 不给未经核实的成效数字、价格、性能实测、合规资质结论或真实客户案例；原文里的演练项目与指标是教学设定；
- 结尾给「本模块可验收产出物」清单与 3 个继续追问的问题；
- 上下文不足时先列出需要补充的信息，而不是替你补全。

**规模**：三册共 **__ASK_N__ 个学习点**（每个标题 = 一个模块），每个 5 个角度，
预生成 **__ASK_P__ 段**提示词模板；每个模块另存一份原文摘录，浏览器端按同一组标记展开，
不发起任何网络请求。提示词库页可按「资料（主手册 / 速查手册 / 开源课程精读）/ 认知层 / 追问角度」筛选，
打印时会把提示词一并输出。

> **边界**：AI 回答只是学习辅助，不替代本手册口径、当期官方文档与客户验收；
> 题目、答案与判分仍以本手册和题库为准。复制动作只写浏览器剪贴板，不上传任何内容。

---

## 11. 部署上线与核对

本目录就是一个**完整的静态站点**，无需构建、无需服务端、无需数据库、无需账号；
所有页面统一走相对路径，本地 `file://` 打开与线上 HTTP 托管的表现一致。

| 场景 | 做法 |
| --- | --- |
| 静态托管 | 把整个目录上传到任意静态托管服务，**入口文件设为 `index.html`**，保持 `参考资料/` 等子目录原有相对位置即可。 |
| 本地预览 | 在本目录执行 `python3 -m http.server 8000`，浏览器访问 `http://localhost:8000/index.html`。 |
| 局域网双端 | 手机连同一 Wi-Fi，访问 `http://电脑IP:8000/index.html`（仍不依赖公网）。 |
| 单文件分发 | 三册阅读器、题库页、术语词典页、门户页各自完全自包含，单独拷走也能用；跨页链接此时失效，其余功能保留。 |
| 更新内容 | 改 Markdown 源文后执行 `python3 build_html.py` 重跑全部页面与 zip，再执行 `python3 verify_offline.py` 复检。 |

**上线前核对**（对应 `站点地图.html` 的导航规则）：

1. 顶部主导航在每一页都可达，当前栏目高亮；面包屑层级正确，每页都能一键回到 L0 门户与站点地图；
2. 门户页吸顶分区导航滚动高亮、阅读进度条、滚动进场与「减少动态效果」降级在桌面与手机都正常；
3. 页脚站点地图链接无死链；阅读页使用精简页脚条，不干扰正文；
4. **__MUST__ 个** `#anchor-*` 稳定锚点跨页跳转正常（生成器与核验脚本逐一验证）；
5. 深浅主题、手机菜单、目录抽屉、术语弹窗、细节追问弹窗与题库交互在移动端可用；
6. 全站无外部请求：CSS / JS / 字体栈 / SVG / 术语 JSON / 题目 JSON / 截图全部内嵌或本地存放；
7. 第三册精读的原文引用均在 `参考资料/开源课程原文/` 有本地副本，且正文标注了版权与引用口径边界。

> 页面已写入 `description`、`theme-color` 与 Open Graph 元信息，便于搜索引擎与分享卡片识别；
> 本站不加载任何在线字体、CDN、统计脚本或第三方资源，**全站不发起任何网络请求**。
"""


def build_zip():
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    skip_names = {'.DS_Store'}
    skip_dirs = {'__pycache__', '.git', '.workbuddy'}
    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(BASE.rglob('*')):
            if p.is_dir() or p.suffix in ('.zip', '.pyc') or p.name in skip_names:
                continue
            if any(part in skip_dirs for part in p.relative_to(BASE).parts):
                continue
            z.write(p, str(Path(BASE.name) / p.relative_to(BASE)))
    return ZIP_PATH.stat().st_size


def main():
    print('生成三册阅读版…')
    for d in DOCS:
        md = (BASE / d['md']).read_text(encoding='utf-8')
        if '<!--CONTINUE-->' in md:
            print('  WARN %s 仍含未替换占位符' % d['md'])
        doc, toc, injected = render(md, d['key'], d['title'], d['badge'],
                                    d['sub'], d['pills'])
        doc = site_chrome.inject(
            doc, {'main': 'learn', 'book3': 'reading', 'quick': 'lookup'}[d['key']],
            [('门户', 'index.html'),
             ('介绍', '手册展示页.html'),
             (d['badge'], None)],
            title=d['title'] + ' | 企业级智能体交付实战手册',
            description=d['sub'])
        (BASE / d['out']).write_text(doc, encoding='utf-8')
        print('  OK  %-24s %8d chars  toc=%3d  anchors=%d/%d'
              % (d['out'], len(doc), len(toc), len(injected),
                 sum(1 for x in MUST if x[3] == d['key'])))

    print('本地化 19 节逐节笔记…')
    rows = prepare_lessons()
    if rows:
        build_lesson_index(rows)
        print('  OK  %d 篇笔记，%d 个阅读版 HTML' % (len(rows), len(rows)))

    print('生成术语词典页…')
    n_terms = build_glossary_page()
    print('  OK  %s（%d 条词条 / %d 个分类）'
          % (GLOSS_HTML, n_terms, len(glossary_data.CATEGORIES)))

    print('生成考核题库页与手册展示页…')
    print('生成站点级页面（门户 / 介绍 / 站点地图）…')
    build_index(rows)
    (BASE / SHOW_HTML).write_text(site_pages.intro_doc(
        q_total=question_bank_data.STATS['total'],
        terms=len(glossary_data.GLOSSARY),
        must=len(MUST), rows=40, ask_n=len(ASK_MODULES),
        domains=len(question_bank_data.DOMAINS)), encoding='utf-8')
    (BASE / SITE_MAP_HTML).write_text(site_pages.sitemap_doc(), encoding='utf-8')
    print('  OK  %s / %s / %s（统一站点导航 + 面包屑 + 页脚站点地图）'
          % ('index.html', SHOW_HTML, SITE_MAP_HTML))
    print('生成细节追问提示词库…')
    (BASE / ASK_HTML).write_text(
        prompt_data.build_library_page(ASK_MODULES, VERSION), encoding='utf-8')
    print('  OK  %s（%d 个学习点 × %d 个角度 = %d 段提示词）'
          % (ASK_HTML, len(ASK_MODULES), len(prompt_data.ANGLES),
             len(ASK_MODULES) * len(prompt_data.ANGLES)))


if __name__ == '__main__':
    main()
