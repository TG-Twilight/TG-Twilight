# -*- coding: utf-8 -*-
"""贡献日历小游戏：吃豆人沿着格子一行行吃过去，三只 Claude 小精灵在后面追。

board(days, levels) 接收 make_cards.fetch_contributions() 抓到的
date -> count / date -> level，返回 assets/pacman.svg 的内容。
平时由 make_cards.py 统一调用；也可以单独运行本文件，只重画这一张：

    python tools/make_pacman.py

实现要点：
- 日历保持 GitHub 的样子（53 周 × 7 天、月份、Mon/Wed/Fri、Less/More），
  只是换成落日色阶，一眼还能认出是贡献图。
- 全部动画是 SMIL，并且共用同一个总时长、都从 0 开始，所以永远同步，
  不需要脚本（GitHub 以 <img> 方式展示 SVG，脚本本来也跑不了）。
- 追兵走的是同一条路线，只是晚出发几格。
"""
import datetime
import math
import os
import sys
import xml.dom.minidom

from sunset import (BG, CORAL, GOLD, INK, MUTED, ORANGE, PURPLE, bitmap, mtext,
                    num, shell, sprite_path, tw)

# ── 版面（px）───────────────────────────────────────────────────────
W = 880
GX, GY = 58, 66            # 格子区左上角
CELL, PITCH = 11, 15
WEEKS = 53
H = GY + 7 * PITCH + 34

LEVELS = ["#3A2745", PURPLE, "#C05299", ORANGE, GOLD]   # 0 = 没有贡献
TRACK = "#20152A"          # 被吃掉之后留下的空槽

# ── 时间（s）────────────────────────────────────────────────────────
STEP = 0.07                # 走过一格
INTRO = 1.6                # 开场：完整日历 + READY!
OUTRO = 2.4                # 收场：空日历 + 总分
EAT_AHEAD = 4              # 嘴碰到格子就算吃掉（px）
CHOMP = 0.24               # 嘴一张一合

# 追兵：(落后几格, 特长, 迈一步的秒数)。步频故意不一样，免得三只齐步走。
CAST = ((3, "blink", 0.34), (5, "wave", 0.30), (7, "hop", 0.38))
CLAUDE = "#D97757"         # 角色自己的颜色，不跟卡片配色走

MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

# ── 像素角色 ────────────────────────────────────────────────────────
PAC_U = 1.4
CLAWD_U = 1.4

CLAWD_BODY = """
..############..
..############..
..##.######.##..
..##.######.##..
..############..
..############..
..############..
..############..
"""
CLAWD_EYES = """
................
................
....#......#....
....#......#....
"""
CLAWD_ARMS_DOWN = """
................
................
................
................
##............##
##............##
"""
CLAWD_ARMS_UP = """
................
................
##............##
##............##
"""
CLAWD_LEGS_A = """
................
................
................
................
................
................
................
................
..##.##..##.##..
..##........##..
"""
CLAWD_LEGS_B = """
................
................
................
................
................
................
................
................
..##.##..##.##..
.....##..##.....
"""
CLAWD_ROWS = 10


def clawd_path(art):
    rows = bitmap(art)
    rows += ["." * 16] * (CLAWD_ROWS - len(rows))      # 各图层补齐到同一高度再居中
    return sprite_path(rows, CLAWD_U)


def pac_path(mouth_deg):
    """11×11 的圆，朝右张开 mouth_deg 的嘴。"""
    n, r = 11, 5.5
    rows = []
    for j in range(n):
        row = ""
        for i in range(n):
            dx, dy = i + 0.5 - r, j + 0.5 - r
            inside = dx * dx + dy * dy <= r * r
            bite = dx > -0.6 and abs(math.degrees(math.atan2(dy, dx + 0.6))) < mouth_deg
            row += "#" if inside and not bite else "."
        rows.append(row)
    return sprite_path(rows, PAC_U)


# ── 路线 ────────────────────────────────────────────────────────────
def cx(col):
    return GX + col * PITCH + CELL / 2


def cy(row):
    return GY + row * PITCH + CELL / 2


class Route:
    """吃豆人的路线：从左边进场，沿七行之字形走完，从右边出场。"""

    def __init__(self):
        pts = [(-16.0, cy(0))]
        for r in range(7):
            a, b = (0, WEEKS - 1) if r % 2 == 0 else (WEEKS - 1, 0)
            pts += [(cx(a), cy(r)), (cx(b), cy(r))]
        pts.append((W + 16.0, cy(6)))
        self.pts = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
        self.dist = [0.0]
        for a, b in zip(self.pts, self.pts[1:]):
            self.dist.append(self.dist[-1] + abs(b[0] - a[0]) + abs(b[1] - a[1]))
        self.speed = PITCH / STEP
        self.lag = max(lag for lag, _, _ in CAST) * STEP
        self.cleared = INTRO + self.dist[-1] / self.speed + self.lag
        self.total = self.cleared + OUTRO

    def k(self, t):
        return ("%.5f" % min(max(t / self.total, 0.0), 1.0)).rstrip("0").rstrip(".")

    def eat_time(self, col, row):
        x, y = cx(col), cy(row)
        for i, (a, b) in enumerate(zip(self.pts, self.pts[1:])):
            if a[1] == b[1] == y and min(a[0], b[0]) <= x <= max(a[0], b[0]):
                return INTRO + max(0.0, self.dist[i] + abs(x - a[0]) - EAT_AHEAD) / self.speed
        raise ValueError((col, row))

    def motion(self, lag_cells=0):
        """<animateTransform> 两条：位移（线性）与朝向（离散）。"""
        delay = INTRO + lag_cells * STEP
        times = [0.0] + [delay + d / self.speed for d in self.dist] + [self.total]
        pts = [self.pts[0]] + self.pts + [self.pts[-1]]
        move = ('<animateTransform attributeName="transform" type="translate" '
                'values="%s" keyTimes="%s" dur="%.3fs" repeatCount="indefinite"/>'
                % (";".join("%g,%g" % p for p in pts), ";".join(self.k(t) for t in times), self.total))
        heads, at = [], []
        for i, (a, b) in enumerate(zip(self.pts, self.pts[1:])):
            deg = 0 if b[0] > a[0] else 180 if b[0] < a[0] else 90
            if not heads or heads[-1] != deg:
                heads.append(deg)
                at.append(0.0 if not at else delay + self.dist[i] / self.speed)
        face = ('<animateTransform attributeName="transform" type="rotate" calcMode="discrete" '
                'values="%s" keyTimes="%s" dur="%.3fs" repeatCount="indefinite"/>'
                % (";".join(map(str, heads)), ";".join(self.k(t) for t in at), self.total))
        return move, face

    def show(self, start, end=None):
        """只在 [start, end) 之间可见的离散动画。"""
        if start <= 0 and end is None:
            return ""
        if start <= 0:
            vals, keys = ["visible", "hidden"], [0, end]
        elif end is None or end >= self.total:
            vals, keys = ["hidden", "visible"], [0, start]
        else:
            vals, keys = ["hidden", "visible", "hidden"], [0, start, end]
        return ('<animate attributeName="visibility" calcMode="discrete" values="%s" keyTimes="%s" '
                'dur="%.3fs" repeatCount="indefinite"/>'
                % (";".join(vals), ";".join(self.k(t) for t in keys), self.total))


def flip(a, b, dur, key="0;.5"):
    """两帧来回切换：a 先亮，b 后亮。返回 (a 的动画, b 的动画)。"""
    tpl = ('<animate attributeName="visibility" calcMode="discrete" values="%s" keyTimes="' + key
           + '" dur="%gs" repeatCount="indefinite"/>')
    return (a.replace("/>", ">" + tpl % ("visible;hidden", dur) + "</path>", 1),
            b.replace("/>", ' visibility="hidden">' + tpl % ("hidden;visible", dur) + "</path>", 1))


def clawd(route, lag, trait, stride):
    move, _ = route.motion(lag)
    legs = "".join(flip('<path d="%s"/>' % clawd_path(CLAWD_LEGS_A),
                        '<path d="%s"/>' % clawd_path(CLAWD_LEGS_B), stride))
    down, up = '<path d="%s"/>' % clawd_path(CLAWD_ARMS_DOWN), '<path d="%s"/>' % clawd_path(CLAWD_ARMS_UP)
    arms = "".join(flip(down, up, 0.28)) if trait == "wave" else down
    extra = ""
    if trait == "blink":                              # 眼睛是身体上的两个洞，眨眼就是把洞补上
        extra = ('<path d="%s" visibility="hidden"><animate attributeName="visibility" calcMode="discrete" '
                 'values="hidden;visible;hidden" keyTimes="0;.9;.96" dur="2.4s" repeatCount="indefinite"/></path>'
                 % clawd_path(CLAWD_EYES))
    hop = ""
    if trait == "hop":
        hop = ('<animateTransform attributeName="transform" type="translate" values="0,0;0,-3;0,0" '
               'dur="%gs" repeatCount="indefinite"/>' % stride)
    return ('<g transform="translate(-40,0)">%s<g fill="%s">%s<path d="%s"/>%s%s%s</g></g>'
            % (move, CLAUDE, hop, clawd_path(CLAWD_BODY), arms, legs, extra))


def pacman(route):
    move, face = route.motion(0)
    frames = [pac_path(a) for a in (50, 26, 3)]
    seq = [0, 1, 2, 1]                                # 张 → 半 → 合 → 半
    out = []
    for i, d in enumerate(frames):
        vals = ";".join("visible" if s == i else "hidden" for s in seq)
        out.append('<path d="%s"><animate attributeName="visibility" calcMode="discrete" values="%s" '
                   'dur="%gs" repeatCount="indefinite"/></path>' % (d, vals, CHOMP))
    return ('<g transform="translate(-40,0)">%s<g>%s<g fill="%s">%s</g></g></g>'
            % (move, face, GOLD, "".join(out)))


# ── 日历 ────────────────────────────────────────────────────────────
def calendar(days, levels, today):
    """最近 53 周，每周从周日开始：[[(date, count, level) | None × 7] × 53]。"""
    start = today - datetime.timedelta(days=(today.weekday() + 1) % 7 + 7 * (WEEKS - 1))
    weeks = []
    for w in range(WEEKS):
        col = []
        for d in range(7):
            day = start + datetime.timedelta(days=w * 7 + d)
            key = day.isoformat()
            col.append(None if day > today else (day, days.get(key, 0), levels.get(key, 0)))
        weeks.append(col)
    return weeks


def board(days, levels, today=None):
    today = today or datetime.date.today()
    weeks = calendar(days, levels, today)
    route = Route()
    out = []

    # 月份、星期
    last_col = -9
    for c, col in enumerate(weeks):
        first = col[0][0] if col[0] else None
        if first and first.day <= 7 and c - last_col >= 3 and c <= WEEKS - 2:
            out.append(mtext(GX + c * PITCH, GY - 10, MONTHS[first.month - 1], 10, MUTED))
            last_col = c
    for r, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(mtext(24, cy(r) + 3.5, name, 10, MUTED))

    # 空槽垫底，上面是会被吃掉的格子
    out.append(f'<defs><rect id="d" width="{CELL}" height="{CELL}" rx="2.5"/>'
               f'<pattern id="slots" x="{GX}" y="{GY}" width="{PITCH}" height="{PITCH}" '
               f'patternUnits="userSpaceOnUse"><rect width="{CELL}" height="{CELL}" rx="2.5" '
               f'fill="{TRACK}"/></pattern></defs>'
               f'<rect x="{GX}" y="{GY}" width="{WEEKS * PITCH}" height="{7 * PITCH}" fill="url(#slots)"/>')
    eaten = []                                        # (时间, 这一口的贡献数)
    for c, col in enumerate(weeks):
        for r, cell in enumerate(col):
            if not cell:
                continue
            _, n, lvl = cell
            t = route.eat_time(c, r)
            if n:
                eaten.append((t, n))
            out.append('<use href="#d" x="%d" y="%d" fill="%s">%s</use>'
                       % (GX + c * PITCH, GY + r * PITCH, LEVELS[min(lvl, 4)], route.show(0, t)))

    # 计分牌：每吃到一天有贡献的格子就跳一次
    eaten.sort()
    total = sum(n for _, n in eaten)
    out.append(mtext(24, 31, "SCORE", 13, MUTED))
    sx, score, marks = 24 + tw("SCORE ", 13), 0, [(0.0, 0)]
    for t, n in eaten:
        score += n
        marks.append((t, score))
    for (t, s), nxt in zip(marks, marks[1:] + [(None, None)]):
        hidden = ' visibility="hidden"' if t > 0 else ""
        out.append(mtext(sx, 31, "%05d" % s, 13, GOLD, bold=True,
                         extra=hidden).replace("</text>", route.show(t, nxt[0]) + "</text>"))
    out.append(mtext(W - 24, 31, "%s contributions in the last year" % num(total), 12, MUTED, anchor="end"))

    # 角色：追兵先画，吃豆人压在最上面
    out.append('<g class="px">%s%s</g>'
               % ("".join(clawd(route, *c) for c in reversed(CAST)), pacman(route)))

    # READY! / CLEAR!
    mid_x, mid_y = GX + WEEKS * PITCH / 2 - 2, GY + 7 * PITCH / 2 - 2

    def banner(text, color, anim, blink):
        w = tw(text, 15) + 28
        pulse = ('<animate attributeName="opacity" calcMode="discrete" values="1;.25" dur=".5s" '
                 'repeatCount="indefinite"/>' if blink else "")
        return (f'<g visibility="hidden">{anim}'
                f'<rect x="{mid_x - w / 2:.1f}" y="{mid_y - 15}" width="{w:.1f}" height="30" rx="6" '
                f'fill="{BG}" stroke="{color}" stroke-opacity=".6"/>'
                + mtext(mid_x, mid_y + 5.5, text, 15, color, bold=True,
                        anchor="middle").replace("</text>", pulse + "</text>") + '</g>')

    out.append(banner("READY!", GOLD, route.show(0, INTRO * 0.85), True).replace(
        '<g visibility="hidden">', "<g>", 1))
    out.append(banner("CLEAR!  %05d" % total, CORAL, route.show(route.cleared + 0.2), False))

    # 图例
    ly = GY + 7 * PITCH + 9
    lx = W - 24 - tw("More", 10)
    out.append(mtext(lx, ly + 9, "More", 10, MUTED))
    for i in range(4, -1, -1):
        lx -= PITCH if i < 4 else PITCH + 1
        out.append('<use href="#d" x="%g" y="%g" fill="%s"/>' % (lx, ly, LEVELS[i]))
    out.append(mtext(lx - 6, ly + 9, "Less", 10, MUTED, anchor="end"))
    out.append(mtext(24, ly + 9, "1UP pac-man", 10, GOLD)
               + mtext(24 + tw("1UP pac-man  ", 10), ly + 9, "vs", 10, MUTED)
               + mtext(24 + tw("1UP pac-man  vs  ", 10), ly + 9, "clawd x3", 10, CLAUDE))

    return shell(W, H, "\n  ".join(out), "G",
                 "Pac-Man eating %s contributions from the last year, chased by three Claudes" % num(total))


def check(svg):
    """XML 能解析，且每条动画的 keyTimes 合法（不合法的 SMIL 会被浏览器整条丢弃）。"""
    doc = xml.dom.minidom.parseString(svg.encode("utf-8"))
    n = 0
    for tag in ("animate", "animateTransform"):
        for el in doc.getElementsByTagName(tag):
            n += 1
            if not el.hasAttribute("keyTimes"):
                continue
            keys = [float(k) for k in el.getAttribute("keyTimes").split(";")]
            vals = el.getAttribute("values").split(";")
            ok = (len(keys) == len(vals) and keys[0] == 0 and keys == sorted(keys)
                  and (el.getAttribute("calcMode") == "discrete" or keys[-1] == 1))
            if not ok:
                raise ValueError("bad keyTimes: %s" % el.toxml()[:200])
    return n


if __name__ == "__main__":
    from make_cards import FAILURES, OUT, USER, fetch_contributions

    year = datetime.date.today().year
    counts, lvls = fetch_contributions(year - 1, year)
    if FAILURES or not counts:
        sys.exit("refusing to write pacman.svg: could not read %s's calendar" % USER)
    art = board(counts, lvls)
    print("  %d animations ok" % check(art))
    with open(os.path.join(OUT, "pacman.svg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(art)
    print("  wrote assets/pacman.svg")
