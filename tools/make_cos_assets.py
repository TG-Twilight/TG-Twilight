# -*- coding: utf-8 -*-
"""导出 Alastor cos 那一节要用的 webp。

    alastor.webp        cos 主图，从本地原图裁出来
                        （原图走 .gitignore，只留在本地）
    alastor-icon.webp   对话头像，官方立绘裁圆 + 红环
    vox-icon.webp       对话头像，官方立绘裁圆 + 青环

立绘从 Hazbin Hotel wiki 现拉，不往仓库里塞源图。

    pip install Pillow
    python tools/make_cos_assets.py

换图就改下面的 URL 和裁切框（都是立绘原始像素坐标，正方形）。
"""
import io
import os
import urllib.request

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, "Alastor.Cos")

# ── 主图：本地原图 ──────────────────────────────────────────────────
SRC = os.path.join(DIR, "photo_1_2026-08-24_22-25-24.jpg")
HERO_BOX = (0, 120, 853, 1240)      # 去掉顶上的天花板和脚下的地面
HERO_W = 800

# ── 头像：官方立绘 ──────────────────────────────────────────────────
ICON = 288
SS = 4                              # 超采样，圆边才不毛糙
PAD = 0.88                          # 立绘在圆里占多大
RING = 7                            # 描边粗细

FACES = [
    ("alastor-icon.webp",
     "https://static.wikia.nocookie.net/hazbinhotel/images/a/a6/"
     "Alastor_s2_Render_by_OKDraws.png/revision/latest/scale-to-width-down/1000"
     "?cb=20251124134605",
     (70, 240, 710, 880),           # 以脸为中心，含耳朵与完整笑容
     (122, 20, 32), (32, 7, 14), (226, 29, 44, 240)),
    ("vox-icon.webp",
     "https://static.wikia.nocookie.net/hazbinhotel/images/5/5d/"
     "Vox_render.png/revision/latest/scale-to-width-down/1000"
     "?cb=20260205165928",
     (100, 10, 740, 650),           # 整个电视头，含天线
     (16, 60, 92), (5, 18, 31), (43, 190, 230, 240)),
]


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGBA")


def radial(size, inner, outer):
    """从中心往外压暗的底色，比纯色有层次。"""
    g = Image.new("RGB", (size, size), outer)
    d = ImageDraw.Draw(g)
    for i in range(90, 0, -1):
        t = i / 90
        r = size * 0.78 * t
        d.ellipse([size / 2 - r, size / 2 - r, size / 2 + r, size / 2 + r],
                  fill=tuple(int(o + (n - o) * (1 - t)) for n, o in zip(inner, outer)))
    return g


def face_icon(render, box, bg_in, bg_out, ring):
    x0, y0, x1, y1 = box
    cell = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    cell.alpha_composite(render, (-x0, -y0))
    inner = int(ICON * PAD)
    cell = cell.resize((inner, inner), Image.LANCZOS)

    base = radial(ICON, bg_in, bg_out).convert("RGBA")
    base.alpha_composite(cell, ((ICON - inner) // 2, (ICON - inner) // 2))

    big = ICON * SS
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, big - 1, big - 1], fill=255)
    out = Image.new("RGBA", (ICON, ICON), (0, 0, 0, 0))
    out.paste(base.convert("RGB"), (0, 0))
    out.putalpha(mask.resize((ICON, ICON), Image.LANCZOS))

    w = RING * SS
    stroke = Image.new("L", (big, big), 0)
    ImageDraw.Draw(stroke).ellipse([w // 2, w // 2, big - 1 - w // 2, big - 1 - w // 2],
                                   outline=255, width=w)
    stroke = stroke.resize((ICON, ICON), Image.LANCZOS)
    return Image.alpha_composite(
        out, Image.composite(Image.new("RGBA", (ICON, ICON), ring),
                             Image.new("RGBA", (ICON, ICON), (0, 0, 0, 0)), stroke))


if __name__ == "__main__":
    hero = Image.open(SRC).crop(HERO_BOX)
    hero = hero.resize((HERO_W, round(hero.height * HERO_W / hero.width)), Image.LANCZOS)
    hero.convert("RGB").save(os.path.join(DIR, "alastor.webp"), "WEBP", quality=84, method=6)

    for name, url, box, bg_in, bg_out, ring in FACES:
        face_icon(fetch(url), box, bg_in, bg_out, ring).save(
            os.path.join(DIR, name), "WEBP", quality=92, method=6)

    for n in ("alastor.webp", "alastor-icon.webp", "vox-icon.webp"):
        p = os.path.join(DIR, n)
        print("  %-20s %s  %d KB" % (n, Image.open(p).size, os.path.getsize(p) / 1024))
