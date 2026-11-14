# -*- coding: utf-8 -*-
"""页首的 neofetch 风格终端卡片 → assets/hero.svg。

左边是程序画出来的 ASCII 落日（太阳、百叶条纹、仙人掌、透视地面），
右边是个人信息与 GitHub 数字。由 make_cards.py 取完数据后调用 hero(data)。

改个人信息：编辑下面的 PROFILE。SVG 里的文字用 textLength 钉了宽度，
只能写单宽字符 —— 中文介绍留在 README 里。
"""
import datetime
import math

from sunset import (CORAL, GOLD, INK, MUTED, ORANGE, PURPLE, RAMP, mix, mrow,
                    mtext, num, shell, tw)

W = 880
HOST = "simon@twilight"

# (键, 值)；None 开头的是小节标题
PROFILE = [
    ("Alias", "SuperCowboy, forever in the sunset"),
    ("Uptime", "{uptime} on GitHub"),
    ("Routine", "rules by day, sketches by night, cosplay on weekends"),
    ("Hobbies", "drawing, Rainbow Six Siege, cosplay"),
    (None, "Stack"),
    ("Languages", "Kotlin, TypeScript, Rust, C++, Python, Shell"),
    ("Building", "ad-block rules, cross-platform apps, utilities"),
    ("Tinkering", "game mods, reviving abandoned software"),
    (None, "Contact"),
    ("Web", "me.awads.cc", "Blog", "awads.cc"),
    ("X", "@Simon_Twilight", "Pixiv", "Simon Twilight"),
]

LANG_ALIAS = {"Adblock Filter List": "Adblock"}

# ── ASCII 落日 ──────────────────────────────────────────────────────
COLS, ROWS = 48, 36
ART_SIZE, ART_LH = 10, 12              # 字符格 6×12，所以横向要按 2:1 换算
HORIZON = 25
SUN_C, SUN_R, SUN_RY = 24.0, 19.0, 10.5
SUN_ROW = HORIZON - 5.5                # 圆心所在的行
SLATS = (HORIZON - 1, HORIZON - 3, HORIZON - 6)   # 太阳下半截被挖掉的行（复古百叶）

SUN_RAMP = ["#FFF2BC", GOLD, "#FF7A45", "#FF4E62"]

CACTUS_L = ["...##...",
            "...##..#",
            "#..##..#",
            "#..##..#",
            "#..#####",
            "#####...",
            "...##...",
            "...##...",
            "...##..."]
CACTUS_R = ["..#..",
            "..#.#",
            "#.#.#",
            "#.###",
            "###..",
            "..#..",
            "..#.."]


def ramp(stops, t):
    t = min(max(t, 0.0), 1.0) * (len(stops) - 1)
    i = min(int(t), len(stops) - 2)
    return mix(stops[i], stops[i + 1], t - i)


def scene():
    """返回 ROWS×COLS 的 (字符, 颜色) 网格。"""
    grid = [[(" ", None)] * COLS for _ in range(ROWS)]

    # 星星：固定种子的伪随机，越靠近地平线越稀
    seed = 20221230
    for _ in range(70):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        c = seed % COLS
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        r = seed % (HORIZON - 4)
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        ch = ".." "." "+" "*" "."[seed % 6]
        in_sun = ((c - SUN_C) / (SUN_R + 2)) ** 2 + ((r - SUN_ROW) / (SUN_RY + 1)) ** 2 < 1
        if (seed >> 8) % (HORIZON - 4) >= r and not in_sun:
            grid[r][c] = (ch, mix(PURPLE, INK, 0.25 + 0.6 * ((seed >> 4) % 100) / 100))

    # 太阳
    for r in range(int(SUN_ROW - SUN_RY), HORIZON):
        dy = (r + 0.5 - SUN_ROW) / SUN_RY
        if r in SLATS or abs(dy) >= 1:
            continue
        half = SUN_R * math.sqrt(1 - dy * dy)
        color = ramp(SUN_RAMP, (r - (SUN_ROW - SUN_RY)) / (HORIZON - (SUN_ROW - SUN_RY)))
        for c in range(COLS):
            edge = half - abs(c + 0.5 - SUN_C)
            if edge > 0:
                grid[r][c] = ("@" if edge > 2.6 else "%" if edge > 1.3 else "*" if edge > 0.5 else ":", color)

    # 飞鸟
    for r, c in ((6, 38), (8, 42), (7, 5), (5, 9)):
        grid[r][c] = ("v", INK)

    # 地平线与透视地面
    for c in range(COLS):
        grid[HORIZON][c] = ("=", ORANGE)
    for r in range(HORIZON + 1, ROWS):
        depth = r - HORIZON
        color = mix(CORAL, PURPLE, min(1.0, depth / 9))
        if depth in (2, 5, 9):
            for c in range(COLS):
                grid[r][c] = ("-", mix(color, "#1B1123", 0.35))
        for k in range(-6, 7):
            c = int(round(SUN_C - 0.5 + k * (2.4 + depth * 0.8)))
            if 0 <= c < COLS:
                grid[r][c] = ("|" if k == 0 else "/" if k < 0 else "\\", color)

    # 仙人掌：站在地平线上的剪影
    for art, left, base, color in ((CACTUS_L, 0, HORIZON + 5, "#C05299"), (CACTUS_R, 42, HORIZON + 2, "#9A5AA8")):
        for j, line in enumerate(art):
            r = base - len(art) + 1 + j
            for i, ch in enumerate(line):
                # 剪影周围留一格空白，免得和地面线条糊在一起
                if ch == "#":
                    grid[r][left + i] = ("#", color)
                elif grid[r][left + i][0] in "/\\|-" and r > HORIZON:
                    grid[r][left + i] = (" ", None)
    return grid


def ascii_art(x, y):
    out = []
    for r, row in enumerate(scene()):
        c = 0
        while c < COLS:
            ch, color = row[c]
            if ch == " ":
                c += 1
                continue
            run = c                                   # 同色连续段合成一个 <text>，中间允许夹空格
            while run < COLS and (row[run][1] == color or row[run][0] == " "):
                run += 1
            s = "".join(cell[0] for cell in row[c:run]).rstrip(" ")
            out.append(mtext(x + tw(" " * c, ART_SIZE), y + r * ART_LH, s, ART_SIZE, color))
            c += len(s)
    return "".join(out)


# ── 右侧信息 ────────────────────────────────────────────────────────
def uptime(created, today):
    months = (today.year - created.year) * 12 + today.month - created.month - (today.day < created.day)
    y, m = divmod(max(months, 0), 12)
    parts = (["%d year%s" % (y, "s" * (y != 1))] if y else []) + (["%d month%s" % (m, "s" * (m != 1))] if m else [])
    return ", ".join(parts) or "a few days"


def hero(d, today=None):
    today = today or datetime.date.today()
    created = datetime.date.fromisoformat((d.get("created_at") or "2022-12-30")[:10])
    X, SIZE, LH, WIDTH = 348, 13, 21, 65              # 信息区：起点、字号、行高、每行字符数
    PRE, HALF = 13, 31                                # 键 + 点线占 13 格；双栏每栏 31 格
    DOTS = mix(MUTED, "#1B1123", 0.45)
    lines = []                                        # 每行一段 svg

    def kv(key, value):
        return mrow(X, 0, SIZE, [(key, ORANGE), (" " + "." * (PRE - 2 - len(key)) + " ", DOTS),
                                 (value[:WIDTH - PRE], INK)])[0]

    def kv2(k1, v1, k2, v2):
        def half(k, v):
            return [(k, ORANGE), (" " + "." * (HALF - 2 - len(k) - len(v)) + " ", DOTS), (v, INK)]
        return mrow(X, 0, SIZE, half(k1, v1) + [(" | ", DOTS)] + half(k2, v2))[0]

    def section(name):
        head, x = mrow(X, 0, SIZE, [("- ", DOTS), (name + " ", GOLD, True)])
        return head + f'<rect x="{x:.1f}" y="-4.5" width="{X + tw("x" * WIDTH, SIZE) - x:.1f}" height="1" fill="{ORANGE}" opacity=".3"/>'

    title, x = mrow(X, 0, SIZE, [(HOST.split("@")[0], GOLD, True), ("@", INK), (HOST.split("@")[1] + " ", GOLD, True)])
    lines.append(title + f'<rect x="{x:.1f}" y="-4.5" width="{X + tw("x" * WIDTH, SIZE) - x:.1f}" height="1.6" fill="url(#ruleH)"/>')
    for item in PROFILE:
        if item[0] is None:
            lines.append(section(item[1]))
        elif len(item) == 4:
            lines.append(kv2(*item))
        else:
            lines.append(kv(item[0], item[1].format(uptime=uptime(created, today))))

    k = d.get("contrib") or {}
    lines.append(section("GitHub"))
    lines.append(kv2("Repos", num(d.get("repos")), "Stars", num(d.get("stars"))))
    lines.append(kv2("Commits", num(d.get("commits")), "Followers", num(d.get("followers"))))
    lines.append(kv2("Pull requests", num(d.get("prs")), "Contributions", num(k.get("total"))))

    # 语言比例：一条分段色带 + 两行图例
    langs = d.get("langs") or {}
    total = sum(langs.values())
    if total:
        lines.append(section("Code by language"))
        top = sorted(langs.items(), key=lambda kv_: -kv_[1])[:5]
        rest = total - sum(v for _, v in top)
        if rest / total >= 0.001:
            top.append(("Other", rest))
        bw, seg, bx = tw("x" * WIDTH, SIZE), [], X
        for i, (_, size) in enumerate(top):
            w = bw * size / total
            seg.append(f'<rect x="{bx:.1f}" y="-9" width="{w:.1f}" height="8" fill="{RAMP[i % len(RAMP)]}"/>')
            bx += w
        lines.append(f'<clipPath id="barH"><rect x="{X}" y="-9" width="{bw:.1f}" height="8" rx="4"/></clipPath>'
                     f'<g clip-path="url(#barH)">{"".join(seg)}</g>')
        for row in range(0, len(top), 3):
            cells = []
            for i, (name, size) in enumerate(top[row:row + 3], row):
                label = LANG_ALIAS.get(name, name)[:12]
                pct = "%.1f%%" % (size / total * 100)
                cx = X + tw("x" * 22, SIZE) * (i - row)
                cells.append(f'<circle cx="{cx + 3.5:.1f}" cy="-4.5" r="3.5" fill="{RAMP[i % len(RAMP)]}"/>'
                             + mrow(cx + tw("xx", SIZE), 0, SIZE,
                                    [(label, INK), (" " * (17 - len(label) - len(pct)) + pct, MUTED)])[0])
            lines.append("".join(cells))

    cursor = (f'<rect x="{X + tw("> ", SIZE):.1f}" y="-11" width="{tw("x", SIZE):.1f}" height="14" fill="{GOLD}">'
              f'<animate attributeName="opacity" calcMode="discrete" values="1;0" dur="1.06s" '
              f'repeatCount="indefinite"/></rect>')
    lines.append(mtext(X, 0, ">", SIZE, ORANGE, bold=True) + cursor)

    top_y = 82
    body = [mrow(24, 60, 12, [(HOST, GOLD, True), (":", MUTED), ("~", CORAL), ("$ ", MUTED),
                              ("neofetch --sunset", INK)])[0]]
    body.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".9s" begin=".1s" '
                f'fill="freeze"/>{ascii_art(24, top_y + 2)}</g>')
    for i, line in enumerate(lines):
        body.append(f'<g transform="translate(0,{top_y + 2 + i * LH})" opacity="0">'
                    f'<animate attributeName="opacity" from="0" to="1" dur=".35s" '
                    f'begin="{0.25 + i * 0.06:.2f}s" fill="freeze"/>{line}</g>')

    height = max(top_y + ROWS * ART_LH, top_y + len(lines) * LH) + 6
    return shell(W, height, "\n  ".join(body), "H",
                 "%s — terminal profile card" % (d.get("name") or HOST), chrome=HOST + ": ~")
