# -*- coding: utf-8 -*-
"""~/cosplay 的角色对话卡 → assets/cos-*.svg。

把角色头像直接嵌进 SVG（base64），所以成品不依赖任何外部图片。
R6 的头像取自 r6.awads.cc（需要联网），Hazbin 的头像用仓库里的 webp
（由 tools/make_cos_assets.py 生成）。静态资源，改了台词或头像才需要重跑：

    python tools/make_dialogue.py

台词只写单宽字符：全角 ！？ 换成半角。
"""
import base64
import os
import sys
import urllib.request

from sunset import CORAL, GOLD, INK, ORANGE, PANEL, mtext, shell, tw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")
R6_ICON = "https://r6.awads.cc/api/icons?game=r6x&i=%s"

# 文件名: (宽度, 窗口标题, [(角色, 头像来源, 台词, 强调色)…])。一左一右轮流说话。
SCENES = {
    "cos-r6.svg": (880, "~/cosplay/rainbow-six-siege-x", [
        ("Jäger", R6_ICON % "jager", "Hey, Ash is up ahead, let's go take her out!", GOLD),
        ("Solis", R6_ICON % "solis", "Hurh?", ORANGE),
    ]),
    "cos-alastor.svg": (430, "~/cosplay/hazbin-hotel", [
        ("Alastor", "Alastor.Cos/alastor-icon.webp", "You're never fully dressed without a smile!", CORAL),
        ("Vox", "Alastor.Cos/vox-icon.webp", "...Put me down, Alastor.", "#4FC3D9"),
    ]),
}

MIME = {".webp": "image/webp", ".png": "image/png", ".svg": "image/svg+xml"}


def data_uri(src):
    if src.startswith("http"):
        req = urllib.request.Request(src, headers={"User-Agent": "tg-twilight-cards"})
        with urllib.request.urlopen(req, timeout=45) as r:
            raw, mime = r.read(), r.headers.get_content_type()
    else:
        with open(os.path.join(ROOT, src), "rb") as f:
            raw, mime = f.read(), MIME[os.path.splitext(src)[1]]
    return "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode("ascii"))


def scene(width, title, lines):
    AV, ROW, TOP = 48, 76, 54
    room = width - (22 + AV + 14) - 16                         # 独占一行时，气泡最多能占的宽度
    longest = max(len(text) for _, _, text, _ in lines)
    SIZE = next(s for s in (12.5, 12, 11.5, 11, 10) if tw("x" * longest, s) + 26 <= room or s == 10)
    # 够宽的话一左一右挤在同一行，否则一人一行
    pair = (sum(tw(text, SIZE) + 26 for _, _, text, _ in lines[:2]) + 40
            <= width - 2 * (22 + AV + 14))
    out = []
    for i, (name, src, text, accent) in enumerate(lines):
        left = i % 2 == 0
        y = TOP + (i // 2 if pair else i) * ROW
        bw = tw(text, SIZE) + 26
        ax = 22 if left else width - 22 - AV                    # 头像
        bx = ax + AV + 14 if left else ax - 14 - bw            # 气泡
        nx = bx + 2 if left else bx + bw - 2                   # 名字
        tail = (f'M{bx} {y + 36}l-7 5 7 5z' if left else f'M{bx + bw} {y + 36}l7 5 -7 5z')
        out.append(
            f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".45s" '
            f'begin="{0.3 + i * 0.9:.1f}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="0,8" to="0,0" dur=".45s" '
            f'begin="{0.3 + i * 0.9:.1f}s" fill="freeze"/>'
            f'<image href="{data_uri(src)}" x="{ax}" y="{y + 6}" width="{AV}" height="{AV}"/>'
            + mtext(nx, y + 12, name, 11, accent, bold=True, anchor="start" if left else "end")
            + f'<path d="{tail}" fill="{PANEL}"/>'
            f'<rect x="{bx:.1f}" y="{y + 20}" width="{bw:.1f}" height="34" rx="10" fill="{PANEL}" '
            f'stroke="{accent}" stroke-opacity=".35"/>'
            + mtext(bx + 13, y + 41.5, text, SIZE, INK) + '</g>')
    height = TOP + ((len(lines) + 1) // 2 if pair else len(lines)) * ROW + 8
    names = " & ".join(l[0] for l in lines)
    return shell(width, height, "".join(out), "C", "%s — in-character dialogue" % names, chrome=title)


if __name__ == "__main__":
    try:
        cards = [(name, scene(*spec)) for name, spec in SCENES.items()]
    except OSError as e:
        sys.exit("refusing to write dialogue cards: could not load an avatar (%s)" % e)
    for name, svg in cards:
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(svg)
        print("  wrote assets/%s (%d KB)" % (name, len(svg) // 1024))
