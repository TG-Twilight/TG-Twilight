# -*- coding: utf-8 -*-
"""自托管的 GitHub 统计卡生成器 —— 配色跟 assets/banner.svg 完全一致。

不依赖 github-readme-stats 之类的公共实例（它们经常限流或直接下线），
只调 GitHub 公开 REST API，把结果画成 assets/stats-strip.svg（统计长条）、
assets/feature-*.svg（招牌横幅）与 assets/pin-*.svg（仓库卡），
由 .github/workflows/stats.yml 每天跑一次并提交。

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

# 顺序无所谓，README 里按分组摆；新增仓库记得同时在 README 里放上对应的 pin-*.svg
PINS = [
    "Any.ADB", "Call.Editor", "JKS.Recover", "Fastboot.js-Next",
    "CaveStory-rs", "DeskPins",
    "Starstruck", "Gamer-Skill-Icons",
]

# 招牌项目单独画一张全宽横幅卡 → assets/feature-<name>.svg
FEATURE = "AWAvenue-Ads-Rule"
FEATURE_TAGLINE = "The upstream of many great ad-block lists — one of the best in open source."
FEATURE_WORKS_WITH = ["AdGuard", "AdAway", "hosts", "Mosdns", "Clash Meta", "QuantumultX"]

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
    f = by_name.get(FEATURE)
    feature = f and {"name": f["name"], "stars": f.get("stargazers_count", 0),
                     "forks": f.get("forks_count", 0), "since": (f.get("created_at") or "")[:4]}

    created = (user.get("created_at") or "2015-01-01")[:4]
    today = datetime.date.today()
    contrib = fetch_contributions(int(created), today.year)

    return {
        "contrib":   summarise(contrib),
        "pins":      pins,
        "feature":   feature,
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


LANG_ALIAS = {"Adblock Filter List": "Adblock"}


def strip_card(d):
    """一条 880×124 的细长统计条：关键数字 | 语言比例 | 逐年贡献。刻意做得低调。"""
    W, H = 880, 124
    out = []

    def caption(x, text, anchor="start", color=MUTED):
        return (f'<text x="{x}" y="30" fill="{color}" font-family="{MONO}" font-size="10" '
                f'letter-spacing="1.6" text-anchor="{anchor}">{text}</text>')

    def fade(i, body):
        return (f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".5s" '
                f'begin="{0.15 + i * 0.05:.2f}s" fill="freeze"/>{body}</g>')

    # ① 关键数字，3 × 2
    k = d["contrib"] or {}
    metrics = [("STARS", d["stars"]), ("COMMITS", d["commits"]), ("CONTRIBS", k.get("total")),
               ("PRS", d["prs"]), ("ISSUES", d["issues"]), ("FOLLOWERS", d["followers"])]
    out.append(caption(24, "GITHUB"))
    for i, (label, value) in enumerate(metrics):
        x, y = 24 + (i % 3) * 96, 60 + (i // 3) * 38
        out.append(fade(i, f'<text x="{x}" y="{y}" fill="{GOLD}" font-family="{MONO}" font-size="15" '
                           f'font-weight="600">{num(value)}</text>'
                           f'<text x="{x}" y="{y + 14}" fill="{MUTED}" font-family="{SANS}" '
                           f'font-size="9.5" letter-spacing=".8">{label}</text>'))

    for x in (316, 624):
        out.append(f'<rect x="{x}" y="22" width="1" height="{H - 44}" fill="{ORANGE}" opacity=".2"/>')

    # ② 语言比例
    BX, BY, BW, BH = 340, 42, 260, 7
    total = sum(d["langs"].values())
    out.append(caption(BX, "LANGUAGES"))
    if total:
        top = d["langs"].most_common(5)
        rest = total - sum(v for _, v in top)
        if rest / total >= 0.001:
            top.append(("Other", rest))
        seg, x = [], BX
        for i, (_, size) in enumerate(top):
            w = BW * size / total
            seg.append(f'<rect x="{x:.1f}" y="{BY}" width="{w:.1f}" height="{BH}" fill="{RAMP[i % len(RAMP)]}"/>')
            x += w
        out.append(f'<clipPath id="barclipT"><rect x="{BX}" y="{BY}" width="{BW}" height="{BH}" rx="{BH / 2}"/></clipPath>'
                   f'<g clip-path="url(#barclipT)">{"".join(seg)}</g>')
        for i, (name, size) in enumerate(top):
            cx, cy = BX + (i % 2) * 136, 70 + (i // 2) * 18
            out.append(fade(i, f'<circle cx="{cx + 3}" cy="{cy - 3.5}" r="3" fill="{RAMP[i % len(RAMP)]}"/>'
                               f'<text x="{cx + 11}" y="{cy}" fill="{INK}" font-family="{SANS}" '
                               f'font-size="11">{esc(LANG_ALIAS.get(name, name))}</text>'
                               f'<text x="{cx + 122}" y="{cy}" fill="{MUTED}" font-family="{MONO}" '
                               f'font-size="10" text-anchor="end">{size / total * 100:.1f}%</text>'))

    # ③ 逐年贡献
    L, R, BASE, TOP = 648, 856, 94, 44
    out.append(caption(L, "CONTRIBUTIONS"))
    if k:
        out.append(caption(R, "%s total" % num(k["total"]), anchor="end", color=GOLD))
        years = k["years"]
        peak = max(n for _, n, _ in years) or 1
        slot = (R - L) / len(years)
        bw = min(24, slot - 14)
        for i, (year, n, partial) in enumerate(years):
            h = max(2, (BASE - TOP) * n / peak)
            x = L + slot * i + (slot - bw) / 2
            out.append(f'<rect x="{x:.1f}" y="{BASE - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="2" '
                       f'fill="{GOLD if n == peak else ORANGE}" opacity=".85">'
                       f'<title>{year}: {n}</title></rect>'
                       f'<text x="{x + bw / 2:.1f}" y="{BASE + 14}" fill="{MUTED}" font-family="{MONO}" '
                       f'font-size="9.5" text-anchor="middle">{year}{"*" if partial else ""}</text>')
        out.append(f'<rect x="{L}" y="{BASE + 1}" width="{R - L}" height="1" fill="{ORANGE}" opacity=".2"/>')

    return shell(W, H, "", "\n  ".join(out), "T", label="GitHub stats")


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


def feature_card(r):
    """招牌项目的全宽横幅：左边名字 / 一句话 / 兼容工具，右边大号 star 数。"""
    W, H, SPLIT = 880, 220, 624
    CX = (SPLIT + W) / 2
    out = []

    # 右侧落日余晖，垫在 star 数后面
    out.append(f'<defs><radialGradient id="glowF" cx="50%" cy="50%" r="50%">'
               f'<stop offset="0%" stop-color="{CORAL}" stop-opacity=".30"/>'
               f'<stop offset="60%" stop-color="{ORANGE}" stop-opacity=".08"/>'
               f'<stop offset="100%" stop-color="{ORANGE}" stop-opacity="0"/>'
               f'</radialGradient></defs>'
               f'<ellipse cx="{CX:.0f}" cy="104" rx="150" ry="104" fill="url(#glowF)"/>')

    # 左：眉标 + 名字 + 一句话
    out.append(f'<g transform="translate(32,31)"><g fill="none" stroke="{ORANGE}" stroke-width="1.5" '
               f'stroke-linejoin="round" stroke-linecap="round">'
               f'<path d="M8 1.2L14 3.4V8c0 3.6-2.6 6-6 7-3.4-1-6-3.4-6-7V3.4z"/>'
               f'<path d="M5.4 8.2l1.9 1.8 3.5-3.8"/></g></g>')
    out.append(f'<text x="56" y="44" fill="{ORANGE}" font-family="{MONO}" font-size="11" '
               f'letter-spacing="2">FLAGSHIP &#183; SINCE {esc(r["since"])}</text>')
    out.append(f'<text x="30" y="90" fill="{GOLD}" font-family="{SANS}" font-size="32" '
               f'font-weight="700">{esc(r["name"])}</text>')
    out.append(f'<text x="32" y="118" fill="{INK}" font-family="{SANS}" font-size="13.5">'
               f'{esc(FEATURE_TAGLINE)}</text>')
    out.append(f'<rect x="32" y="134" width="0" height="1.6" fill="url(#ruleF)">'
               f'<animate attributeName="width" from="0" to="280" dur=".9s" begin=".15s" fill="freeze"/></rect>')

    # 左下：兼容工具标签
    chips, x = [], 32
    for i, name in enumerate(FEATURE_WORKS_WITH):
        w = est(name, 12) + 22
        chips.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".4s" '
                     f'begin="{0.45 + i * 0.07:.2f}s" fill="freeze"/>'
                     f'<rect x="{x:.1f}" y="170" width="{w:.1f}" height="24" rx="12" fill="#2A1B33" '
                     f'stroke="{ORANGE}" stroke-opacity=".45"/>'
                     f'<text x="{x + w / 2:.1f}" y="186" fill="{INK}" font-family="{SANS}" font-size="12" '
                     f'text-anchor="middle">{esc(name)}</text></g>')
        x += w + 8
    out.append(f'<text x="32" y="160" fill="{MUTED}" font-family="{MONO}" font-size="10.5" '
               f'letter-spacing="1.5">WORKS WITH</text>' + "".join(chips))

    # 右：star / fork
    out.append(f'<rect x="{SPLIT}" y="40" width="1" height="{H - 80}" fill="{ORANGE}" opacity=".22"/>')
    out.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".7s" '
               f'begin=".3s" fill="freeze"/>'
               f'<g transform="translate({CX - 11:.0f},38) scale(1.4)">{ICONS["star"] % GOLD}</g>'
               f'<text x="{CX:.0f}" y="114" fill="{GOLD}" font-family="{MONO}" font-size="46" '
               f'font-weight="700" text-anchor="middle">{num(r["stars"])}</text>'
               f'<text x="{CX:.0f}" y="140" fill="{INK}" font-family="{SANS}" font-size="12" '
               f'font-weight="600" letter-spacing="2.2" text-anchor="middle">STARS</text></g>')
    forks = "%s forks" % num(r["forks"])
    fw = 18 + est(forks, 12)
    fx = CX - fw / 2
    out.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".5s" '
               f'begin=".6s" fill="freeze"/>'
               f'<g transform="translate({fx:.0f},{175}) scale(0.8)">{ICONS["fork"].replace("%s", MUTED)}</g>'
               f'<text x="{fx + 18:.0f}" y="186" fill="{MUTED}" font-family="{MONO}" '
               f'font-size="12">{forks}</text></g>')

    return shell(W, H, "", "\n  ".join(out), "F",
                 label="%s — %s stars" % (r["name"], r["stars"]))


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
    if not data["feature"]:
        sys.exit("refusing to write cards: feature repo %s not found" % FEATURE)
    if len(data["pins"]) != len(PINS):
        sys.exit("refusing to write cards: only resolved %d/%d pinned repos"
                 % (len(data["pins"]), len(PINS)))

    os.makedirs(OUT, exist_ok=True)
    cards = [("stats-strip.svg", strip_card(data))]
    cards.append(("feature-%s.svg" % FEATURE, feature_card(data["feature"])))
    cards += [("pin-%s.svg" % r["name"], pin_card(r)) for r in data["pins"]]
    for fname, svg in cards:
        with open(os.path.join(OUT, fname), "w", encoding="utf-8") as f:
            f.write(svg)
        print("  wrote assets/" + fname)
