# -*- coding: utf-8 -*-
"""页首的像素风链接按钮 → assets/link-*.svg。

纯静态、不联网；配色取自 tools/sunset.py，所以只在改按钮或改配色之后才需要重跑：

    python tools/make_links.py

链接地址写在 README 里（SVG 作为 <img> 展示时自身不能带链接），
这里只管按钮长什么样。新增按钮：在 LINKS 里加一行，再到 README 里放上图片。
"""
import os

from sunset import (BG, CORAL, GOLD, INK, ORANGE, PURPLE, bitmap, esc, mtext,
                    sprite_path, tw)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
W, H, PAD = 290, 56, 3     # 四周留 3px 透明边，三个并排时自然有间隔
U = 3                      # 图标的一个像素

ICONS = {
    "pad": """
.......
.#####.
##.####
#...#.#
##.####
##...##
""",
    "x": """
#.....#
.#...#.
..#.#..
...#...
..#.#..
.#...#.
#.....#
""",
    "pencil": """
.....##
....###
...###.
..###..
#.##...
##.....
###....
""",
    "house": """
...#...
..###..
.#####.
#######
.##.##.
.##.##.
.##.##.
""",
    "feed": """
####...
....##.
###...#
...##.#
##..#.#
##..#.#
""",
    "heart": """
.##.##.
#######
#######
#######
.#####.
..###..
...#...
""",
}

# (文件名, 按钮文字, 图标, 强调色)
LINKS = [
    ("steam",    "STEAM",    "pad",    GOLD),
    ("x",        "X",        "x",      INK),
    ("pixiv",    "PIXIV",    "pencil", CORAL),
    ("homepage", "HOMEPAGE", "house",  "#C05299"),
    ("blog",     "BLOG",     "feed",   ORANGE),
    ("sponsor",  "SPONSOR",  "heart",  "#FF7A8A"),
]


def button(label, icon, accent):
    size = 16
    width = 21 + 14 + tw(label, size) + 6 + tw("x", size)      # 图标 + 间距 + 文字 + 光标
    x = (W - width) / 2
    tx = x + 21 + 14
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(label.title())}" font-family="ui-monospace,SFMono-Regular,'Cascadia Mono',Consolas,Menlo,'DejaVu Sans Mono','Liberation Mono',monospace">
  <defs>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{accent}" stop-opacity=".9"/>
      <stop offset="100%" stop-color="{PURPLE}" stop-opacity=".5"/>
    </linearGradient>
  </defs>
  <rect x="{PAD + .9}" y="{PAD + .9}" width="{W - 2 * PAD - 1.8}" height="{H - 2 * PAD - 1.8}" rx="10" fill="{BG}" stroke="url(#edge)" stroke-width="1.8"/>
  <path transform="translate({x + 10.5:.1f},{H / 2})" d="{sprite_path(bitmap(ICONS[icon]), U)}" fill="{accent}" shape-rendering="crispEdges"/>
  {mtext(tx, H / 2 + 5.5, label, size, INK, bold=True)}
  <rect x="{tx + tw(label, size) + 6:.1f}" y="{H / 2 - 8}" width="{tw("x", size):.1f}" height="16" fill="{accent}"><animate attributeName="opacity" calcMode="discrete" values="1;0" dur="1.06s" repeatCount="indefinite"/></rect>
</svg>
'''


if __name__ == "__main__":
    for name, label, icon, accent in LINKS:
        with open(os.path.join(OUT, "link-%s.svg" % name), "w", encoding="utf-8", newline="\n") as f:
            f.write(button(label, icon, accent))
        print("  wrote assets/link-%s.svg" % name)
