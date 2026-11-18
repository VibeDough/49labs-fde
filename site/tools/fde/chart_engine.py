#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v5.1 声明式 SVG 图表引擎（编译期渲染 · 零运行时依赖）

解决的问题
----------
旧版 11 张图是手写硬编码坐标：框宽 / 行高 / viewBox 高度 / 箭头起止点全部人填，
没有文字宽度测量，导致中文长标题顶出框、副标题溢出、箭头绕到框外、向下箭头只有
6px、象限轴标注与卡片位置互相矛盾。

设计原则
--------
1. **声明式**：图表只描述「有哪些节点、什么关系、什么布局」，不写坐标。
2. **测量驱动**：用真实中文字体（Hiragino Sans GB / PingFang / STHeiti）测量文本
   宽度，自动换行；框高由行数推导，viewBox 高度由内容总高推导。
3. **统一版式**：8px 栅格、统一圆角 / 内边距 / 字号层级 / 语义配色，节点等高对齐。
4. **正交连线**：箭头走明确的水平 / 垂直 / 折线路径，不穿越节点，方向可读。
5. **零运行时**：输出纯静态 SVG，无 <script>、无外链；主题色由 CSS 变量控制，
   支持深色与打印；不依赖浏览器字体加载时序。

两套主题
--------
reader : 供三册阅读器使用，元素带 class（.b/.ba/.band/.t/.s/.h1/.k/.n/...），
         样式定义在 build_html.py 的 .figsvg 规则中。
site   : 供门户 / 介绍 / 站点地图使用，元素带 inline style（var(--sx-*)）。

可移植性
--------
Pillow 可用时用字体精确测量；不可用时自动降级为基于字符类别的 em 宽度估算，
因此核验脚本在任意机器上都能独立重跑，不把 Pillow 变成硬依赖。
"""

from __future__ import annotations

import html as _html
import math
import re

# ------------------------------------------------------------------ 字体测量
_FONT_CANDIDATES = (
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "C:/Windows/Fonts/msyh.ttc",
)
_FONT_FILE = None
_FONT_CACHE: dict[int, object] = {}
try:                                    # 可选依赖：只用于更精确的宽度测量
    from PIL import ImageFont as _ImageFont

    for _p in _FONT_CANDIDATES:
        try:
            _f = _ImageFont.truetype(_p, 14)
            if _f.getlength("中文") > 0:
                _FONT_FILE = _p
                break
        except Exception:
            continue
except Exception:                       # pragma: no cover - 无 Pillow 时降级
    _ImageFont = None

# 安全余量：浏览器实际渲染比字体度量略宽，留出余量杜绝溢出
_SAFETY = 1.06


def has_native_measure() -> bool:
    """是否启用了真实字体测量（核验脚本会据此给出不同提示）。"""
    return _FONT_FILE is not None


def measure(text: str, size: float) -> float:
    """返回文本在给定字号下的像素宽度。"""
    if not text:
        return 0.0
    if _FONT_FILE:
        if size not in _FONT_CACHE:
            _FONT_CACHE[size] = _ImageFont.truetype(_FONT_FILE, int(round(size)))
        return float(_FONT_CACHE[size].getlength(text)) * _SAFETY
    # 降级估算：CJK 全角 1em，拉丁/数字约 .55em，空格 .3em，标点 .5em
    total = 0.0
    for ch in text:
        o = ord(ch)
        if ch == " ":
            total += 0.30
        elif 0x2E80 <= o <= 0x9FFF or 0xFF00 <= o <= 0xFFEF or 0x3000 <= o <= 0x303F:
            total += 1.00
        elif ch.isdigit() or ch.isalpha():
            total += 0.56
        else:
            total += 0.50
    return total * size * _SAFETY


_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+/-]*|\s+|.", re.S)


def wrap(text: str, max_w: float, size: float) -> list[str]:
    """按最大像素宽度自动折行；CJK 逐字、拉丁单词整体不拆。

    支持显式 ``\\n`` 换行；并做「孤字平衡」：若末行只剩一个字符，
    从前一行末尾借一个字符，避免出现「标准模 / 式」这种难看的断行。
    """
    if not text:
        return []
    if max_w <= 0:
        return text.split("\n")
    out: list[str] = []
    for para in text.split("\n"):
        if not para:
            out.append("")
            continue
        if measure(para, size) <= max_w:
            out.append(para)
            continue
        # 空格保留为「可断点」，不再丢弃 —— 否则中文与英文会粘成 Step8-10
        # 行首禁止出现孤立标点（· / 、，等）：宁可让标点贴在前一行末尾
        punct = set("·/、，。；：)）]】")
        lines: list[list[str]] = []
        cur: list[str] = []
        for t in _TOKEN.findall(para):
            if t.isspace():
                if cur and cur[-1] != " ":
                    cur.append(" ")
                continue
            if measure("".join(cur + [t]), size) <= max_w:
                cur.append(t)
            elif t in punct and cur and measure("".join(cur + [t]), size) <= max_w + size:
                # 允许标点带来 ≤1 字符宽的轻微贴边，右侧内边距足以吸收
                cur.append(t)
            else:
                while cur and cur[-1] == " ":
                    cur.pop()
                if cur:
                    lines.append(cur)
                cur = [t]
        while cur and cur[-1] == " ":
            cur.pop()
        if cur:
            lines.append(cur)
        # 孤字平衡：末行只剩一个字符时，从前一行末尾借一个字符
        if len(lines) >= 2:
            last = [x for x in lines[-1] if x != " "]
            prev = lines[-2]
            idx = len(prev) - 1
            while idx >= 0 and prev[idx] == " ":
                idx -= 1
            if len(last) == 1 and idx > 0:
                moved = prev[idx]
                trial = [moved] + lines[-1]
                if measure("".join(trial), size) <= max_w:
                    lines[-2] = prev[:idx]
                    lines[-1] = trial
        out.extend("".join(x) for x in lines)
    return out


# ------------------------------------------------------------------ 版式 token
GRID = 8
PAD = 18                 # 画布内边距
GAP = 18                 # 节点间距（保证箭头有可见长度）
NODE_PAD_X = 14
NODE_PAD_Y = 12
RADIUS = 10
BADGE = 22
F_H1 = 16                # 图主标题
F_TITLE = 14             # 节点标题
F_SUB = 11.5             # 节点副标题
F_BAND = 12.5            # 要点条
F_NOTE = 11.5            # 说明文字
F_KICK = 11              # 眉标
LH_H1 = 23
LH_TITLE = 20
LH_SUB = 17
LH_BAND = 19
LH_NOTE = 18

# reader 主题：全部走既有 .figsvg class，样式在 build_html.py 中统一定义
_READER = {
    "rect": {"b": 'class="b"', "ba": 'class="ba"', "band": 'class="band"',
             "rail": 'class="rail"', "chip": 'class="chip"', "soft": 'class="soft"',
             "ghost": 'class="ghost"'},
    "text": {"h1": 'class="h1"', "t": 'class="t"', "t2": 'class="t2"',
             "s": 'class="s"', "cap": 'class="cap"', "k": 'class="k"',
             "n": 'class="n"', "badge": 'class="n"'},
    "line": {"ln": 'class="ln"', "axis": 'class="axis"', "rail": 'class="rail-ln"'},
    "mark": "",
}

# site 主题：用 --sx-* 变量，避免依赖站点页是否定义了 .figsvg 规则
_SX = {
    "fill_node": "var(--sx-card)", "stroke_node": "var(--sx-line2)",
    "fill_accent": "var(--sx-soft)", "stroke_accent": "var(--sx-a1)",
    "fill_band": "var(--sx-bg2)", "stroke_band": "var(--sx-line)",
    "fill_rail": "var(--sx-soft)", "stroke_rail": "var(--sx-a1)",
    "fill_chip": "var(--sx-a1)",
    "ink": "var(--sx-ink)", "muted": "var(--sx-mute)", "accent": "var(--sx-a1)",
}


def _site_rect(kind: str, rx: int) -> str:
    if kind == "ba":
        fill, stroke, sw = _SX["fill_accent"], _SX["stroke_accent"], 1.5
    elif kind == "band":
        fill, stroke, sw = _SX["fill_band"], _SX["stroke_band"], 1.1
    elif kind in ("rail", "soft"):
        fill, stroke, sw = _SX["fill_rail"], _SX["stroke_rail"], 1.1
    elif kind == "chip":
        fill, stroke, sw = _SX["fill_chip"], _SX["fill_chip"], 0
    elif kind == "ghost":
        fill, stroke, sw = "none", _SX["stroke_band"], 1.0
    else:
        fill, stroke, sw = _SX["fill_node"], _SX["stroke_node"], 1.2
    return ('style="fill:%s;stroke:%s;stroke-width:%s"' % (fill, stroke, sw))


def _site_text(kind: str) -> str:
    if kind == "h1":
        return 'style="fill:%s;font-size:16px;font-weight:800"' % _SX["ink"]
    if kind == "t":
        return 'style="fill:%s;font-size:14px;font-weight:650"' % _SX["ink"]
    if kind == "t2":
        return 'style="fill:%s;font-size:12.5px;font-weight:700"' % _SX["ink"]
    if kind == "cap":
        return 'style="fill:%s;font-size:12px;font-weight:750"' % _SX["accent"]
    if kind == "k":
        return ('style="fill:%s;font-size:11px;font-weight:800;letter-spacing:.08em"'
                % _SX["accent"])
    if kind in ("n", "badge"):
        return 'style="fill:#fff;font-size:11px;font-weight:800"'
    return 'style="fill:%s;font-size:11.5px"' % _SX["muted"]


_SITE = {
    "rect": None, "text": None,
    "line": {"ln": 'style="stroke:%s;stroke-width:1.7;fill:none"' % _SX["accent"],
             "axis": 'style="stroke:%s;stroke-width:1.2;fill:none;stroke-dasharray:4 4"'
                     % _SX["stroke_band"],
             "rail": 'style="stroke:%s;stroke-width:2;fill:none"' % _SX["accent"]},
    "mark": 'style="fill:%s"' % _SX["accent"],
}


def _esc(s: str) -> str:
    return _html.escape(str(s), quote=True)


# ------------------------------------------------------------------ 画布
class Chart:
    """声明式图表画布：所有坐标由布局器推导，viewBox 高度自动收口。"""

    def __init__(self, width: int = 680, theme: str = "reader",
                 pad: int = PAD, marker: str = "ce", aria: str = "示意图"):
        self.W = int(width)
        self.pad = int(pad)
        self.theme = theme
        self.marker = marker
        self.aria = aria
        self.y = float(pad)
        self.parts: list[str] = []
        self.overflows: list[str] = []
        self.stats = {"nodes": 0, "arrows": 0, "texts": 0, "rects": 0}
        self.P = _READER if theme == "reader" else _SITE

    # ---------------- 基础绘制
    def rect(self, x, y, w, h, kind="b", rx=RADIUS):
        attr = self.P["rect"][kind] if self.theme == "reader" else _site_rect(kind, rx)
        self.parts.append('<rect %s x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%d"/>'
                          % (attr, x, y, w, h, rx))
        self.stats["rects"] += 1

    def text(self, x, y, s, kind="t", anchor="start"):
        if not s:
            return
        attr = self.P["text"][kind] if self.theme == "reader" else _site_text(kind)
        self.parts.append('<text %s x="%.1f" y="%.1f" text-anchor="%s">%s</text>'
                          % (attr, x, y, anchor, _esc(s)))
        self.stats["texts"] += 1

    def line(self, x1, y1, x2, y2, kind="ln", marker=False):
        attr = self.P["line"][kind]
        tail = ' marker-end="url(#%s-ar)"' % self.marker if marker else ""
        self.parts.append('<line %s x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"%s/>'
                          % (attr, x1, y1, x2, y2, tail))
        if marker:
            self.stats["arrows"] += 1

    def poly(self, pts, kind="ln", marker=True):
        attr = self.P["line"][kind]
        d = "M" + " L".join("%.1f,%.1f" % (x, y) for x, y in pts)
        tail = ' marker-end="url(#%s-ar)"' % self.marker if marker else ""
        self.parts.append('<path %s d="%s"%s/>' % (attr, d, tail))
        if marker:
            self.stats["arrows"] += 1

    # ---------------- 语义组件
    def header(self, kicker: str, title: str, sub: str = ""):
        """图头：眉标 + 主标题 + 可选副标题。"""
        if kicker:
            self.text(self.pad, self.y + 10, kicker, "cap")
            self.y += 20
        for ln in wrap(title, self.W - 2 * self.pad, F_H1):
            self.text(self.pad, self.y + 15, ln, "h1")
            self.y += LH_H1
        if sub:
            for ln in wrap(sub, self.W - 2 * self.pad, F_NOTE):
                self.text(self.pad, self.y + 13, ln, "s")
                self.y += LH_NOTE
        self.y += 12

    def node(self, x, y, w, title, sub="", kind="b", badge=None,
             align="center", min_h=42, rx=RADIUS):
        """绘制节点，返回实际高度（由文字行数推导）。"""
        badge_w = (BADGE + 8) if badge else 0
        avail = max(40.0, w - 2 * NODE_PAD_X - badge_w)
        tl = wrap(title, avail, F_TITLE)
        sl = wrap(sub, avail, F_SUB) if sub else []
        block = len(tl) * LH_TITLE + (5 if sl else 0) + len(sl) * LH_SUB
        h = max(min_h, 2 * NODE_PAD_Y + block)
        top = y + (h - block) / 2
        self.rect(x, y, w, h, kind, rx)
        left = x + NODE_PAD_X
        if badge:
            # 徽标与首行标题对齐，绝不能垂直居中后压到副标题上
            by = top + (LH_TITLE - BADGE) / 2
            self.rect(x + 10, by, BADGE, BADGE, "chip", BADGE // 2)
            self.text(x + 10 + BADGE / 2, by + 15, str(badge), "badge", "middle")
            left += badge_w
        for ln in tl:
            if measure(ln, F_TITLE) > avail + F_TITLE + 0.6:
                self.overflows.append("主标题 %s (%.1f > %.1f)"
                                      % (ln, measure(ln, F_TITLE), avail))
        for ln in sl:
            # 容差 = 1 个字符宽：用于吸收「标点贴前行」，右侧内边距足以兜住
            if measure(ln, F_SUB) > avail + F_SUB + 0.6:
                self.overflows.append("副标题 %s (%.1f > %.1f)"
                                      % (ln, measure(ln, F_SUB), avail))
        if align == "center":
            tx, anchor = x + badge_w / 2 + w / 2, "middle"
        else:
            tx, anchor = left, "start"
        ty = top + F_TITLE * 0.84
        for ln in tl:
            self.text(tx, ty, ln, "t", anchor)
            ty += LH_TITLE
        if sl:
            ty = top + len(tl) * LH_TITLE + 5 + F_SUB * 0.84
            for ln in sl:
                self.text(tx, ty, ln, "s", anchor)
                ty += LH_SUB
        self.stats["nodes"] += 1
        return h

    def band(self, text, label="", kind="band"):
        """要点条：label 独占一行（蓝色眉标），正文自动换行，层级不混淆。"""
        w = self.W - 2 * self.pad
        padx, pady = 14, 11
        label_h = 19 if label else 0
        lines = wrap(text, w - 2 * padx, F_BAND)
        h = 2 * pady + label_h + len(lines) * LH_BAND
        self.rect(self.pad, self.y, w, h, kind)
        ty = self.y + pady
        if label:
            self.text(self.pad + padx, ty + 12, label, "k")
            ty += label_h
        for ln in lines:
            self.text(self.pad + padx, ty + 12, ln, "t2")
            ty += LH_BAND
        self.y += h + 12
        return h

    def note(self, text, kind="s"):
        """图注说明：自动换行，不画框。"""
        for ln in wrap(text, self.W - 2 * self.pad, F_NOTE):
            self.text(self.pad, self.y + 12, ln, kind)
            self.y += LH_NOTE
        self.y += 8

    def h_arrow(self, x1, x2, y):
        if x2 - x1 >= 6:
            self.line(x1, y, x2, y, "ln", marker=True)

    def v_arrow(self, x, y1, y2):
        if y2 - y1 >= 6:
            self.line(x, y1, x, y2, "ln", marker=True)

    # ---------------- 布局器
    def flow_row(self, items, gap=GAP, badge_start=1, arrows=True, align="center"):
        """等宽横向流程：节点等高对齐，箭头长度由 gap 保证。"""
        x0 = self.pad
        w_all = self.W - 2 * self.pad
        n = len(items)
        w = (w_all - gap * (n - 1)) / n
        y = self.y
        heights = []
        for i, it in enumerate(items):
            badge = (badge_start + i) if it.get("badge", True) else None
            heights.append(self._node_h(w, it, badge))
        h = max(heights)
        for i, it in enumerate(items):
            x = x0 + i * (w + gap)
            badge = (badge_start + i) if it.get("badge", True) else None
            self.node(x, y, w, it["title"], it.get("sub", ""),
                      it.get("kind", "b"), badge, align, h)
            if arrows and i < n - 1:
                self.h_arrow(x + w + 2, x + w + gap - 2, y + h / 2)
        self.y += h + 14
        return {"y": y, "h": h, "w": w, "gap": gap,
                "cx": [x0 + i * (w + gap) + w / 2 for i in range(n)],
                "left": [x0 + i * (w + gap) for i in range(n)],
                "right": [x0 + i * (w + gap) + w for i in range(n)]}

    def _node_h(self, w, it, badge):
        badge_w = (BADGE + 8) if badge else 0
        avail = max(40.0, w - 2 * NODE_PAD_X - badge_w)
        tl = wrap(it["title"], avail, F_TITLE)
        sl = wrap(it.get("sub", ""), avail, F_SUB) if it.get("sub") else []
        return max(42, 2 * NODE_PAD_Y + len(tl) * LH_TITLE +
                   (5 if sl else 0) + len(sl) * LH_SUB)

    def grid_flow(self, items, cols, gap=GAP, badge_start=1, snake=True):
        """网格流程：行内横向箭头；换行走「行间通道」正交折线，不穿越任何节点。"""
        x0 = self.pad
        w_all = self.W - 2 * self.pad
        w = (w_all - gap * (cols - 1)) / cols
        rows = math.ceil(len(items) / cols)
        layout = []
        for r in range(rows):
            chunk = items[r * cols:(r + 1) * cols]
            y = self.y
            hs = [self._node_h(w, it, badge_start + r * cols + i)
                  for i, it in enumerate(chunk)]
            h = max(hs)
            for i, it in enumerate(chunk):
                x = x0 + i * (w + gap)
                self.node(x, y, w, it["title"], it.get("sub", ""),
                          it.get("kind", "b"), badge_start + r * cols + i,
                          "center", h)
                if i < len(chunk) - 1:
                    self.h_arrow(x + w + 2, x + w + gap - 2, y + h / 2)
            last_right = x0 + (len(chunk) - 1) * (w + gap) + w
            layout.append({"y": y, "h": h, "count": len(chunk),
                           "first_x": x0, "last_right": last_right})
            if r < rows - 1 and len(chunk) == cols:
                # 单条连续折线：行末右侧 → 外侧下行 → 行间通道横穿 → 行首上方落下
                lane = y + h + 9
                next_y = lane + 17
                out_x = self.W - self.pad - 2
                self.poly([(last_right + 3, y + h / 2),
                           (out_x, y + h / 2),
                           (out_x, lane),
                           (x0 + w / 2, lane),
                           (x0 + w / 2, next_y - 3)], "ln", marker=True)
                self.y = next_y
            else:
                self.y = y + h + 16
        return layout

    def layer_rows(self, rows, col_widths, gap=12, head=None, rail=False):
        """多列分层表：每列独立宽度、每行等高、可选表头与左侧进度轨。"""
        x0 = self.pad
        total = self.W - 2 * self.pad - (len(col_widths) - 1) * gap
        scale = total / sum(col_widths)
        widths = [c * scale for c in col_widths]
        xs = [x0]
        for w in widths[:-1]:
            xs.append(xs[-1] + w + gap)
        if head:
            hy = self.y
            hh = 26
            for i, label in enumerate(head):
                if label:
                    self.text(xs[i] + 10, hy + 17, label, "k")
            self.y += hh + 4
        y = self.y
        row_boxes = []
        for ri, row in enumerate(rows):
            cells = []
            for ci, cell in enumerate(row):
                cells.append(self._node_h(widths[ci], cell, None))
            h = max(cells)
            for ci, cell in enumerate(row):
                self.node(xs[ci], y, widths[ci], cell["title"], cell.get("sub", ""),
                          cell.get("kind", "b"), None, cell.get("align", "start"), h,
                          rx=8)
            row_boxes.append({"y": y, "h": h})
            if rail and ri < len(rows) - 1:
                self.v_arrow(xs[0] + 14, y + h + 2, y + h + 9)
            y += h + 6
        self.y = y + 6
        return {"xs": xs, "widths": widths, "rows": row_boxes}

    def dag_columns(self, columns, gap=16, row_gap=20):
        """分层有向图：列内节点垂直均分、列间等高对齐，连线走正交折线不穿节点。"""
        x0 = self.pad
        W = self.W - 2 * self.pad
        n = len(columns)
        w = (W - gap * (n - 1)) / n
        xs = [x0 + i * (w + gap) for i in range(n)]
        y0 = self.y
        col_h = []
        for col in columns:
            hs = [self._node_h(w, it, None) for it in col]
            col_h.append(sum(hs) + (len(col) - 1) * row_gap)
        H = max(col_h)
        boxes = []
        for ci, col in enumerate(columns):
            hs = [self._node_h(w, it, None) for it in col]
            total = sum(hs) + (len(col) - 1) * row_gap
            top = y0 + (H - total) / 2
            cb = []
            for it, h in zip(col, hs):
                self.node(xs[ci], top, w, it["title"], it.get("sub", ""),
                          it.get("kind", "b"), None, "center", h)
                cb.append((xs[ci], top, w, h))
                top += h + row_gap
            boxes.append(cb)
        for ci in range(n - 1):
            for (sx, sy, sw, sh) in boxes[ci]:
                for (tx, ty, tw, th) in boxes[ci + 1]:
                    x1, x2 = sx + sw + 3, tx - 4
                    y1, y2 = sy + sh / 2, ty + th / 2
                    if x2 <= x1:
                        continue
                    if abs(y1 - y2) < 4:
                        self.h_arrow(x1, x2, y1)
                    else:
                        mx = (x1 + x2) / 2
                        self.poly([(x1, y1), (mx, y1), (mx, y2), (x2, y2)],
                                  "ln", marker=True)
        self.y = y0 + H + 14
        return boxes

    def render(self):
        """收口：viewBox 高度由内容推导；任何文字溢出都会直接报错。"""
        if self.overflows:
            raise ValueError("图表文字溢出：" + "; ".join(self.overflows[:5]))
        H = int(math.ceil(self.y + self.pad))
        mark = self.P["mark"]
        defs = ('<defs><marker id="%s-ar" viewBox="0 0 10 10" refX="9" refY="5" '
                'markerWidth="6" markerHeight="6" orient="auto">'
                '<path d="M0,0 L10,5 L0,10 z" %s/></marker></defs>'
                % (self.marker, mark))
        cls = ' class="figsvg"' if self.theme == "reader" else ""
        return ('<svg%s viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg" '
                'role="img" aria-label="%s">%s%s</svg>'
                % (cls, self.W, H, _esc(self.aria), defs, "".join(self.parts)))


# ------------------------------------------------------------------ 通用小工具
def circles(n):
    return ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"][:n]


def build_all():
    """编译全部 11 张图，返回 dict；同时提供自检统计。"""
    import figure_data  # 延迟导入，避免循环
    out = {k: v[0] for k, v in figure_data.FIGURES.items()}
    out.update({
        "journey": build_journey(),
        "ia": build_ia(),
        "capability": build_capability(),
    })
    return out


# ------------------------------------------------------------------ 站点图 1：能力旅程
def build_journey():
    c = Chart(460, "site", pad=10, marker="ce-j",
              aria="四阶段交付能力旅程示意图")
    c.header("LEARNING JOURNEY", "14 步 · 四阶段能力旅程",
             "从左到右推进，每一步都有产出物")
    items = [
        {"title": "判断力", "sub": "场景 / 边界 / 验收线", "kind": "ba"},
        {"title": "动手力", "sub": "五种模式 / 知识 / 编排", "kind": "b"},
        {"title": "证明力", "sub": "评测集 / 调优 / 回归", "kind": "b"},
        {"title": "治理与表达", "sub": "选型 / 讲解 / 复盘", "kind": "ba"},
    ]
    c.grid_flow(items, cols=2, gap=14, badge_start=1)
    c.band("场景判断卡 → 方案画布 → 配置与评测集 → 验收报告 → 上线检查单",
           "交付主线")
    c.note("能跑通、能证明、能签字，才算完成")
    return c.render()


# ------------------------------------------------------------------ 站点图 2：三层 IA
def build_ia():
    c = Chart(960, "site", pad=16, marker="ce-i",
              aria="门户、介绍、详细三层信息架构与导航分布")
    c.header("INFORMATION ARCHITECTURE", "三层信息架构 · L0 门户 → L1 介绍 → L2 详细",
             "L2 按「学习 / 查阅 / 考核 / 资料」四板块分流，任一页都有统一导航与返回路径")
    W = c.W - 2 * c.pad
    # L0 / L1 居中窄卡
    top_w = 340
    tx = (c.W - top_w) / 2
    y0 = c.y
    h0 = c.node(tx, y0, top_w, "L0 · 入口门户", "index.html　品牌 / 价值 / 来意分流 / 导航总览",
                "ba", None, "start", 62, rx=12)
    c.v_arrow(c.W / 2, y0 + h0 + 2, y0 + h0 + 20)
    y1 = y0 + h0 + 22
    h1 = c.node(tx, y1, top_w, "L1 · 手册介绍", "手册展示页.html　一句话定义 / 结构 / 边界 / 阅读节奏",
                "b", None, "start", 62, rx=12)
    # 分支母线：从 L1 底部向下，再水平分到四个 L2 卡中心
    bus_y = y1 + h1 + 24
    c.line(c.W / 2, y1 + h1 + 2, c.W / 2, bus_y, "ln")
    gap = 16
    cw = (W - 3 * gap) / 4
    xs = [c.pad + i * (cw + gap) for i in range(4)]
    centers = [x + cw / 2 for x in xs]
    c.line(centers[0], bus_y, centers[-1], bus_y, "ln")
    for cx in centers:
        c.v_arrow(cx, bus_y, bus_y + 16)
    blocks = [
        ("L2 · 学习", "主手册 / 速查 / 精读", "三册正文 · 19 节笔记\n14 步路径 · 40 行目录"),
        ("L2 · 查阅", "术语词典 / 图示", "291 条可点术语 · 11 张图 / 逐点细节追问"),
        ("L2 · 考核", "FDE 工程师考核题库", "208 题 / 两类 / 14 能力域 / 打乱复习 · 错题本 · 成绩单"),
        ("L2 · 资料", "站点地图 / 使用说明", "核验报告 · 缺口清单 / 离线包 · 生成器 · 边界声明"),
    ]
    y2 = bus_y + 18
    sub_lines = [wrap(s, cw - 28, F_SUB) for _, _, s in blocks]
    hh = max(28 + LH_TITLE + 6 + len(ls) * LH_SUB + 20 for ls in sub_lines)
    hh = max(hh, 110)
    for i, (label, title, sub) in enumerate(blocks):
        c.rect(xs[i], y2, cw, hh, "b", 12)
        c.text(xs[i] + 14, y2 + 20, label, "k")
        c.text(xs[i] + 14, y2 + 28 + LH_TITLE, title, "t")
        for j, ln in enumerate(sub_lines[i]):
            c.text(xs[i] + 14, y2 + 28 + LH_TITLE + 6 + LH_SUB + j * LH_SUB,
                   ln, "s")
    c.y = y2 + hh + 14
    c.note("导航规则：顶部主导航 + 面包屑 + 站点地图入口 + 页脚站点地图；跨页全部相对路径，离线与静态托管一致。")
    return c.render()


# ------------------------------------------------------------------ 站点图 3：能力体系
def build_capability():
    c = Chart(680, "site", pad=14, marker="ce-c",
              aria="三项核心能力与五阶段交付方法论")
    c.header("CAPABILITY MAP", "三项核心能力 · 五阶段交付",
             "能力决定会不会做，阶段决定做到哪一步；每一步都要留下可验收的产出物")
    c.band("场景理解与方案设计　｜　交付实施与评测运维　｜　安全合规与责任 AI",
           "三项核心能力")
    caps = [
        {"title": "场景判断", "sub": "值不值得做 · 边界 · 验收线", "kind": "ba"},
        {"title": "方案与建设", "sub": "五种构建模式 · 知识 · 编排", "kind": "ba"},
        {"title": "证明与治理", "sub": "评测集 · 权限 · 审计 · 运维", "kind": "ba"},
    ]
    r = c.flow_row(caps, gap=18, badge_start=1, arrows=True, align="start")
    c.note("五阶段交付方法论（每阶段都有产出物与完成判据）")
    phases = [
        {"title": "接入", "sub": "材料与边界"},
        {"title": "建设", "sub": "知识 / 流程 / 工具"},
        {"title": "验证", "sub": "评测集与基线"},
        {"title": "推广", "sub": "灰度 / 培训 / 采纳"},
        {"title": "治理", "sub": "版本 / 成本 / 回滚"},
    ]
    c.flow_row(phases, gap=14, badge_start=1, arrows=True, align="center")
    c.band("场景判断卡 → 方案画布 → 配置与评测集 → 验收报告 → 上线检查单与运维手册",
           "产出物")
    return c.render()
