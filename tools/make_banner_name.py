# -*- coding: utf-8 -*-
"""把 banner.svg 里的名字换成手写体路径。

GitHub 用 <img> 显示 SVG，外部字体一律加载不到，看的人也未必装了手写体，
所以直接把字形转成 <path> 写进 banner：颜色仍走 url(#ink) 渐变 + #soft 阴影，
并按字形实际范围同步擦出动画的裁剪框（wipeName）和光标。

字体现拉 Google Fonts 仓库，不往仓库里塞字体文件。

    pip install fonttools uharfbuzz
    python tools/make_banner_name.py

换字体就改 FONT_URL；换文案改 NAME；位置改 LEFT / TOP / BOTTOM —— 字形整体
（含花体尾巴）按高度塞进 TOP–BOTTOM 这条带子，宽度随字体比例自动算。
"""
import io
import os
import re
import urllib.request

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANNER = os.path.join(ROOT, "assets", "banner.svg")

# Yellowtail by Astigmatic，Apache License 2.0
FONT_URL = "https://github.com/google/fonts/raw/main/apache/yellowtail/Yellowtail-Regular.ttf"
NAME = "Simon Twilight"
# 上面是 MOUNTAIN OF FAITH（y≈78，下划线 86），下面是副标题（顶≈194）
LEFT, TOP, BOTTOM = 64, 94, 190


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "tg-twilight-banner"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def shape(data, text):
    face = hb.Face(data)
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True, "calt": True})
    return buf.glyph_infos, buf.glyph_positions


def main():
    data = fetch(FONT_URL)
    tt = TTFont(io.BytesIO(data))
    gs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    infos, poss = shape(data, NAME)

    # 先按字体单位量一遍整体范围，再换算成 px
    raw = BoundsPen(gs)
    x = 0
    for info, pos in zip(infos, poss):
        gs[order[info.codepoint]].draw(TransformPen(raw, (1, 0, 0, 1, x + pos.x_offset, pos.y_offset)))
        x += pos.x_advance
    fx0, fy0, fx1, fy1 = raw.bounds
    s = (BOTTOM - TOP) / (fy1 - fy0)           # font units → px
    ox = LEFT - fx0 * s                         # 最左一笔贴 LEFT
    baseline = TOP + fy1 * s                    # 最高一笔贴 TOP

    svg = SVGPathPen(gs, ntos=lambda v: ("%.1f" % v).rstrip("0").rstrip("."))
    bounds = BoundsPen(gs)
    x = 0
    for info, pos in zip(infos, poss):
        name = order[info.codepoint]
        # y 轴翻转：字体坐标向上，SVG 向下
        m = (s, 0, 0, -s, ox + (x + pos.x_offset) * s, baseline - pos.y_offset * s)
        gs[name].draw(TransformPen(svg, m))
        gs[name].draw(TransformPen(bounds, m))
        x += pos.x_advance
    d = svg.getCommands()
    x0, y0, x1, y1 = bounds.bounds

    src = open(BANNER, encoding="utf-8").read()

    # 名字本体：替换 wipeName 组里的内容
    body = ('\n      <path fill="url(#ink)" filter="url(#soft)" aria-hidden="true" d="%s"/>\n    ' % d)
    src, n = re.subn(r'(<g clip-path="url\(#wipeName\)">).*?(</g>)',
                     lambda m: m.group(1) + body + m.group(2), src, count=1, flags=re.S)
    assert n == 1, "wipeName group not found"

    # 擦出裁剪框：上下各留 4px，别把花体尾巴切掉
    top, h, w = int(y0) - 4, int(y1 - y0) + 8, int(x1 - 56) + 12
    src, n = re.subn(r'<clipPath id="wipeName"><rect x="56" y="[\d.]+" width="0" height="[\d.]+">\s*'
                     r'<animate attributeName="width" from="0" to="[\d.]+"',
                     '<clipPath id="wipeName"><rect x="56" y="%d" width="0" height="%d">\n'
                     '      <animate attributeName="width" from="0" to="%d"' % (top, h, w), src, count=1)
    assert n == 1, "wipeName clip not found"

    # 光标：从最高一笔到 baseline，终点停在最后一笔后
    cy, ch = int(y0) + 4, int(baseline - y0) - 4
    src, n = re.subn(r'<rect x="64" y="[\d.]+" width="4" height="[\d.]+" fill="#FFD166" opacity="0">'
                     r'(\s*<set[^>]*/>\s*)<animate attributeName="x" from="64" to="[\d.]+"',
                     lambda m: ('<rect x="64" y="%d" width="4" height="%d" fill="#FFD166" opacity="0">'
                                '%s<animate attributeName="x" from="64" to="%d"'
                                % (cy, ch, m.group(1), int(x1) + 8)), src, count=1)
    assert n == 1, "caret not found"

    open(BANNER, "w", encoding="utf-8", newline="\n").write(src)
    print("name bbox: x %.0f-%.0f  y %.0f-%.0f  baseline %.0f  (%d path chars)"
          % (x0, x1, y0, y1, baseline, len(d)))


if __name__ == "__main__":
    main()
