# -*- coding: utf-8 -*-
"""自托管的 GitHub 统计卡生成器 —— 配色跟 assets/banner.svg 完全一致。

不依赖 github-readme-stats 之类的公共实例（它们经常限流或直接下线），
只调 GitHub 公开 REST API，把结果画成 assets/stats-card.svg 与
assets/langs-card.svg，由 .github/workflows/stats.yml 每天跑一次并提交。

    python tools/make_cards.py            # 匿名调用，60 次/小时，够用
    GITHUB_TOKEN=xxx python tools/make_cards.py   # CI 里走 token，额度更高
"""
import collections
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request

USER = os.environ.get("GH_USER", "TG-Twilight")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")

# ── sunset palette，跟 banner.svg 同源 ──────────────────────────────
BG      = "#1B1123"
INK     = "#F3D9C4"
GOLD    = "#FFD166"
ORANGE  = "#FF8C42"
CORAL   = "#FF5F6D"
MUTED   = "#9B8494"
RAMP    = ["#FF8C42", "#FFD166", "#FF5F6D", "#C05299", "#7B4B94", "#E8A33D", "#6E5A78"]

PINS = ["AWAvenue-Ads-Rule", "Starstruck", "Gamer-Skill-Icons", "JKS.Recover"]

SANS = "'Segoe UI',Roboto,'Helvetica Neue',Arial,'PingFang SC','Microsoft YaHei',sans-serif"
MONO = "ui-monospace,SFMono-Regular,'Cascadia Mono',Consolas,'Liberation Mono',monospace"


FAILURES = []


def api(path, default=None):
    url = path if path.startswith("http") else "https://api.github.com" + path
    req = urllib.request.Request(url, headers={
        "User-Agent": "tg-twilight-cards",
        "Accept": "application/vnd.github+json",
    })
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.load(r)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print("  ! %s -> %s" % (url, e), file=sys.stderr)
        FAILURES.append(url)
        return default


def count(query):
    """search API 的 total_count，取不到就返回 None（卡片上显示 —）。"""
    r = api("/search/" + query + "&per_page=1")
    return r.get("total_count") if isinstance(r, dict) else None


def collect():
    user = api("/users/" + USER) or {}
    repos, page = [], 1
    while True:
        batch = api("/users/%s/repos?per_page=100&type=owner&page=%d" % (USER, page)) or []
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    own = [r for r in repos if not r.get("fork")]

    langs = collections.Counter()
    for r in own:
        for name, size in (api(r["languages_url"], {}) or {}).items():
            langs[name] += size

    by_name = {r["name"]: r for r in repos}
    pins = [{"name": r["name"], "lang": r.get("language"),
             "stars": r.get("stargazers_count", 0), "forks": r.get("forks_count", 0)}
            for r in (by_name.get(n) for n in PINS) if r]

    created = (user.get("created_at") or "2015-01-01")[:4]
    today = datetime.date.today()
    contrib = fetch_contributions(int(created), today.year)

    return {
        "contrib":   summarise(contrib),
        "pins":      pins,
        "name":      user.get("name") or USER,
        "stars":     sum(r.get("stargazers_count", 0) for r in own),
        "forks":     sum(r.get("forks_count", 0) for r in own),
        "followers": user.get("followers"),
        "commits":   count("commits?q=author:" + USER),
        "prs":       count("issues?q=author:%s+type:pr" % USER),
        "issues":    count("issues?q=author:%s+type:issue" % USER),
        "langs":     langs,
    }


# ── SVG 零件 ────────────────────────────────────────────────────────
ICONS = {
    "star": '<path d="M8 1.4l2 4.1 4.5.7-3.3 3.2.8 4.5L8 11.8l-4 2.1.8-4.5L1.5 6.2 6 5.5z" fill="%s"/>',
    "fork": '<g fill="none" stroke="%s" stroke-width="1.6" stroke-linecap="round">'
            '<circle cx="4" cy="3.8" r="2.1"/><circle cx="12" cy="3.8" r="2.1"/>'
            '<circle cx="8" cy="12.6" r="2.1"/>'
            '<path d="M4 5.9v1.4a2 2 0 002 2h4a2 2 0 002-2V5.9M8 9.3v1.2"/></g>',
    "commit": '<g fill="none" stroke="%s" stroke-width="1.6" stroke-linecap="round">'
              '<circle cx="8" cy="8" r="3"/><path d="M1.4 8h3.4M11.2 8h3.4"/></g>',
    "pr": '<g fill="none" stroke="%s" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
          '<circle cx="4" cy="12.3" r="2"/><circle cx="4" cy="3.7" r="2"/><circle cx="12" cy="12.3" r="2"/>'
          '<path d="M4 5.7v4.6M12 10.3V6.2a2 2 0 00-2-2H7.4M9.6 2.1L7.2 4.2l2.4 2.1"/></g>',
    "issue": '<g fill="none" stroke="%s" stroke-width="1.6"><circle cx="8" cy="8" r="6.2"/></g>'
             '<circle cx="8" cy="8" r="1.8" fill="%s"/>',
    "user": '<g fill="none" stroke="%s" stroke-width="1.6" stroke-linecap="round">'
            '<circle cx="8" cy="5.1" r="2.8"/><path d="M2.7 14.2a5.3 5.3 0 0110.6 0"/></g>',
    "repo": '<g fill="none" stroke="%s" stroke-width="1.5" stroke-linejoin="round">'
            '<path d="M3 2.6h8.2a1.6 1.6 0 011.6 1.6v9.2H4.6A1.6 1.6 0 013 11.8z"/>'
            '<path d="M3 11.4h9.8"/></g>',
}


def est(text, size):
    """粗略字宽：CJK 按 1em，其余按 0.55em。"""
    w = 0.0
    for ch in text:
        w += 1.0 if ord(ch) > 0x2E80 else 0.55
    return w * size


def esc(t):
    return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def icon(kind, x, y, color=ORANGE):
    body = ICONS[kind]
    body = body % ((color, color) if body.count("%s") == 2 else color)
    return '<g transform="translate(%s,%s)">%s</g>' % (x, y, body)


def num(v):
    return "—" if v is None else "{:,}".format(v)


def shell(w, h, title, body, uid, label=None):
    """卡片外壳：暗底、渐变描边。title 为空时不画标题栏（仓库小卡用）。"""
    head = ""
    if title:
        head = (f'<text x="24" y="33" fill="{GOLD}" font-family="{SANS}" font-size="16" '
                f'font-weight="600">{title}</text>\n'
                f'  <rect x="24" y="42" width="0" height="1.6" fill="url(#rule{uid})">'
                f'<animate attributeName="width" from="0" to="{w * 0.42:.0f}" dur=".9s" '
                f'begin=".1s" fill="freeze"/></rect>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{label or title}">
  <defs>
    <linearGradient id="edge{uid}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{ORANGE}" stop-opacity=".85"/>
      <stop offset="55%" stop-color="{CORAL}" stop-opacity=".55"/>
      <stop offset="100%" stop-color="#7B4B94" stop-opacity=".45"/>
    </linearGradient>
    <linearGradient id="rule{uid}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{GOLD}" stop-opacity=".9"/>
      <stop offset="100%" stop-color="{CORAL}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x=".9" y=".9" width="{w - 1.8}" height="{h - 1.8}" rx="12" fill="{BG}" stroke="url(#edge{uid})" stroke-width="1.8"/>
  {head}
  {body}
</svg>
'''


def stats_card(d):
    rows = [
        ("star",   "Total Stars Earned", d["stars"]),
        ("commit", "Total Commits",      d["commits"]),
        ("fork",   "Total Forks",        d["forks"]),
        ("pr",     "Pull Requests",      d["prs"]),
        ("issue",  "Issues Opened",      d["issues"]),
        ("user",   "Followers",          d["followers"]),
    ]
    W, COLW = 470, 196
    out = []
    for i, (ic, label, value) in enumerate(rows):
        cx = 24 + (i % 2) * 226
        cy = 66 + (i // 2) * 40
        delay = 0.25 + i * 0.09
        out.append(
            f'<g opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" dur=".5s" begin="{delay:.2f}s" fill="freeze"/>'
            f'{icon(ic, cx, cy)}'
            f'<text x="{cx + 26}" y="{cy + 12.5}" fill="{INK}" font-family="{SANS}" font-size="13">{label}</text>'
            f'<text x="{cx + COLW}" y="{cy + 12.5}" fill="{GOLD}" font-family="{MONO}" font-size="14" '
            f'font-weight="600" text-anchor="end">{num(value)}</text>'
            f'</g>')
    return shell(W, 200, "%s &#183; GitHub" % d["name"], "\n  ".join(out), "S")


def langs_card(d):
    total = sum(d["langs"].values())
    if not total:
        return shell(400, 200, "Top Languages",
                     f'<text x="24" y="110" fill="{MUTED}" font-family="{SANS}" font-size="13">no data</text>', "L")

    top = d["langs"].most_common(6)
    rest = total - sum(v for _, v in top)
    if rest / total >= 0.001:            # 低于 0.1% 的尾巴不值得占一行
        top.append(("Other", rest))

    W, BX, BY, BW, BH = 400, 24, 58, 352, 11
    seg, x = [], BX
    for i, (name, size) in enumerate(top):
        w = BW * size / total
        seg.append(f'<rect x="{x:.1f}" y="{BY}" width="0" height="{BH}" fill="{RAMP[i % len(RAMP)]}">'
                   f'<animate attributeName="width" from="0" to="{w:.1f}" dur=".9s" '
                   f'begin="{0.2 + i * 0.08:.2f}s" fill="freeze"/></rect>')
        x += w
    bar = (f'<clipPath id="barclip"><rect x="{BX}" y="{BY}" width="{BW}" height="{BH}" rx="{BH / 2}"/></clipPath>'
           f'<rect x="{BX}" y="{BY}" width="{BW}" height="{BH}" rx="{BH / 2}" fill="#2A1B33"/>'
           f'<g clip-path="url(#barclip)">{"".join(seg)}</g>')

    legend = []
    rows = (len(top) + 1) // 2           # 图例行高按行数摊开，底部不留空档
    gap = (184 - 86) / rows
    for i, (name, size) in enumerate(top):
        cx = 24 + (i % 2) * 184
        cy = 86 + gap * (i // 2) + gap / 2 + 4.5
        pct = size / total * 100
        label = name if len(name) <= 20 else name[:19] + "…"
        legend.append(
            f'<g opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" dur=".5s" begin="{0.5 + i * 0.07:.2f}s" fill="freeze"/>'
            f'<circle cx="{cx + 4}" cy="{cy - 4:.1f}" r="4.2" fill="{RAMP[i % len(RAMP)]}"/>'
            f'<text x="{cx + 16}" y="{cy:.1f}" fill="{INK}" font-family="{SANS}" font-size="12.5">{label}</text>'
            f'<text x="{cx + 168}" y="{cy:.1f}" fill="{MUTED}" font-family="{MONO}" font-size="11.5" '
            f'text-anchor="end">{pct:.1f}%</text>'
            f'</g>')

    return shell(W, 200, "Top Languages", bar + "\n  " + "\n  ".join(legend), "L")


def fetch_contributions(created_year, this_year):
    """从公开的贡献日历页面逐年抓 date -> count（不走 API，不吃 60 次/小时的额度）。"""
    days = {}
    for year in range(created_year, this_year + 1):
        url = ("https://github.com/users/%s/contributions?from=%d-01-01&to=%d-12-31"
               % (USER, year, year))
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; tg-twilight-cards)",
            "X-Requested-With": "XMLHttpRequest",
        })
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                html = r.read().decode("utf-8", "replace")
        except Exception as e:                      # noqa: BLE001
            print("  ! %s -> %s" % (url, e), file=sys.stderr)
            FAILURES.append(url)
            continue

        tips = {}
        for cell_id, text in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
            m = re.match(r"\s*([\d,]+)\s+contribution", text)
            tips[cell_id] = int(m.group(1).replace(",", "")) if m else 0

        for tag in re.findall(r'<td[^>]*class="ContributionCalendar-day"[^>]*>', html):
            date = re.search(r'data-date="([\d-]{10})"', tag)
            cid = re.search(r'id="([^"]+)"', tag)
            if not date:
                continue
            n = tips.get(cid.group(1) if cid else "", None)
            if n is None:                            # 没有 tooltip 时退回 level
                lvl = re.search(r'data-level="(\d+)"', tag)
                n = 1 if lvl and lvl.group(1) != "0" else 0
            days[date.group(1)] = n
    return days


def summarise(days):
    """总贡献 / 最高单日 / 活跃天数 / 最近 12 个自然月的月度桶。"""
    if not days:
        return None
    # 按自然年抓的日历会带上账号注册前 / 今天之后的空日子，只认真正有贡献的区间
    active_dates = sorted(d for d, n in days.items() if n > 0)
    if not active_dates:
        return None
    first = datetime.date.fromisoformat(active_dates[0])
    last = datetime.date.fromisoformat(active_dates[-1])

    best_day, best_n = None, 0
    for d, n in days.items():
        if n > best_n:
            best_day, best_n = d, n

    # 按年聚合：这位是"爆发式"维护者，按月看全是空档，按年才看得出节奏
    buckets = []
    for y in range(first.year, last.year + 1):
        pre = "%04d-" % y
        total = sum(n for d, n in days.items() if d.startswith(pre))
        buckets.append((y, total, y == last.year))
    while len(buckets) > 1 and buckets[0][1] == 0:      # 开头的空年份不占位
        buckets.pop(0)

    fmt = lambda x: x.strftime("%b %Y").replace(" 0", " ")
    return {
        "total": sum(days.values()),
        "range": "%s — %s" % (fmt(first), fmt(last)),
        "active": sum(1 for n in days.values() if n > 0),
        "best_n": best_n,
        "best_day": (datetime.date.fromisoformat(best_day).strftime("%b %d, %Y").replace(" 0", " ")
                     if best_day else "—"),
        "years": buckets,
    }


def contrib_card(c):
    W, H = 880, 190
    out = []

    # 左：总量
    out.append(f'<text x="24" y="102" fill="{GOLD}" font-family="{MONO}" font-size="42" '
               f'font-weight="700" opacity="0">{num(c["total"])}'
               f'<animate attributeName="opacity" from="0" to="1" dur=".7s" begin=".25s" fill="freeze"/></text>')
    out.append(f'<text x="26" y="126" fill="{INK}" font-family="{SANS}" font-size="12" '
               f'font-weight="600" letter-spacing="1.1">TOTAL CONTRIBUTIONS</text>')
    out.append(f'<text x="26" y="145" fill="{MUTED}" font-family="{MONO}" font-size="10.5">{c["range"]}</text>')
    out.append(f'<text x="26" y="164" fill="{MUTED}" font-family="{MONO}" font-size="10.5">'
               f'{c["active"]} active days &#183; best {c["best_n"]} on {c["best_day"]}</text>')

    out.append(f'<rect x="284" y="56" width="1" height="{H - 100}" fill="{ORANGE}" opacity=".22"/>')

    # 右：逐年的贡献节奏
    BX, BR, BASE, TOP = 314, W - 24, 142, 62
    peak = max(n for _, n, _ in c["years"]) or 1
    slot = (BR - BX) / len(c["years"])
    bw = min(78, slot - 22)
    for i, (year, n, partial) in enumerate(c["years"]):
        h = max(2.5, (BASE - TOP) * n / peak)
        x = BX + slot * i + (slot - bw) / 2
        fill = GOLD if n == peak else ORANGE
        out.append(f'<rect x="{x:.1f}" y="{BASE - h:.1f}" width="{bw:.1f}" height="0" rx="3" '
                   f'fill="{fill}" opacity=".9">'
                   f'<animate attributeName="height" from="0" to="{h:.1f}" dur=".7s" '
                   f'begin="{0.3 + i * 0.05:.2f}s" fill="freeze"/></rect>')
        if n:
            out.append(f'<text x="{x + bw / 2:.1f}" y="{BASE - h - 6:.1f}" fill="{MUTED}" '
                       f'font-family="{MONO}" font-size="11" text-anchor="middle" opacity="0">{n}'
                       f'<animate attributeName="opacity" from="0" to="1" dur=".4s" '
                       f'begin="{0.85 + i * 0.05:.2f}s" fill="freeze"/></text>')
        out.append(f'<text x="{x + bw / 2:.1f}" y="{BASE + 15:.1f}" fill="{MUTED}" '
                   f'font-family="{MONO}" font-size="10.5" text-anchor="middle">'
                   f'{year}{"*" if partial else ""}</text>')
    out.append(f'<rect x="{BX}" y="{BASE + 1}" width="{BR - BX}" height="1" fill="{ORANGE}" opacity=".25"/>')
    out.append(f'<text x="{BR}" y="{H - 18}" fill="{MUTED}" font-family="{SANS}" font-size="10.5" '
               f'text-anchor="end">by year &#183; * year to date</text>')

    return shell(W, H, "Contributions", "".join(out), "K", label="contribution rhythm")


def pin_card(r):
    """仓库小卡：名字 + 语言 + star / fork。中文说明留在 README 里，避免 SVG 缺字体。"""
    W, H = 430, 96
    name = esc(r["name"])
    fs = 16 if est(name, 16) < 340 else 14

    foot, x = [], 20
    if r["lang"]:
        foot.append(f'<circle cx="{x + 4}" cy="{H - 26}" r="4.2" fill="{ORANGE}"/>'
                    f'<text x="{x + 14}" y="{H - 22}" fill="{MUTED}" font-family="{SANS}" '
                    f'font-size="11.5">{esc(r["lang"])}</text>')
        x += 14 + est(r["lang"], 11.5) + 22
    for ic, val in (("star", r["stars"]), ("fork", r["forks"])):
        foot.append(f'<g transform="translate({x:.0f},{H - 34}) scale(0.8)">'
                    f'{ICONS[ic].replace("%s", MUTED)}</g>'
                    f'<text x="{x + 18:.0f}" y="{H - 22}" fill="{INK}" font-family="{MONO}" '
                    f'font-size="11.5">{num(val)}</text>')
        x += 18 + est(num(val), 11.5) + 24

    body = (f'{icon("repo", 20, 21)}'
            f'<text x="44" y="34" fill="{GOLD}" font-family="{SANS}" font-size="{fs}" '
            f'font-weight="600">{name}</text>'
            f'<rect x="20" y="50" width="0" height="1.4" fill="url(#ruleP)">'
            f'<animate attributeName="width" from="0" to="170" dur=".8s" begin=".15s" fill="freeze"/></rect>'
            f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".5s" '
            f'begin=".35s" fill="freeze"/>{"".join(foot)}</g>')

    return shell(W, H, "", body, "P", label="%s — %s stars" % (r["name"], r["stars"]))


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                # noqa: BLE001
        pass
    print("fetching %s ..." % USER)
    data = collect()
    print("  stars=%s forks=%s commits=%s prs=%s issues=%s followers=%s langs=%d pins=%d"
          % (data["stars"], data["forks"], data["commits"], data["prs"],
             data["issues"], data["followers"], len(data["langs"]), len(data["pins"])))
    if data["contrib"]:
        k = data["contrib"]
        print("  contributions=%s active_days=%s best=%s months=%s"
              % (k["total"], k["active"], k["best_n"], [(y, n) for y, n, _ in k["years"]]))

    if FAILURES:
        sys.exit("refusing to write cards: %d API call(s) failed (rate limit?) -- "
                 "keeping the previous SVGs" % len(FAILURES))
    if len(data["pins"]) != len(PINS):
        sys.exit("refusing to write cards: only resolved %d/%d pinned repos"
                 % (len(data["pins"]), len(PINS)))

    os.makedirs(OUT, exist_ok=True)
    cards = [("stats-card.svg", stats_card(data)), ("langs-card.svg", langs_card(data))]
    if data["contrib"]:
        cards.append(("contrib-card.svg", contrib_card(data["contrib"])))
    cards += [("pin-%s.svg" % r["name"], pin_card(r)) for r in data["pins"]]
    for fname, svg in cards:
        with open(os.path.join(OUT, fname), "w", encoding="utf-8") as f:
            f.write(svg)
        print("  wrote assets/" + fname)
