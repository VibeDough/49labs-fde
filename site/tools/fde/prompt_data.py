#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
细节追问提示词体系（v5.0 · 第十轮「上下文自足」增强）
======================================================
每个学习点 = 一个「模块」。点击模块旁的「🔍 细节追问」，得到一段**自带本模块原文摘录**、
可直接复制到任意 AI 的结构化提示词；同一模块有 5 个追问角度。

为什么改
--------
v5.0 初版只把「元数据」（书名 / 章节路径 / 认知层 / 核心问题）写进提示词，
还写了「你不必联网访问」「出处锚点不是给你访问的链接」，结果外部 AI 既拿不到正文、
又被告知不必去找，只能给通用答案。本轮把提示词改为**上下文自足**：

1. 原文随包：每个模块从 Markdown 正文抽取权威摘录（清洗注释 / 代码块 / 表格噪声，
   限长），复制时随提示词一起粘贴；AI 被明确要求以这段原文为准。
2. 三档复制：完整上下文包（默认，无需部署 / 联网 / 上传文件）、精简版（AI 已加载
   本手册文件时使用）、带链接版（部署后可选，链接只作回查辅助，不替代原文）。
3. 会话开场白：一次性说明「这套手册是什么、怎么组织、怎么问」，避免 AI 把
   「我的手册」当成未知外部资料。
4. 五层追问角度与诚实边界保持不变；仍禁止编造成效数字、明确区分三类信息。
5. 零外部请求：模块元数据 / 原文摘录 / 5 段提示词模板在生成期预渲染为内嵌 JSON，
   浏览器端按同一份标记展开为最终文本并复制，不发起任何网络请求。

对外接口
--------
  ANGLES                       五个追问角度
  build_modules(main_md, quick_md, term_keys, version, book3_md) -> list[dict]
  lesson_module(stem, title, version, body)            -> dict
  prompt_text(module, angle, version)                 -> str（含 [[FDE:CTX]] 占位）
  context_block(module) / prompt_full(...)            -> str（展开后的自足提示词，供核验）
  payload(modules, version)                          -> str（内嵌 JSON）
  ASK_CSS / ASK_CORE_JS / ASK_JS / ASK_POP_HTML       共享交互组件
  build_library_page(modules, version)               独立提示词库 HTML
"""

import json
import re
import html as ihtml

# ---------------------------------------------------------------- 上下文包协议
# 生成期：prompt_text() 在提示词里留一个占位符；浏览器与核验脚本用同一组标记展开。
# 这么做是为了让「一段提示词 = 一份自带原文的独立文本」，同时避免在 5 个角度里
# 重复内嵌同一段摘录导致 HTML 体积翻数倍。
CTX_TOKEN = "[[FDE:CTX]]"
CTX_BEGIN = "<<<FDE_MODULE_EXCERPT_BEGIN>>>"
CTX_END = "<<<FDE_MODULE_EXCERPT_END>>>"
CTX_CAP = 1100           # 单模块原文摘录字符上限（控制单次粘贴长度）
CTX_MIN = 120             # 核验下限：低于此值视为摘录失败
SITE_KEY = "fde_site_base"

LITE_NOTE = (
    "（本次未随附手册原文。若你已在会话中加载了本手册的 Markdown 文件 / 知识库，请据其回答；"
    "否则先向我索要该节原文，不要凭书名、章节号或常识猜测手册内容。）"
)

SITE_NONE_NOTE = (
    "\n# 资料回查（可选）\n"
    "- 我尚未配置部署地址；本次请完全依据上面粘贴的手册原文，不要尝试访问任何链接。"
)

SESSION_PRIMER = (
    "# 会话开场白：请先读完这段，再回答我后面的问题\n\n"
    "接下来我会就《企业级智能体交付实战手册》v5.0 逐节向你提问。"
    "这是一套面向「前沿部署工程师（FDE，Forward Deployed Engineer）」的离线学习与交付实战资料，"
    "跨行业、厂商中立、独立学习整理，**不是**任何厂商的官方教材，也不是已上线项目的对外宣传材料。\n\n"
    "## 这套资料是什么\n"
    "- 主手册：从场景判断、方案设计、构建模式、评测调优到交付治理的完整方法，"
    "含三个贯穿全书的**教学演练项目**（星澜零售 / 岚江城商行 / 恒岳精密）；\n"
    "- 速查手册：专业名词、易混概念、疑难与常见问题解决方案、必背数字与硬约束；\n"
    "- 开源课程精读：对公开《前线部署工程师》开源版课程（fde4.ai/book/）的逐章解读与双向对照；\n"
    "- 配套：术语词典（可点开释义）、纯选择题考核题库、逐节笔记、站点地图与离线使用说明。\n\n"
    "## 统一口径\n"
    "- 五阶段交付方法论：接入 → 建设 → 验证 → 推广 → 治理；\n"
    "- 三项核心能力：场景理解 / 交付实施 / 安全合规；认知分层 L0 定位 → L5 传授；\n"
    "- 三个贯穿项目及其人员、数据、指标**均为教学设计构造的演练场景**，不是真实客户，"
    "指标是演练目标值 / 验收基线，不得对外引用为项目成效；\n"
    "- 公开行业案例只作公开参照，具体数值以原始公开资料为准，手册不做二次推断。\n\n"
    "## 我接下来会怎么问\n"
    "我会按「一个学习点 = 一段提示词」粘贴给你，每段包含四部分：\n"
    "1) 该模块的**手册原文摘录**，用 <<<FDE_MODULE_EXCERPT_BEGIN>>> / "
    "<<<FDE_MODULE_EXCERPT_END>>> 包住；\n"
    "2) 模块元数据（册 / 章节 / 认知层 / 能力域 / 关键概念 / 核心问题 / 建议产出物）；\n"
    "3) 本次追问角度（概念澄清 / 落地做法 / 验收与评测 / 风险与治理 / 对外讲解）与具体问题；\n"
    "4) 输出要求。\n\n"
    "## 请遵守\n"
    "- **优先依据我粘贴的原文**作答，逐条对齐其中的定义、口径、步骤与验收判据；"
    "原文未覆盖的部分不要假装见过，先向我索要该节原文；\n"
    "- 你无法访问我的本地文件、内网、下载目录或未提供的链接；除非我明确给出可公开访问的"
    "地址且你确实支持联网浏览，否则不要假设能打开，更不要据此编内容；\n"
    "- 明确区分【手册已写明】【你的推断】【需查当期官方文档或客户确认】三类信息；\n"
    "- 不给未经核实的成效数字、价格、性能实测、合规资质结论或真实客户案例；\n"
    "- 提到产品与开源项目名称只作能力举例，并注明「不构成推荐、排名或采购建议」；\n"
    "- 每次回答结尾给「本模块可验收产出物」清单与 3 个我接下来该继续追问的问题。\n\n"
    "请先回复一句「已读，将以你粘贴的原文为准」，然后等我发第一段提示词。"
)

# ---------------------------------------------------------------- 追问角度
ANGLES = [
    dict(key="concept", icon="🧩", name="概念澄清", label="把概念讲准",
         focus="先把这个模块的概念边界讲清楚，避免我用错词、定错指标。",
         qs=["这个模块的核心定义是什么？英文全称与常见别名是什么？",
             "它最容易和哪 2–3 个概念混淆？分别怎么区分？",
             "在这个模块里，哪些说法是错的、过时的，或只在特定前提下成立？"]),
    dict(key="practice", icon="🛠", name="落地做法", label="按步骤做出来",
         focus="按真实交付顺序讲清怎么落地，让我能照着做一遍。",
         qs=["做这个模块需要哪些输入（数据 / 权限 / 文档 / 系统接口）？",
             "从零到可演示分几步？每步的关键配置、参数与判断点是什么？",
             "最常见的 3 个坑是什么？现场怎么快速定位与修复？"]),
    dict(key="proof", icon="📐", name="验收与评测", label="证明它有效",
         focus="讲清怎么证明这个模块做对了，而不是「看起来能跑」。",
         qs=["该定哪些验收指标？口径与计算公式分别是什么？",
             "评测集 / 回归用例怎么设计？Badcase 如何归因到具体环节？",
             "什么条件下必须停止推进、降级或回滚？谁签字？"]),
    dict(key="risk", icon="⚠️", name="风险与治理", label="把风险管住",
         focus="讲清上线前必须管住的安全、权限、审计、成本与运维风险。",
         qs=["谁能看什么、写什么、留什么痕？最小权限与数据分级怎么划？",
             "提示注入 / 越权检索 / 凭证泄露 / 幻觉等风险怎么防？怎么做红队测试？",
             "降级、兜底、回滚、审计留痕、变更管理与成本核算怎么落地？"]),
    dict(key="explain", icon="🗣", name="对外讲解", label="讲给别人听",
         focus="帮我把这个模块讲给业务方、评审或新人听，并准备好被质疑。",
         qs=["一句话定义，以及 1 分钟 / 5 分钟 / 15 分钟三种讲法分别怎么说？",
             "业务方最可能质疑哪 3 点？怎么基于验收证据回答而不空口承诺？",
             "配一张白板图的话，画哪几层、每层标什么、验收线画在哪？"]),
]
ANGLE_KEYS = [a["key"] for a in ANGLES]

ROLE = (
    "你是企业级智能体交付（FDE，Forward Deployed Engineer）领域的资深顾问，"
    "熟悉场景判断、知识工程、智能体编排、评测调优、安全合规与上线治理。"
    "我在下面**直接粘贴了手册该模块的原文摘录**，这就是「我的手册」具体写了什么；"
    "请以这段原文为第一依据做逐层展开式作答，不要泛泛而谈，不要凭书名、章节号或常识猜测"
    "我没粘贴的内容，也不要假设我没说过的业务背景。"
)

CONSTRAINTS = (
    "- 每个问题先给一句结论，再给 1 个可操作示例（配置 / 表格 / 步骤 / 话术均可）；\n"
    "- 明确区分三类信息：【手册已写明】（须与上面粘贴的原文对应）【你的推断】"
    "【需查当期官方文档或客户确认】；\n"
    "- 引用原文中的定义、指标口径、步骤编号或验收判据时，按原文写，不要改写数值与条件；\n"
    "- 不要给未经核实的成效数字、价格、性能实测、合规资质结论或真实客户案例；"
    "原文里的演练项目与指标是教学设定，不得当作真实项目成效；\n"
    "- 提到产品与开源项目名称时只作能力举例，并注明「不构成推荐、排名或采购建议」；\n"
    "- 结尾给「本模块可验收产出物」清单，以及 3 个我接下来该继续追问的问题；\n"
    "- 若原文摘录不足以回答，先列出你需要我补充的原文或信息，再给初步回答；"
    "不要假装读过我的本地文件、内网或未提供的链接。"
)

BOOK_NAME = {"main": "主手册", "quick": "速查手册", "book3": "开源课程精读",
             "lesson": "19 节逐节笔记"}
BOOK_FILE = {"main": "01_主手册.html", "quick": "02_速查手册.html",
            "book3": "03_开源课程解读.html",
            "lesson": "参考资料/课程逐节笔记/"}

# 14 个能力域（与题库口径一致）
D_AI = "能力域 1 · AI 与 Agent 基础"
D_PLAT = "能力域 2 · 智能体平台能力地图"
D_MODE = "能力域 3 · 方案设计与五种构建模式"
D_EVAL = "能力域 4 · 评测与调优"
D_DELIV = "跨能力域 · 企业级交付标准"
D_SEC = "安全合规与责任 AI"
D_ENG = "第七篇 · 工程与治理补遗"
D_SEL = "第九篇 · 国内技术选型"
D_READ = "第十篇 · 扩展阅读与最终目录"
D_BOOK3 = "能力域 10 · 开源课程与商业交付"
D_MODEL = "能力域 11 · 模型与技术选型"
D_AGENT = "能力域 12 · Agent 工程与测试"
D_TTS = "能力域 13 · 语音与 TTS 选型"
D_CASE = "能力域 14 · 跨行业真实案例"

# ---------------------------------------------------------------- 精编模块
# key = 标题前缀（去空白后 startswith），命中则覆写 question / deliverable / concepts / note
CURATED = {
    "0.4": dict(question="我下一步该做什么、每步交什么、怎么判断这步真的完成了？",
                deliverable="14 份阶段产出物 + 打勾记录",
                note="按 Step 1→14 顺序，重点问四阶段的验收边界"),
    "0.6": dict(question="我的行业能不能直接套用这套方法？要替换哪些前提？",
                deliverable="行业映射表 + 不适用项清单"),
    "2.2": dict(question="平台到底提供哪些能力组件，哪些是我要自己补的？",
                deliverable="能力地图 + 自建 / 采买分界线"),
    "3.0": dict(question="这个需求值不值得做？怎么把模糊诉求收敛成可验收的一句话？",
                deliverable="场景判断卡 + 方案画布"),
    "3.2": dict(question="知识问答型应用怎么把资料接进来，且回答有据可查？",
                deliverable="可发布应用 + 知识切分与兜底配置说明"),
    "3.3": dict(question="流程编排型应用怎么提取参数、做分支并安全地写回业务系统？",
                deliverable="主工作流 + 变量隔离表 + 幂等方案"),
    "3.4": dict(question="多智能体协同时，转交描述与具名返回怎么写才不跑偏？",
                deliverable="协同图 + 转交描述 + 兜底路径"),
    "4.1": dict(question="怎么证明智能体有效，而不是只看几条 demo？",
                deliverable="评测集 + 基线 + 回归报告"),
    "4.3": dict(question="Badcase 出来了，怎么归因到知识 / 检索 / 生成 / 编排哪一环？",
                deliverable="归因记录 + 修改前后对比"),
    "5.2": dict(question="五阶段交付每个阶段交什么、谁签字、什么条件下不进下一阶段？",
                deliverable="项目文件包 + 阶段验收记录"),
    "5.5": dict(question="谁能看什么、写什么、留什么痕？高风险动作怎么分级管控？",
                deliverable="权限矩阵 + 审计方案 + 红队用例"),
    "5.10": dict(question="上线后怎么监控、降级、回滚、控制Token成本？",
                 deliverable="运维 SOP + 回滚演练记录"),
    "7.5": dict(question="指标怎么定义与计算？P95、命中率、拒答准确率各自口径是什么？",
                deliverable="指标字典 + 计算样例"),
    "7.6": dict(question="提示注入、越权检索、凭证泄露怎么防？怎么红队测试？",
                deliverable="红队报告 + 修复清单"),
    "9.4": dict(question="按数据敏感度与集成复杂度，四类部署方案包怎么选？",
                deliverable="选型报告 + 六份交付物"),
    "9.6": dict(question="评审 12 问逐条问，答不上为什么就不能进建设期？",
                deliverable="评审意见 + 待确认项清单"),
    "10.2": dict(question="这套手册明确还缺哪些内容？我该去哪里补、怎么并入？",
                 deliverable="个人缺口清单 + 扩展阅读计划"),
    "10.5": dict(question="两类选择题怎么判分、复习怎么打乱才不背题序、节奏怎么排？",
                 deliverable="复习记录 + 错题本 + 成绩单"),
    "F.6": dict(question="最后一次复习，40 行最终目录按什么顺序走？",
                deliverable="复习计划 + 打勾记录"),
    "F.8": dict(question="我此刻的来意对应哪个入口？第一件事做什么？",
                deliverable="一页速用卡"),
    "C.10": dict(question="站点化改造改变了什么、没改变什么？上线前要核对哪六项？",
                 deliverable="上线检查单"),
    "C.11": dict(question="细节追问提示词怎么设计、怎么用、边界在哪？",
                 deliverable="一段可复制的追问提示词 + 使用记录"),
    "A1": dict(question="AI / LLM / 生成式 AI / 推理 这几个词到底怎么分？",
               deliverable="概念地图"),
    "B1": dict(question="25 组易混淆概念分别怎么区分？现场怎么一句话讲清？",
               deliverable="对照卡"),
    "C1": dict(question="文档导入规格、切分参数与 Overlap 怎么定？",
               deliverable="导入配置表"),
    "D1": dict(question="排障时按什么顺序定位，才不会瞎改 Prompt？",
               deliverable="诊断树 + 归因记录"),
    "G1": dict(question="能力权重与题型怎么分布？考前该优先背什么？",
               deliverable="复习优先级表"),
    "I1": dict(question="哪些数字是硬约束？记错会出什么事故？",
               deliverable="数字速记卡"),
    "M3": dict(question="选型评审 12 问逐条怎么答？答不上说明什么？",
               deliverable="评审意见"),
    "N1": dict(question="单选与多选两类选择题各自的判分口径是什么？",
               deliverable="判分口径表"),
    "N7": dict(question="三层导航怎么走、上线前核对哪六条规则？",
               deliverable="导航核对记录"),
    "N8": dict(question="细节追问的 5 个角度分别适合什么场景？提示词怎么用才不丢上下文？",
               deliverable="一段可复制提示词 + AI 回答的核验记录"),
    # ---- v5.0 第八轮新增 ----
    "11.": dict(question="模型选型看哪些维度？开源权重与商用 API 怎么放在一张决策表里？",
                deliverable="模型选型矩阵 + 许可证核对表"),
    "12.": dict(question="从零搭一个 Agent 要哪八步？评测流水线怎么接进 CI？",
                deliverable="八步实施清单 + 可回归评测流水线"),
    "13.": dict(question="TTS 全链路哪些环节会吃掉延迟？选型与降级怎么定？",
                deliverable="链路时延预算 + 供应商能力对照表"),
    "14.": dict(question="这个行业的真实约束是什么？把案例迁移到我所在行业要改哪几层？",
                deliverable="行业迁移对照表 + 不可外推项清单"),
    "O1": dict(question="模型类知识怎么快速补齐？参数量、上下文、许可证、推理成本怎么权衡？",
              deliverable="模型速查卡 + 选型判据"),
    "P1": dict(question="语音 / TTS 选型有哪些能力类型？评测指标与合规清单怎么定？",
              deliverable="TTS 评测表 + 合规签字清单"),
    "Q1": dict(question="开源课程与原手册的方法论怎么双向映射？哪些能直接用、哪些要改造？",
              deliverable="双向映射表 + 改造清单"),
    "C.12": dict(question="第八轮补了哪些内容？还有哪些缺口需要我继续补？",
                deliverable="v5.0 变更对照 + 个人补充计划"),
    "第 1 篇": dict(question="这本开源书的整体结构是什么？和本手册的能力框架怎么对齐？",
                 deliverable="全书地图 + 对齐表"),
    "第 5 篇": dict(question="18 张方法论卡片分别解决什么现场问题？怎么带进项目？",
                  deliverable="卡片速记 + 现场用法"),
    "第 6 篇": dict(question="这本书补我们什么、我们补它什么？哪些结论不能直接照搬？",
                  deliverable="双向映射表 + 边界说明"),
}


def _clean(s):
    """标题纯文本：去 Markdown 标记与反引号，保留中文与编号。"""
    s = re.sub(r'`([^`]+)`', r'\1', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'\1', s)
    s = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', s)
    return re.sub(r'\s+', ' ', s).strip()


def _plain(line):
    """把一行 Markdown / 内嵌 HTML 洗成适合粘贴给 AI 的纯文本。"""
    s = line.strip()
    s = re.sub(r"<!--.*?-->", "", s)
    s = re.sub(r"<[^>]+>", "", s)                       # 内嵌 HTML 标签
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)          # 图片
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)      # 链接保留文字
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)            # 加粗
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", s)  # 斜体
    s = re.sub(r"^\s*>\s?", "", s)                       # 引用符
    s = re.sub(r"[ \t]{2,}", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _figure_caption(key):
    """把 <!--FIGURE:key--> 占位换成可读的图注，避免「整节只有图」的模块没有原文。"""
    try:
        import figure_data
        return figure_data.FIGURES[key][1]
    except Exception:
        return ""


def _excerpt(own, child, cap=CTX_CAP, title="", concepts=None):
    """按「本模块自身正文优先、下级小节补足」抽取权威摘录。

    去掉代码块、图片、分隔线与表格分隔行；保留表格数据行与列表，因为定义、指标口径、
    验收判据大量存在于这两种结构里；图示占位转换成图注，保证纯图示模块也有可读上下文。
    """
    picked, total, fence = [], 0, False
    left = cap

    def take(lines):
        nonlocal total, fence, left
        for raw in lines:
            if left <= 0:
                break
            s = raw.strip() if isinstance(raw, str) else ""
            if s.startswith("```"):
                fence = not fence
                # 手册里的围栏常是清单 / 决策树 / 配置原文，不是噪声，转成可读标注后保留
                if fence:
                    picked.append("〔以下为手册原文中的围栏清单 / 决策树 / 配置片段〕")
                continue
            if not s:
                continue
            m = re.match(r"^<!--\s*FIGURE\s*:\s*([A-Za-z0-9_-]+)\s*-->$", s)
            if m:
                cap_line = _figure_caption(m.group(1))
                if cap_line:
                    s = "〔本模块配图〕" + cap_line
                else:
                    continue
            elif s.startswith("<!--") or s.startswith("<!"):
                continue
            if re.fullmatch(r"[-=:|\s]+", s):     # --- / | --- | --- |
                continue
            if s.startswith("!["):
                continue
            if not s.startswith("〔"):
                s = _plain(s)
            if not s:
                continue
            if len(s) > 260:
                s = s[:258] + "…"
            if len(s) + 1 > left:
                s = s[:max(0, left - 2)] + "…"
            picked.append(s)
            total += len(s) + 1
            left -= len(s) + 1

    take(own)
    n_own = len(picked)
    if child and left > 0:
        n0 = len(picked)
        take(child)
        if len(picked) > n0 and n_own > 0:
            picked.insert(n0, "〔以下为该模块下级小节的原文片段〕")
    text = "\n".join(picked).strip()
    if not text:
        cs = "、".join(concepts or []) or "（见下方元数据）"
        text = ("（本模块「%s」的正文主要是图示 / 表格 / 清单，逐字摘录有限。"
                "可确认的上下文：关键概念 %s；核心问题与建议产出物见下方「模块元数据」。"
                "图示中的具体结构、数值与条款不在本次粘贴范围内，请标注"
                "【需查当期官方文档或客户确认】或直接向我索要该节完整原文，不要凭常识补全。）"
                % (title[:40], cs[:120]))
    elif len(text) < 120:
        text += ("\n（本模块正文较短；未覆盖的定义与数值请标注【需查当期官方文档或客户确认】，"
                 "或向我索要该节完整原文，不要凭常识补全。）")
    if len(text) > cap:
        head = text[:cap].rsplit("\n", 1)[0]
        text = head + "\n…（摘录已达单次粘贴上限；未收录部分请向我索要该节完整原文）"
    return text


def _curated_for(title):
    for k in sorted(CURATED, key=len, reverse=True):
        if title.startswith(k):
            return CURATED[k]
    return None


def _classify(book, h1, h2, title):
    """认知层 + 能力域：按所属篇 / 附录 / 速查组推断。"""
    ctx = (h1 + " " + h2 + " " + title)
    if book == "book3":
        return "L1 · 判断力 / L4 · 治理力", D_BOOK3
    if "第十一章" in ctx or "模型" in h1 or "技术选型" in h1:
        return "L2 · 动手力", D_MODEL
    if "第十二篇" in ctx or "Agent 搭建" in ctx or "CS329Z" in ctx:
        return "L3 · 证明力", D_AGENT
    if "第十三篇" in ctx or "TTS" in ctx or "语音" in h1:
        return "L2 · 动手力", D_TTS
    if "第十四篇" in ctx or "跨行业真实案例" in ctx:
        return "L4 · 治理力", D_CASE
    if book == "quick":
        return "全层 · 速查", D_DELIV
    if "安全合规" in ctx or "责任 AI" in ctx or "红队" in ctx:
        return "L4 · 治理力", D_SEC
    if "第九篇" in ctx or "国内技术选型" in ctx or "选型" in h1:
        return "L4 · 治理力", D_SEL
    if "第十篇" in ctx or "扩展阅读" in ctx or "缺口" in ctx:
        return "L5 · 传授力", D_READ
    if "第七篇" in ctx or "工程与治理" in ctx:
        return "L4 · 治理力", D_ENG
    if "第八篇" in ctx or "对外表达" in ctx:
        return "L5 · 传授力", D_DELIV
    if "第六篇" in ctx or "自评" in ctx:
        return "L5 · 传授力", D_DELIV
    if "附录" in ctx:
        return "L5 · 传授力", D_DELIV
    if "第四篇" in ctx or "评测" in ctx:
        return "L3 · 证明力", D_EVAL
    if "第五篇" in ctx or title.startswith("5."):
        return "L3 · 证明力", D_DELIV
    if "第三篇" in ctx or title.startswith("3."):
        return "L2 · 动手力", D_MODE
    if "第二篇" in ctx or title.startswith("2."):
        return "L1 · 判断力", D_PLAT
    if "第一篇" in ctx or title.startswith("1."):
        return "L1 · 判断力", D_AI
    return "L0 · 定位与语言", D_DELIV


def _concepts(body, term_keys, limit=8):
    """从该节正文里按「长词优先」提取实际出现的术语，作为提示词的上下文锚点。"""
    got = []
    for k in term_keys:
        if len(k) < 2:
            continue
        if k in body:
            got.append(k)
            if len(got) >= limit:
                break
    return got


def _headings(md):
    """严格复刻 render() 的 sec 编号：跳过首个 h1、跳过 fenced code block，
    其余每个 #{1,4} 标题 sec+1。返回 [sec, level, title, bodylines, ownlines]。

    bodylines = 自身正文 + 所有下级小节正文（用于抽概念）；
    ownlines  = 仅自身正文（用于上下文摘录，优先自带内容而非整章堆叠）。"""
    heads, cur, sec = [], None, 0
    in_fence = False
    first_h1 = True
    for line in md.split("\n"):
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            if cur is not None:
                cur[3].append(line)   # 代码围栏保留给 _excerpt 清洗（清单 / 决策树常写在围栏里）
            continue
        if in_fence:
            # 围栏内的 # 号不是标题；内容仍保留给 _excerpt 清洗
            if cur is not None:
                cur[3].append(line)
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            lvl = len(m.group(1))
            if lvl == 1 and first_h1:
                first_h1 = False
                continue
            sec += 1
            cur = [sec, lvl, _clean(m.group(2)), []]
            heads.append(cur)
            continue
        # 保留注释行：<!--FIGURE:key--> 会在 _excerpt() 里转为可读图注
        if cur is not None:
            cur[3].append(line)
    # 上级标题的概念应包含其子标题下的正文（到下一个同级/更高级标题为止）
    raw_bodies = [list(h[3]) for h in heads]
    for i, h in enumerate(heads):
        acc = list(raw_bodies[i])
        for j in range(i + 1, len(heads)):
            if heads[j][1] <= h[1]:
                break
            acc += raw_bodies[j]
        h.append(list(raw_bodies[i]))    # h[4] = 自身正文
        h[3] = acc                       # h[3] = 自身 + 下级正文
    return heads


def build_modules(main_md, quick_md, term_keys, version="v5.0", book3_md=""):
    """三册所有 h2/h3（含非首 h1）+ 19 节笔记 → 模块列表。"""
    mods = []
    mid = 0
    src_books = [("main", main_md), ("quick", quick_md)]
    if book3_md:
        src_books.append(("book3", book3_md))
    for book, md in src_books:
        heads = _headings(md)
        h1, h2 = "", ""
        for sec, lvl, title, bodylines, ownlines in heads:
            if lvl == 1:
                h1, h2 = title, ""
            elif lvl == 2:
                h2 = title
            body = "\n".join(bodylines)
            layer, domain = _classify(book, h1, h2, title)
            c = _curated_for(title)
            concepts = (c.get("concepts") if c and c.get("concepts")
                        else _concepts(body, term_keys))
            if not concepts:
                concepts = ["本模块以流程与判断为主（概念见正文）"]
            child = bodylines[len(ownlines):]
            excerpt = _excerpt(ownlines, child, title=title, concepts=concepts[:8])
            question = (c["question"] if c else
                        "「%s」讲什么、为什么需要、怎么落地、怎么验收、有哪些坑？" % title[:34])
            deliverable = (c.get("deliverable") if c else "一页笔记 + 1 个可操作示例")
            mid += 1
            mods.append(dict(
                id="m%03d" % mid, sec=sec, book=book, bookName=BOOK_NAME[book],
                level=lvl, title=title, loc=" › ".join(x for x in (h1, h2) if x and x != title),
                layer=layer, domain=domain, concepts=concepts[:8],
                question=question, deliverable=deliverable,
                note=((c.get("note") or "") if c else ""),
                curated=bool(c), src="%s#sec-%d" % (BOOK_FILE[book], sec),
                excerpt=excerpt, contextChars=len(excerpt)))
    return mods


def lesson_module(stem, title, version="v5.0", body=""):
    """19 节逐节笔记：每节一个专属模块，原文摘录取自本地讲义副本。"""
    num = re.sub(r"\D", "", stem) or "001"
    lines = (body or "").split("\n")
    concepts = ["课程逐节笔记", "对照核验", "知识点覆盖"]
    excerpt = _excerpt(lines[1:] if len(lines) > 1 else [], [],
                       title=title, concepts=concepts)
    return dict(
        id="L" + num[-3:], sec=1, book="lesson",
        bookName=BOOK_NAME["lesson"], level=2, title=title,
        loc="4 章 19 节 · 公开资料本地副本", layer="L1 · 判断力 / L2 · 动手力",
        domain=D_AI, concepts=["课程逐节笔记", "对照核验", "知识点覆盖"],
        question="这一节的原始讲义讲了什么？和主手册的口径有什么差异？",
        deliverable="对照记录 + 差异清单", curated=False,
        note="本节为公开讲义的本地离线副本，原文版权归原权利人；引用数字须区分原书引用与需当期核对项。",
        src=BOOK_FILE["lesson"] + stem + ".html",
        excerpt=excerpt, contextChars=len(excerpt))


# ---------------------------------------------------------------- 提示词渲染
def context_block(m):
    """浏览器 FDEExpand() 与核验脚本共用的原文摘录块（标记必须逐字一致）。"""
    return "%s\n%s\n%s" % (CTX_BEGIN, m.get("excerpt", ""), CTX_END)


def prompt_text(m, angle, version="v5.0"):
    """渲染一段提示词模板；原文摘录位置留 [[FDE:CTX]]，复制 / 核验时展开。"""
    a = next(x for x in ANGLES if x["key"] == angle)
    src = m["src"]
    if m["book"] == "lesson":
        book_desc = "《企业级智能体交付实战手册》配套 · 19 节课程逐节笔记（公开资料本地副本，版权归原权利人）"
    elif m["book"] == "book3":
        book_desc = ("《开源课程精读模块》· 对《前线部署工程师》开源版（fde4.ai/book/）的逐章解读与对照；"
                     "原文版权归原权利人，本模块为原创分析；引用数字须区分原书引用 / 公开报道 / 需当期核对")
    else:
        book_desc = "《企业级智能体交付实战手册》%s（跨行业 / 厂商中立 / 独立学习整理，非官方教材）" % version
    concepts = "、".join(m["concepts"]) if m["concepts"] else "（本模块以流程与判断为主）"
    L = []
    L.append("# 角色\n" + ROLE)
    L.append("\n# 手册原文（本次粘贴给你的权威上下文）\n"
             "下面是我从《企业级智能体交付实战手册》「%s」模块里**逐字粘贴**的原文摘录，"
             "这就是「我的手册」在这一节具体写了什么。请**优先依据它作答**，"
             "逐条对齐其中的定义、口径、步骤与验收判据；不要凭书名、章节号或常识猜测未粘贴的内容。"
             "\n你无法访问我的本地文件、内网或未提供的链接；若原文不足以回答，先向我索要该节完整原文。"
             % m["title"])
    L.append(CTX_TOKEN)
    L.append("（注：原文为 Markdown 摘录，表格与清单保留原结构；因单次粘贴长度所限，"
             "未收录的部分请标注【需查当期官方文档或客户确认】，不要替我补全。）")
    L.append("\n# 模块元数据（辅助定位，不是内容本身）\n"
             "- 资料：%s\n"
             "- 模块位置：%s › %s%s\n"
             "- 认知层：%s ｜ 能力域：%s\n"
             "- 本模块关键概念：%s\n"
             "- 本模块要回答的核心问题：%s\n"
             "- 建议的可验收产出物：%s\n"
             "- 出处锚点：%s（我在本地 / 部署站点回查用；除非我在文末给出可访问地址且你支持联网浏览，"
             "否则不要尝试打开）"
             % (book_desc, m["bookName"], m["loc"] or "—", " › " + m["title"] if m["title"] else "",
                m["layer"], m["domain"], concepts, m["question"], m["deliverable"], src))
    if m.get("note"):
        L.append("- 我的补充关注点：" + m["note"])
    L.append("\n# 本次追问角度：%s %s · %s\n%s"
             % (a["icon"], a["name"], a["label"], a["focus"]))
    L.append("\n请依次回答：")
    for i, q in enumerate(a["qs"], 1):
        L.append("%d. %s" % (i, q))
    L.append("\n# 输出要求\n" + CONSTRAINTS)
    L.append("\n（本提示词由「企业级智能体交付实战手册 %s · 细节追问」生成；"
             "若你发现我粘贴的原文与你的知识有矛盾，请直接指出并以上述原文为准，而不是替我补全。）" % version)
    return "\n".join(L)


def prompt_full(m, angle, version="v5.0"):
    """展开原文摘录后的最终提示词：浏览器复制到的就是这段文本。"""
    return prompt_text(m, angle, version).replace(CTX_TOKEN, context_block(m))


def site_note(m, base=""):
    """可选的部署链接回查说明；链接永远只作辅助，不替代粘贴的原文。"""
    if not base:
        return SITE_NONE_NOTE
    return ("\n# 资料回查（可选）\n"
            "- 我部署的公开地址：%s/%s\n"
            "- 该链接仅供你（若支持联网浏览）回查，不替代上面粘贴的手册原文；"
            "若无法访问，请完全依据原文作答，不要凭链接猜内容。"
            % (base.rstrip("/"), m.get("src", "")))


def payload_obj(modules, version="v5.0"):
    """构建内嵌数据对象：模块含原文摘录 + 5 段提示词模板，并带会话级上下文。"""
    d = {}
    for m in modules:
        d[m["id"]] = dict(m, prompts={
            a["key"]: prompt_text(m, a["key"], version) for a in ANGLES})
    return {"version": version, "angles": ANGLES, "modules": d,
            "token": CTX_TOKEN, "begin": CTX_BEGIN, "end": CTX_END,
            "lite": LITE_NOTE, "primer": SESSION_PRIMER,
            "siteKey": SITE_KEY, "siteNone": SITE_NONE_NOTE}


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False,
                      separators=(",", ":")).replace("</", "<\\/")


def payload(modules, version="v5.0"):
    """内嵌到 HTML 的 JSON 字符串。"""
    return dumps(payload_obj(modules, version))


# ---------------------------------------------------------------- 共享 UI
ASK_CSS = r"""
/* ===== 细节追问组件（自带主题变量，可注入任意页面而不污染原样式） ===== */
:root{
  --ask-card:#ffffff;--ask-bg:#f5f5f7;--ask-text:#1d1d1f;--ask-text2:#424245;
  --ask-muted:#6e6e73;--ask-line:#e5e5ea;--ask-line2:#d2d2d7;
  --ask-accent:#0071e3;--ask-soft:#eaf3ff;--ask-shadow:0 18px 50px rgba(0,0,0,.16);
}
html[data-theme="dark"]{
  --ask-card:#20232a;--ask-bg:#16181d;--ask-text:#f2f2f5;--ask-text2:#c9ccd3;
  --ask-muted:#9297a2;--ask-line:#2f333c;--ask-line2:#3d424d;
  --ask-accent:#63adff;--ask-soft:#172c47;--ask-shadow:0 18px 50px rgba(0,0,0,.6);
}
.ask-btn{display:inline-flex;align-items:center;gap:4px;float:right;margin:2px 0 0 10px;
  font:inherit;font-size:11px;font-weight:700;letter-spacing:.01em;line-height:1.5;
  padding:3px 9px;border:1px solid var(--ask-line2);border-radius:999px;
  background:var(--ask-card);color:var(--ask-muted);cursor:pointer;
  white-space:nowrap;vertical-align:middle;transition:.16s;font-family:inherit}
.ask-btn:hover,.ask-btn:focus{border-color:var(--ask-accent);color:var(--ask-accent);
  background:var(--ask-soft);outline:none}
.ask-btn::before{content:"🔍";font-size:11px}
h1 .ask-btn,h4 .ask-btn{font-size:10.5px}
.ask-entry{margin:0 0 14px;text-align:right}
.ask-entry .ask-btn{float:none;font-size:12.5px;padding:7px 14px}
.ask-mask{position:fixed;inset:0;background:rgba(0,0,0,.42);z-index:310}
.ask-pop{position:fixed;z-index:311;right:24px;top:76px;width:min(560px,calc(100vw - 36px));
  max-height:min(78vh,760px);overflow:auto;background:var(--ask-card);color:var(--ask-text);
  border:1px solid var(--ask-line);border-radius:18px;box-shadow:var(--ask-shadow);
  padding:0 0 18px;font-size:13.5px;line-height:1.7}
.ask-ph{position:sticky;top:0;background:var(--ask-card);padding:15px 18px 11px;
  border-bottom:1px solid var(--ask-line);display:flex;gap:10px;align-items:flex-start;z-index:2}
.ask-ph .t{flex:1;min-width:0}
.ask-ph .k{font-size:10.5px;font-weight:800;letter-spacing:.12em;color:var(--ask-accent)}
.ask-ph .ask-h3{font-size:16.5px;line-height:1.4;margin:4px 0 3px;letter-spacing:-.01em;font-weight:700}
.ask-ph .loc{font-size:11.5px;color:var(--ask-muted);word-break:break-all}
.ask-x{width:30px;height:30px;flex:none;border:1px solid var(--ask-line);border-radius:9px;
  background:var(--ask-bg);color:var(--ask-text2);cursor:pointer;font-size:15px;font-family:inherit}
.ask-x:hover{border-color:var(--ask-accent);color:var(--ask-accent)}
.ask-angles{display:flex;flex-wrap:wrap;gap:6px;padding:13px 18px 4px}
.ask-angles button{font:inherit;font-size:12px;padding:6px 11px;border-radius:999px;cursor:pointer;
  border:1px solid var(--ask-line);background:var(--ask-bg);color:var(--ask-text2);font-family:inherit}
.ask-angles button:hover{border-color:var(--ask-accent)}
.ask-angles button.on{background:var(--ask-soft);border-color:var(--ask-accent);
  color:var(--ask-accent);font-weight:800}
.ask-focus{margin:8px 18px 0;font-size:12.3px;color:var(--ask-muted)}
.ask-ctx{margin:9px 18px 0;padding:8px 11px;border:1px solid var(--ask-accent);
  border-radius:10px;background:var(--ask-soft);color:var(--ask-text2);
  font-size:11.6px;line-height:1.65}
.ask-body{padding:10px 18px 0}
#askText{display:block;width:100%;min-height:300px;height:42vh;resize:vertical;
  padding:13px 14px;border:1px solid var(--ask-line);border-radius:12px;
  background:var(--ask-bg);color:var(--ask-text);font:12.5px/1.75 ui-monospace,SFMono-Regular,
  "SF Mono",Menlo,Consolas,"PingFang SC",monospace;outline:none;white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word;overflow:auto}
#askText:focus{border-color:var(--ask-accent);box-shadow:0 0 0 3px var(--ask-soft)}
.ask-acts{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:12px 18px 0}
.ask-acts button,.ask-acts a{font:inherit;font-size:12.5px;font-weight:700;padding:8px 14px;
  border-radius:10px;border:1px solid var(--ask-line2);background:var(--ask-card);
  color:var(--ask-text2);cursor:pointer;text-decoration:none;font-family:inherit}
.ask-acts button.pri{background:var(--ask-accent);border-color:var(--ask-accent);color:#fff}
.ask-acts button.mini{font-size:11.5px;font-weight:600;padding:6px 10px}
.ask-acts button:hover,.ask-acts a:hover{border-color:var(--ask-accent);color:var(--ask-accent)}
.ask-acts button.pri:hover{color:#fff;opacity:.9}
.ask-tip{font-size:11.5px;color:var(--ask-muted);margin-left:auto}
.ask-foot{padding:12px 18px 0;font-size:11.5px;color:var(--ask-muted);line-height:1.75}
@media(max-width:700px){
  .ask-btn{float:none;margin:6px 0 0;font-size:10.5px}
  .ask-pop{right:0;left:0;bottom:0;top:auto;width:auto;max-height:86vh;border-radius:18px 18px 0 0}
  #askText{height:38vh;min-height:220px;font-size:12px}
  .ask-tip{margin-left:0;width:100%}
}
@media print{.ask-btn,.ask-mask,.ask-pop{display:none!important}}
"""

ASK_POP_HTML = (
    '<div class="ask-mask" id="askMask" hidden></div>'
    '<div class="ask-pop" id="askPop" hidden role="dialog" aria-modal="true" '
    'aria-labelledby="askTitle">'
    '<div class="ask-ph"><div class="t"><div class="k">DETAIL PROBE · 细节追问提示词</div>'
    '<div class="ask-h3" id="askTitle"></div><div class="loc" id="askLoc"></div></div>'
    '<button class="ask-x" id="askClose" title="关闭">✕</button></div>'
    '<div class="ask-angles" id="askAngles"></div>'
    '<div class="ask-focus" id="askFocus"></div>'
    '<div class="ask-ctx" id="askCtxInfo"></div>'
    '<div class="ask-body"><textarea id="askText" readonly spellcheck="false"></textarea></div>'
    '<div class="ask-acts"><button class="pri" id="askCopy">📋 复制完整上下文包</button>'
    '<button class="mini" id="askLite">精简版</button>'
    '<button class="mini" id="askLink">带链接版</button>'
    '<button class="mini" id="askPrimer">会话开场白</button>'
    '<button id="askSelect">全选</button><a id="askSrc" href="#">↗ 回看本模块</a>'
    '<span class="ask-tip" id="askTip">默认已附本模块原文，粘贴到任意 AI 即可</span></div>'
    '<div class="ask-foot">完整上下文包 = <b>本模块手册原文摘录</b> + 模块元数据 + 追问角度 + 输出要求；'
    '不需要部署网站、不需要联网、不需要先上传文件。若 AI 已加载本手册文件可用「精简版」；'
    '部署后可在提示词库页填公开地址用「带链接版」，链接只作回查辅助、不替代粘贴的原文。'
    '换角度即换一段；AI 回答请以本手册与当期官方文档复核，不构成结论。</div></div>'
)

# 共享展开逻辑：阅读页弹窗与独立提示词库页使用同一套函数，保证复制出去的文本一致
ASK_CORE_JS = r"""
/* ===== 上下文自足提示词 · 共享展开层（生成期占位，浏览器端按同一标记展开） ===== */
function FDEData(){return window.__FDE_ASK__||{};}
function FDECtxBlock(m){
  var d=FDEData();
  return (d.begin||'<<<FDE_MODULE_EXCERPT_BEGIN>>>')+'\n'+(m.excerpt||'')+'\n'+
         (d.end||'<<<FDE_MODULE_EXCERPT_END>>>');
}
function FDELite(){
  return FDEData().lite||'（本次未随附手册原文；若你已加载本手册文件请据其回答，否则先向我索要原文。）';
}
function FDESiteBase(){
  var d=FDEData(),k=d.siteKey||'fde_site_base',v='';
  try{if(window.localStorage)v=window.localStorage.getItem(k)||'';}catch(e){}
  return String(window.__FDE_SITE_BASE__||v||'').replace(/\/+$/,'');
}
function FDESiteNote(m){
  var b=FDESiteBase();
  if(!b)return FDEData().siteNone||
    '\n# 资料回查（可选）\n- 我尚未配置部署地址；本次请完全依据上面粘贴的手册原文，不要尝试访问任何链接。';
  return '\n# 资料回查（可选）\n- 我部署的公开地址：'+b+'/'+(m.src||'')+
    '\n- 该链接仅供你（若支持联网浏览）回查，不替代上面粘贴的手册原文；若无法访问，请完全依据原文作答，不要凭链接猜内容。';
}
function FDEExpand(m,angle,mode){
  var d=FDEData(),t=(m.prompts&&m.prompts[angle])||'',tok=d.token||'[[FDE:CTX]]';
  var block=(mode==='lite')?FDELite():FDECtxBlock(m);
  var out=t.split(tok).join(block);
  if(mode==='link')out+=FDESiteNote(m);
  return out;
}
function FDEPrimer(){return FDEData().primer||'';}
"""

ASK_JS = ASK_CORE_JS + r"""
(function(){
'use strict';
var DATA=window.__FDE_ASK__||{modules:{},angles:[]}, curId=null, curAngle='concept';
function $(i){return document.getElementById(i);}
var mask=$('askMask'),pop=$('askPop'),box=$('askAngles'),ta=$('askText');
if(!mask||!pop)return;
function angles(){/* 只构建一次：切换角度时不重建 DOM，保留焦点与外部引用 */
  if(box.childNodes.length)return;
  DATA.angles.forEach(function(a){
    var b=document.createElement('button');b.type='button';
    b.textContent=a.icon+' '+a.name;b.setAttribute('data-k',a.key);
    box.appendChild(b);
  });
}
function markAngle(){
  Array.prototype.forEach.call(box.querySelectorAll('button'),function(b){
    var on=b.getAttribute('data-k')===curAngle;
    b.className=on?'on':'';
    b.style.background=on?'var(--ask-soft)':'';
    b.style.borderColor=on?'var(--ask-accent)':'';
    b.style.color=on?'var(--ask-accent)':'';
  });
}
function paint(){
  var m=DATA.modules[curId];if(!m)return;
  $('askTitle').textContent=m.title||'细节追问';
  $('askLoc').textContent=m.bookName+' › '+(m.loc||'—')+' ｜ '+m.layer+' ｜ '+m.domain;
  var a=null;DATA.angles.forEach(function(x){if(x.key===curAngle)a=x;});
  $('askFocus').textContent=a?(a.focus+'（'+a.label+'）'):'';
  ta.value=FDEExpand(m,curAngle,'full');
  var info=$('askCtxInfo');
  if(info){info.textContent='✅ 已附本模块手册原文摘录 '+String(m.excerpt||'').length+
    ' 字 ｜ 完整上下文包可独立使用：无需部署网站、无需联网、无需先上传文件';}
  var s=$('askSrc');
  if(s){s.setAttribute('href',m.src||'#');s.style.display=m.src?'':'none';}
  angles();markAngle();
}
function open(id){
  curId=id;curAngle='concept';
  if(!DATA.modules[id])return;
  paint();mask.hidden=false;pop.hidden=false;
  try{document.body.style.overflow='hidden';}catch(e){}
  setTimeout(function(){try{ta.focus();ta.setSelectionRange(0,0);
    ta.scrollTop=0;ta.scrollLeft=0;}catch(e){}},30);
}
function close(){
  mask.hidden=true;pop.hidden=true;curId=null;
  try{document.body.style.overflow='';}catch(e){}
}
function toast(s){
  var t=$('askTip');if(!t)return;t.textContent=s;
  clearTimeout(window.__ASK_T__);window.__ASK_T__=setTimeout(function(){
    t.textContent='默认已附本模块原文，粘贴到任意 AI 即可';},3200);
}
function copy(txt,msg){
  if(!txt){toast('没有可复制的内容');return;}
  function fallback(){
    ta.removeAttribute('readonly');ta.value=txt;ta.select();ta.setSelectionRange(0,txt.length);
    var ok=false;try{ok=document.execCommand('copy');}catch(e){}
    ta.setAttribute('readonly','readonly');
    toast(ok?'✓ 已复制（兼容模式）':'请手动全选后按 Ctrl/Cmd+C 复制');
    setTimeout(function(){if(curId&&DATA.modules[curId])paint();},1400);
  }
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(txt).then(function(){toast(msg);},fallback);
  }else fallback();
}
function bind(){
  document.addEventListener('click',function(e){
    var b=e.target;
    while(b&&b!==document.body&&b.tagName!=='BUTTON')b=b.parentNode;
    if(!b||b.tagName!=='BUTTON')return;
    if(b.classList.contains('ask-btn')){open(b.getAttribute('data-ask'));return;}
    if(b.parentNode&&b.parentNode.id==='askAngles'){
      curAngle=b.getAttribute('data-k');paint();return;
    }
    var m=DATA.modules[curId];
    if(b.id==='askCopy'){copy(FDEExpand(m,curAngle,'full'),'✓ 完整上下文包已复制（含手册原文）');return;}
    if(b.id==='askLite'){copy(FDEExpand(m,curAngle,'lite'),'✓ 精简版已复制（适用于已加载手册文件的 AI）');return;}
    if(b.id==='askLink'){
      copy(FDEExpand(m,curAngle,'link'),FDESiteBase()?
        '✓ 带链接版已复制（链接仅作回查辅助）':'✓ 未配置部署地址，已复制完整上下文包 + 不访问链接说明');
      return;
    }
    if(b.id==='askPrimer'){copy(FDEPrimer(),'✓ 会话开场白已复制，先发给 AI 再发追问');return;}
    if(b.id==='askSelect'){ta.focus();ta.select();return;}
    if(b.id==='askClose'){close();return;}
  });
  mask.addEventListener('click',close);
  document.addEventListener('keydown',function(e){
    if(e.key==='Escape'&&!pop.hidden)close();
  });
}
bind();
window.__FDE_ASK_OPEN__=open;
})();
"""

# ---------------------------------------------------------------- 独立提示词库页
LIB_CSS = r"""
/* 库页是独立 page_shell 页面，必须自带 body 主题底色，否则深色模式下会白底浅字 */
body{background:var(--sx-bg);color:var(--sx-ink);
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","PingFang SC","Microsoft YaHei",sans-serif;
  font-size:15px;line-height:1.75;-webkit-font-smoothing:antialiased;
  -webkit-text-size-adjust:100%;margin:0}
*{box-sizing:border-box}
.ak-wrap{max-width:1120px;margin:0 auto;padding:0 26px}
.ak-hero{padding:52px 0 30px}
.ak-hero h1{font-size:clamp(28px,4vw,42px);letter-spacing:-.035em;line-height:1.2;margin:12px 0 10px}
.ak-hero h1 span{background:var(--sx-grad);-webkit-background-clip:text;background-clip:text;
  color:transparent;-webkit-text-fill-color:transparent}
.ak-hero p{color:var(--sx-ink2);font-size:15px;max-width:760px;margin:0;line-height:1.9}
.ak-steps{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:24px 0 0}
.ak-steps div{background:var(--sx-card);border:1px solid var(--sx-line);border-radius:14px;
  padding:14px 16px;box-shadow:var(--sx-sh1)}
.ak-steps b{display:block;font-size:11px;letter-spacing:.1em;color:var(--sx-a1);margin-bottom:5px}
.ak-steps span{font-size:12.8px;color:var(--sx-ink2);line-height:1.7}
.ak-tools{background:var(--sx-card);border:1px solid var(--sx-line);border-radius:16px;
  padding:16px 18px;margin:8px 0 20px;box-shadow:var(--sx-sh1)}
.ak-tools input{width:100%;padding:10px 14px;border:1px solid var(--sx-line);border-radius:10px;
  background:var(--sx-bg);color:var(--sx-ink);font:14px inherit;outline:none;font-family:inherit}
.ak-tools input:focus{border-color:var(--sx-a1);box-shadow:0 0 0 3px var(--sx-soft)}
.ak-filters{display:flex;flex-wrap:wrap;gap:14px;margin-top:13px}
.ak-filters .grp{display:flex;flex-wrap:wrap;gap:5px;align-items:center}
.ak-filters .lab{font-size:11px;font-weight:800;letter-spacing:.08em;color:var(--sx-mute);margin-right:4px}
.ak-filters button{font:12.2px inherit;padding:5px 11px;border-radius:999px;cursor:pointer;
  border:1px solid var(--sx-line);background:var(--sx-bg);color:var(--sx-ink2);font-family:inherit}
.ak-filters button.on{background:var(--sx-soft);border-color:var(--sx-a1);color:var(--sx-a1);font-weight:700}
.ak-count{font-size:12.5px;color:var(--sx-mute);margin:12px 0 0}
.ak-list{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-bottom:28px}
.ak-card{background:var(--sx-card);border:1px solid var(--sx-line);border-radius:16px;
  padding:16px 18px;box-shadow:var(--sx-sh1);display:flex;flex-direction:column}
.ak-card h3{font-size:15.5px;line-height:1.5;margin:0 0 6px;letter-spacing:-.01em}
.ak-card .meta{font-size:11.3px;color:var(--sx-mute);line-height:1.7;margin-bottom:9px}
.ak-card .q{font-size:12.8px;color:var(--sx-ink2);background:var(--sx-bg2);
  border-left:3px solid var(--sx-a2);border-radius:0 8px 8px 0;padding:8px 11px;margin:0 0 10px}
.ak-card .tags{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:11px}
.ak-card .tags span{font-size:10.8px;color:var(--sx-mute);background:var(--sx-bg2);
  border:1px solid var(--sx-line);border-radius:999px;padding:2px 8px}
.ak-card .angles{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:11px}
.ak-card .angles button{font:11.5px inherit;padding:4px 9px;border-radius:8px;cursor:pointer;
  border:1px solid var(--sx-line);background:var(--sx-bg);color:var(--sx-ink2);font-family:inherit}
.ak-card .angles button.on{background:var(--sx-soft);border-color:var(--sx-a1);color:var(--sx-a1);font-weight:700}
.ak-card textarea{width:100%;height:150px;resize:vertical;padding:10px 12px;border-radius:10px;
  border:1px solid var(--sx-line);background:var(--sx-bg2);color:var(--sx-ink);
  font:11.5px/1.6 ui-monospace,SFMono-Regular,Menlo,Consolas,"PingFang SC",monospace;
  white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word;outline:none;flex:1}
.ak-card textarea:focus{border-color:var(--sx-a1)}
.ak-card .go{display:flex;gap:7px;margin-top:10px;flex-wrap:wrap}
.ak-card .go button,.ak-card .go a{font:12px inherit;padding:7px 12px;border-radius:9px;cursor:pointer;
  border:1px solid var(--sx-line2);background:var(--sx-card);color:var(--sx-ink2);
  text-decoration:none;font-family:inherit}
.ak-card .go button.pri{background:var(--sx-a1);border-color:var(--sx-a1);color:#fff;font-weight:700}
.ak-card .go .hint{font-size:11px;color:var(--sx-mute);margin-left:auto;align-self:center}
.ak-note{background:var(--sx-bg2);border:1px solid var(--sx-line);border-radius:16px;
  padding:18px 20px;margin:0 0 40px;font-size:13px;color:var(--sx-ink2);line-height:1.9}
.ak-note b{color:var(--sx-ink)}
.ak-heroact{display:flex;flex-wrap:wrap;gap:9px;align-items:center;margin-top:18px}
.ak-heroact button{font:13px inherit;font-weight:700;padding:9px 16px;border-radius:11px;cursor:pointer;
  border:1px solid var(--sx-a1);background:var(--sx-a1);color:#fff;font-family:inherit}
.ak-heroact button.ghost{background:var(--sx-card);color:var(--sx-a1)}
.ak-heroact span{font-size:11.8px;color:var(--sx-mute)}
.ak-primer{margin:16px 0 0;border:1px solid var(--sx-line);border-radius:13px;
  background:var(--sx-card);padding:12px 16px;font-size:12.5px}
.ak-primer summary{cursor:pointer;font-weight:700;color:var(--sx-ink)}
.ak-primer pre{white-space:pre-wrap;overflow-wrap:anywhere;font:11.5px/1.75 inherit;
  color:var(--sx-ink2);margin:12px 0 0;max-height:340px;overflow:auto}
.ak-site{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:13px;
  padding-top:13px;border-top:1px dashed var(--sx-line)}
.ak-site label{font-size:12px;font-weight:700;color:var(--sx-ink2)}
.ak-site input{flex:1;min-width:210px;width:auto;padding:8px 11px;font-size:12.5px}
.ak-site button{font:12px inherit;font-weight:700;padding:8px 14px;border-radius:9px;cursor:pointer;
  border:1px solid var(--sx-a1);background:var(--sx-soft);color:var(--sx-a1);font-family:inherit}
.ak-site .st{font-size:11.5px;color:var(--sx-mute);width:100%}
.ak-card .go button.mini{font-size:11.2px;padding:6px 9px;font-weight:600}
.ak-card .ctx{font-size:10.8px;color:var(--sx-mute);align-self:center;margin-left:auto}
@media(max-width:900px){.ak-steps{grid-template-columns:repeat(2,1fr)}.ak-list{grid-template-columns:1fr}}
@media(max-width:600px){.ak-wrap{padding:0 16px}.ak-steps{grid-template-columns:1fr 1fr}}
@media print{.ak-tools,.ak-card .angles,.ak-card .go{display:none!important}
  .ak-card textarea{height:auto;min-height:180px}.ak-list{grid-template-columns:1fr 1fr}}
"""

LIB_JS = ASK_CORE_JS + r"""
(function(){
'use strict';
var D=window.__FDE_ASK__||{modules:{},angles:[]};
var q=document.getElementById('akQ'),list=document.getElementById('akList'),
    count=document.getElementById('akCount'),fbox=document.getElementById('akFilters');
var F={book:'全部',layer:'全部',angle:D.angles.length?D.angles[0].key:'concept'};
function esc(s){return String(s).replace(/[&<>"']/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function card(m){
  var d=document.createElement('div');d.className='ak-card';
  d.setAttribute('data-id',m.id);d.setAttribute('data-book',m.bookName);
  d.setAttribute('data-layer',m.layer.split(' ')[0]);
  d.setAttribute('data-s',(m.title+' '+m.loc+' '+m.domain+' '+m.concepts.join(' ')+' '+m.question).toLowerCase());
  var tags=m.concepts.slice(0,6).map(function(x){return '<span>'+esc(x)+'</span>';}).join('');
  var ang=D.angles.map(function(a){return '<button data-a="'+a.key+'"'+
    (a.key===F.angle?' class="on"':'')+'>'+a.icon+' '+a.name+'</button>';}).join('');
  d.setAttribute('data-angle',F.angle);
  d.innerHTML='<h3>'+esc(m.title)+'</h3>'+
    '<div class="meta">'+esc(m.bookName)+' › '+esc(m.loc||'—')+' ｜ '+esc(m.layer)+
    ' ｜ '+esc(m.domain)+(m.curated?' ｜ ★ 精编':'')+'</div>'+
    '<div class="q">'+esc(m.question)+'</div>'+
    '<div class="tags">'+tags+'</div><div class="angles">'+ang+'</div>'+
    '<textarea readonly spellcheck="false"></textarea>'+
    '<div class="go"><button class="pri" data-act="copy">📋 完整上下文包</button>'+
    '<button class="mini" data-act="lite">精简版</button>'+
    '<button class="mini" data-act="link">带链接版</button>'+
    '<a class="back">↗ 回看本模块</a>'+
    '<span class="ctx">已附原文 '+String(m.excerpt||'').length+' 字</span></div>';
  var back=d.querySelector('a.back');back.setAttribute('href',m.src||'#');
  var ta=d.querySelector('textarea');ta.value=FDEExpand(m,F.angle,'full');
  return d;
}
var cards=[];
Object.keys(D.modules).forEach(function(k){var c=card(D.modules[k]);cards.push(c);list.appendChild(c);});
function run(){
  var v=(q.value||'').trim().toLowerCase(),n=0;
  cards.forEach(function(c){
    var ok=(F.book==='全部'||c.getAttribute('data-book')===F.book)&&
           (F.layer==='全部'||c.getAttribute('data-layer')===F.layer)&&
           (!v||c.getAttribute('data-s').indexOf(v)>-1);
    c.style.display=ok?'flex':'none';if(ok)n++;
  });
  count.textContent='显示 '+n+' / '+cards.length+' 个学习点 ｜ 每个学习点 5 个追问角度，共 '+
    (cards.length*D.angles.length)+' 段可复制提示词';
}
q.addEventListener('input',run);
fbox.addEventListener('click',function(e){
  var b=e.target;while(b&&b!==fbox&&b.tagName!=='BUTTON')b=b.parentNode;
  if(!b||b.tagName!=='BUTTON')return;
  var g=b.getAttribute('data-g'),v=b.getAttribute('data-v');
  if(!g)return;F[g]=v;
  fbox.querySelectorAll('button[data-g="'+g+'"]').forEach(function(x){
    x.classList.toggle('on',x===b);});
  if(g==='angle'){
    cards.forEach(function(c){
      var m=D.modules[c.getAttribute('data-id')];
      c.setAttribute('data-angle',v);
      c.querySelector('textarea').value=FDEExpand(m,v,'full');
      c.querySelectorAll('.angles button').forEach(function(x){
        x.classList.toggle('on',x.getAttribute('data-a')===v);});
    });
  }
  run();
});
list.addEventListener('click',function(e){
  var b=e.target;while(b&&b!==list&&b.tagName!=='BUTTON')b=b.parentNode;
  if(!b||b.tagName!=='BUTTON')return;
  var c=b.closest('.ak-card');if(!c)return;
  if(b.getAttribute('data-a')){
    var v=b.getAttribute('data-a'),m=D.modules[c.getAttribute('data-id')];
    c.setAttribute('data-angle',v);
    c.querySelector('textarea').value=FDEExpand(m,v,'full');
    c.querySelectorAll('.angles button').forEach(function(x){
      x.classList.toggle('on',x===b);});
    return;
  }
  var act=b.getAttribute('data-act');
  if(act==='copy'||act==='lite'||act==='link'){
    var mm=D.modules[c.getAttribute('data-id')],ang=c.getAttribute('data-angle')||F.angle;
    var ta=c.querySelector('textarea'),txt=FDEExpand(mm,ang,act==='copy'?'full':act);
    var label=b.textContent;
    function fb(){ta.removeAttribute('readonly');ta.value=txt;ta.select();
      var ok=false;try{ok=document.execCommand('copy');}catch(x){}
      ta.setAttribute('readonly','readonly');b.textContent=ok?'✓ 已复制':'请手动复制';
      setTimeout(function(){ta.value=FDEExpand(mm,ang,'full');b.textContent=label;},2200);}
    if(navigator.clipboard&&navigator.clipboard.writeText){
      navigator.clipboard.writeText(txt).then(function(){b.textContent='✓ 已复制';
        setTimeout(function(){b.textContent=label;},2200);},fb);
    }else fb();
  }
});
/* 会话开场白 + 可选部署地址：本地保存，不发起任何网络请求 */
var primerBtn=document.getElementById('akPrimer');
if(primerBtn)primerBtn.addEventListener('click',function(){
  var t=FDEPrimer(),self=this,lab=self.textContent;
  function fb(){var x=document.createElement('textarea');x.value=t;document.body.appendChild(x);
    x.select();var ok=false;try{ok=document.execCommand('copy');}catch(e){}
    document.body.removeChild(x);self.textContent=ok?'✓ 已复制':'请手动复制';
    setTimeout(function(){self.textContent=lab;},2200);}
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(t).then(function(){self.textContent='✓ 已复制';
      setTimeout(function(){self.textContent=lab;},2200);},fb);
  }else fb();
});
var siteIn=document.getElementById('akSite'),siteBtn=document.getElementById('akSiteSave'),
    siteSt=document.getElementById('akSiteState');
function siteKey(){return (D.siteKey||'fde_site_base');}
if(siteIn){
  try{siteIn.value=window.localStorage.getItem(siteKey())||window.__FDE_SITE_BASE__||'';}catch(e){}
  if(siteSt)siteSt.textContent=siteIn.value?'当前已配置部署地址；「带链接版」会附上公开回查链接。':
    '未配置也可正常使用；完整上下文包不依赖网站。';
}
if(siteBtn)siteBtn.addEventListener('click',function(){
  var v=(siteIn?siteIn.value:'').trim().replace(/\/+$/,'');
  if(v && !/^https?:\/\//i.test(v))v='https://'+v;
  window.__FDE_SITE_BASE__=v;
  try{window.localStorage.setItem(siteKey(),v);}catch(e){}
  if(siteIn)siteIn.value=v;
  if(siteSt)siteSt.textContent=v?'已保存：'+v+'（仅作回查辅助，不替代粘贴的原文）':
    '已清空；「带链接版」将提示 AI 不要访问任何链接。';
});
run();
})();
"""


def build_library_page(modules, version="v5.0"):
    """生成独立《细节追问提示词库.html》（全站导航外壳 + 可检索卡片）。"""
    import site_chrome as sc
    from pathlib import Path
    n = len(modules)
    n_prompt = n * len(ANGLES)
    books = ["全部", "主手册", "速查手册", "开源课程精读"]
    layers = ["全部", "L0", "L1", "L2", "L3", "L4", "L5", "全层"]

    def fgrp(label, key, vals):
        bs = "".join('<button data-g="%s" data-v="%s" class="%s">%s</button>'
                     % (key, ihtml.escape(v, quote=True),
                        "on" if i == 0 else "", ihtml.escape(v))
                     for i, v in enumerate(vals))
        return '<div class="grp"><span class="lab">%s</span>%s</div>' % (label, bs)

    angle_grp = ('<div class="grp"><span class="lab">追问角度</span>'
                 + "".join('<button data-g="angle" data-v="%s" class="%s">%s %s</button>'
                           % (a["key"], "on" if i == 0 else "", a["icon"], a["name"])
                           for i, a in enumerate(ANGLES))
                 + '</div>')

    H = []
    H.append('<main><div class="ak-wrap">')
    H.append('<section class="ak-hero" id="anchor-ask"><div class="pt-kicker"><i></i>DETAIL PROBE · '
             'PROMPT LIBRARY · ' + version + '</div>'
             '<h1>把每个学习点，<span>变成一段自带原文的追问</span></h1>'
             '<p>手册里每个章节、每个速查组、每一步学习路径旁都有「🔍 细节追问」。'
             '复制出去的每段提示词都<b>直接粘贴了这一节的手册原文摘录</b>——不是只说「这是我的手册」，'
             '而是把「这一节到底写了什么」一起交给 AI。因此<b>不需要部署网站、不需要联网、不需要先上传文件</b>，'
             '换任意 AI 都能接着这一节往下问。</p>'
             '<div class="ak-heroact">'
             '<button id="akPrimer" type="button">📋 复制会话开场白</button>'
             '<button class="ghost" type="button" onclick="document.getElementById(\'akPrimerText\').open=true">'
             '查看开场白全文</button>'
             '<span>建议先发一次开场白，说明这套手册是什么、怎么问；之后每段提示词可独立使用。</span>'
             '</div>'
             '<details class="ak-primer" id="akPrimerText"><summary>会话开场白全文（可展开核对）</summary>'
             '<pre>' + ihtml.escape(SESSION_PRIMER) + '</pre></details>'
             '<div class="ak-steps">'
             '<div><b>STEP 01</b><span>可选：先复制「会话开场白」发给 AI，建立整册上下文</span></div>'
             '<div><b>STEP 02</b><span>在正文标题旁点「🔍 细节追问」，或在本页搜索模块、选追问角度</span></div>'
             '<div><b>STEP 03</b><span>点「完整上下文包」：手册原文摘录 + 元数据 + 问题 + 输出要求一起复制</span></div>'
             '<div><b>STEP 04</b><span>粘贴到任意 AI；原文不足以回答时，它会先向你索要而不是编内容</span></div>'
             '</div></section>')
    H.append('<div class="ak-tools"><input id="akQ" type="search" '
             'placeholder="搜索章节 / 概念 / 能力域，如「RAG」「验收」「风险」「9.4」">'
             '<div class="ak-filters" id="akFilters">'
             + fgrp("资料", "book", books)
             + fgrp("认知层", "layer", layers)
             + angle_grp +
             '</div>'
             '<div class="ak-site"><label for="akSite">部署地址（可选）</label>'
             '<input id="akSite" type="text" placeholder="https://你的域名/手册目录（不填完全不影响使用）">'
             '<button id="akSiteSave" type="button">保存</button>'
             '<span class="st" id="akSiteState">未配置也可正常使用；完整上下文包不依赖网站。</span></div>'
             '<div class="ak-count" id="akCount"></div></div>')
    H.append('<div class="ak-list" id="akList"></div>')
    H.append('<div class="ak-note"><b>为什么要原文随包？</b>把「3.2 怎么配」直接丢给 AI，'
             '它既不知道你说的是哪本资料、哪一节，也看不到验收口径，只能给通用答案。'
             '只写书名、章节路径、认知层这类「元数据」同样不够——元数据只说明位置，不是内容。'
             '所以本页每段提示词都附了该模块的<b>手册原文摘录</b>，并要求 AI 以粘贴的原文为第一依据、'
             '区分【手册已写明】【它的推断】【需查当期官方文档或客户确认】、禁止编造成效数字，'
             '结尾给可验收产出物与 3 个继续追问的问题。'
             '<br><b>需要部署网站吗？</b>不需要。部署上线只解决「人能访问、能贴链接回查」，'
             '不解决「外部 AI 自动知道手册内容」。只有当你用的 AI 明确支持联网浏览，且你已把站点部署到公网时，'
             '才在上方填写公开地址，用「带链接版」附一个回查链接——链接是辅助，永远不替代粘贴的原文。'
             '若你的 AI 支持文件问答，也可以把 <b>01_主手册_…md / 02_速查手册_…md / 03_开源课程解读.md</b> '
             '上传到会话，之后用「精简版」即可。'
             '<br><b>三种复制模式：</b>① 完整上下文包（默认，任一 AI 通用）；② 精简版（AI 已加载手册文件时更短）；'
             '③ 带链接版（完整包 + 可选公开回查地址）。'
             '<br><b>边界：</b>AI 的回答只是学习辅助，不能替代本手册口径、当期官方文档与客户验收；'
             '题目、答案与判分仍以本手册和题库为准。所有提示词在本地生成与展开，'
             '页面不发起任何网络请求，复制动作只写浏览器剪贴板、不上传任何内容。</div>')
    H.append('</div></main>')

    # page_shell 会自行包一层 <script>，这里必须是纯 JS，不能自带 script 标签
    js = ("\nwindow.__FDE_ASK__=%s;\n%s\n"
          % (payload(modules, version), LIB_JS))

    crumbs = [("门户", "index.html"), ("介绍", "手册展示页.html"),
              ("细节追问提示词库", None)]
    return sc.page_shell(
        "细节追问提示词库 | %d 个学习点 × 5 个角度" % n,
        "%d 个学习点、%d 段自带本模块手册原文摘录的上下文自足提示词，可直接复制到任意 AI，"
        "无需部署网站 / 联网 / 上传文件；支持按资料 / 认知层 / 角度筛选。" % (n, n_prompt),
        "ask", crumbs, "".join(H), extra_css=LIB_CSS, extra_js=js)
