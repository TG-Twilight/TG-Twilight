# -*- coding: utf-8 -*-
"""~/graffiti 的作品卡 → assets/art-<pixiv id>.svg。

纯静态、不联网（Pixiv 不允许未登录的程序读取作品信息，标题和日期手填）：

    python tools/make_graffiti.py

画了新东西：在 WORKS 最前面加一行，把原来那行的 NEW 去掉，
跑一遍脚本，再到 README 的 ~/graffiti 里放上对应的图片和链接。
"""
import os

from make_links import ICONS
from sunset import CORAL, GOLD, MUTED, PANEL, bitmap, mrow, mtext, shell, sprite_path, tw

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
W, H = 430, 80

# (Pixiv 作品 id, 标题, 发布年月, 是否标 NEW)，新的在前。
# 标题只写单宽字符：全角 ！？ 换成半角（README 里的 alt 保留原样）。
WORKS = [
    ("150784396", "Dear?", "2026-10", True),
    ("146949017", "Keep Smile! My Dear!", "2026-07", False),
    ("146948848", "Hey! My Dear?", "2026-07", False),
    ("119393336", "Judgement - HellTaker", "2024-06", False),
]


def card(pid, title, when, new):
    out = [f'<rect x="16" y="16" width="48" height="48" rx="10" fill="{PANEL}"/>',
           f'<path class="px" transform="translate(40,40)" d="{sprite_path(bitmap(ICONS["pencil"]), 4)}" '
           f'fill="{CORAL}"/>']
    fs = 15 if tw(title, 15) < (250 if new else 320) else 13
    out.append(mtext(80, 36, title, fs, GOLD, bold=True))
    out.append(mrow(80, 57, 11, [("pixiv.net/artworks/", MUTED), (pid, CORAL)])[0])
    out.append(mtext(W - 22, 57, when, 11, MUTED, anchor="end"))
    if new:
        bw = tw("NEW", 11) + 18
        out.append(f'<rect x="{W - 20 - bw:.1f}" y="21" width="{bw:.1f}" height="20" rx="10" fill="{CORAL}">'
                   f'<animate attributeName="opacity" values="1;.55;1" dur="2.4s" repeatCount="indefinite"/></rect>'
                   + mtext(W - 20 - bw / 2, 35, "NEW", 11, "#1B1123", bold=True, anchor="middle"))
    return shell(W, H, "".join(out), "A", "%s — Pixiv artwork %s" % (title, pid))


if __name__ == "__main__":
    for pid, title, when, new in WORKS:
        with open(os.path.join(OUT, "art-%s.svg" % pid), "w", encoding="utf-8", newline="\n") as f:
            f.write(card(pid, title, when, new))
        print("  wrote assets/art-%s.svg" % pid)
