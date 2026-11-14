# -*- coding: utf-8 -*-
"""落日终端风格的公共零件：配色、字体、等宽排版、卡片外壳。

所有生成脚本（make_cards / make_hero / make_pacman / make_links）都从这里取色，
改一处，全页跟着变。仅用标准库。
"""

# ── sunset palette ──────────────────────────────────────────────────
BG      = "#1B1123"
PANEL   = "#2A1B33"      # 比背景亮一档：标签底、空格子
INK     = "#F3D9C4"
GOLD    = "#FFD166"
ORANGE  = "#FF8C42"
CORAL   = "#FF5F6D"
PURPLE  = "#7B4B94"
MUTED   = "#9B8494"
RAMP    = ["#FF8C42", "#FFD166", "#FF5F6D", "#C05299", "#7B4B94", "#E8A33D", "#6E5A78"]

MONO = "ui-monospace,SFMono-Regular,'Cascadia Mono',Consolas,Menlo,'DejaVu Sans Mono','Liberation Mono',monospace"

# 等宽字体的字宽各家不同（Consolas 0.55em、Menlo 0.60em……）。
# 排版一律按 0.6em 计算，并给每段文字写上 textLength，换字体也不会错位。
CW = 0.6


def esc(t):
    return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def num(v):
    return "—" if v is None else "{:,}".format(v)


def mix(a, b, t):
    """两个 #rrggbb 之间取色：t=0 是 a，t=1 是 b。"""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join("%02x" % round(x + (y - x) * t) for x, y in zip(ca, cb))


def tw(s, size):
    """一段等宽文字的排版宽度。"""
    return len(s) * size * CW


def mtext(x, y, s, size, fill, bold=False, anchor="start", extra=""):
    """一段等宽文字。宽度用 textLength 钉死，所以只能放单宽字符（不要放中文）。"""
    attrs = f'x="{x:.2f}" y="{y:.2f}" fill="{fill}" font-size="{size}"'
    if len(s) > 1:
        attrs += f' textLength="{tw(s, size):.2f}"'
    if bold:
        attrs += ' font-weight="700"'
    if anchor != "start":
        attrs += f' text-anchor="{anchor}"'
    return f'<text {attrs}{extra}>{esc(s)}</text>'


def mrow(x, y, size, parts):
    """同一行里依次排开的多段文字：parts = [(text, fill[, bold]), ...]。返回 (svg, 结束 x)。"""
    out = []
    for p in parts:
        s, fill, bold = p[0], p[1], (p[2] if len(p) > 2 else False)
        lead = len(s) - len(s.lstrip(" "))
        body = s.strip(" ")
        if body:
            out.append(mtext(x + tw(" " * lead, size), y, body, size, fill, bold))
        x += tw(s, size)
    return "".join(out), x


def shell(w, h, body, uid, label, chrome=None):
    """卡片外壳：暗底、落日渐变描边。chrome 给出标题时画一条终端窗口标题栏。"""
    bar = ""
    if chrome:
        bar = (f'<circle cx="24" cy="18" r="5" fill="{CORAL}"/>'
               f'<circle cx="42" cy="18" r="5" fill="{GOLD}"/>'
               f'<circle cx="60" cy="18" r="5" fill="{PURPLE}"/>'
               + mtext(w / 2, 22.5, chrome, 12, MUTED, anchor="middle")
               + f'<rect x="1.8" y="36" width="{w - 3.6}" height="1" fill="{ORANGE}" opacity=".22"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(label)}" font-family="{MONO}">
  <style>text{{white-space:pre}}.px{{shape-rendering:crispEdges}}</style>
  <defs>
    <linearGradient id="edge{uid}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{ORANGE}" stop-opacity=".85"/>
      <stop offset="55%" stop-color="{CORAL}" stop-opacity=".55"/>
      <stop offset="100%" stop-color="{PURPLE}" stop-opacity=".45"/>
    </linearGradient>
    <linearGradient id="rule{uid}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{GOLD}" stop-opacity=".9"/>
      <stop offset="100%" stop-color="{CORAL}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x=".9" y=".9" width="{w - 1.8}" height="{h - 1.8}" rx="12" fill="{BG}" stroke="url(#edge{uid})" stroke-width="1.8"/>
  {bar}{body}
</svg>
'''


def bitmap(art):
    return [r for r in art.strip("\n").split("\n") if r]


def sprite_path(rows, u, on="#"):
    """把像素图合并成一条 path（按行合并连续像素），以 0,0 为中心。"""
    h, w = len(rows), max(len(r) for r in rows)
    x0, y0 = -w * u / 2, -h * u / 2
    d = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            if row[x] != on:
                x += 1
                continue
            run = x
            while run < len(row) and row[run] == on:
                run += 1
            d.append("M%g %gh%gv%gh%gz" % (x0 + x * u, y0 + y * u, (run - x) * u, u, -(run - x) * u))
            x = run
    return "".join(d)
