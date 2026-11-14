# -*- coding: utf-8 -*-
"""自托管的 GitHub 资料卡生成器 —— 落日终端风格，配色见 tools/sunset.py。

不依赖 github-readme-stats 之类的公共实例（它们经常限流或直接下线），
只调 GitHub 公开 REST API 和公开的贡献日历页面，一次取数、画出全部动态图：

    assets/hero.svg       页首 neofetch 终端卡      （tools/make_hero.py）
    assets/pacman.svg     吃豆人 + Claude 小精灵贡献图（tools/make_pacman.py）
    assets/feature-*.svg  主项目横幅
    assets/pin-*.svg      仓库小卡

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

from sunset import (CORAL, GOLD, INK, MONO, MUTED, ORANGE, PANEL, esc, mrow, mtext, num, shell,
                    tw)

# 新增仓库：加进对应分组，并在 README 的同名小节里放上 pin-*.svg 和说明
GROUPS = {
    # 目录名: (强调色, [仓库…])。目录名会印在卡片上，README 的小标题与之对应
    "apps":  (ORANGE,    ["c001apk", "Any.ADB", "Call.Editor", "DeskPins"]),
    "web":   (CORAL,     ["JKS.Recover", "Fastboot.js-Next", "Starstruck", "Gamer-Skill-Icons"]),
    "games": ("#C05299", ["CaveStory-rs", "AC130.Zombie.Gunship"]),
}
PINS = [name for _, names in GROUPS.values() for name in names]
GROUP_OF = {name: group for group, (_, names) in GROUPS.items() for name in names}

# 主项目单独画一张全宽横幅卡 → assets/feature-<name>.svg
FEATURE = "AWAvenue-Ads-Rule"
FEATURE_TAGLINE = "The upstream of many great ad-block lists — one of the best in open source."
FEATURE_WORKS_WITH = ["AdGuard", "AdAway", "hosts", "Mosdns", "Clash Meta", "QuantumultX"]

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
             "stars": r.get("stargazers_count", 0), "forks": r.get("forks_count", 0),
             "pushed": r.get("pushed_at")}
            for r in (by_name.get(n) for n in PINS) if r]
    f = by_name.get(FEATURE)
    feature = f and {"name": f["name"], "stars": f.get("stargazers_count", 0),
                     "forks": f.get("forks_count", 0), "since": (f.get("created_at") or "")[:4]}

    created = (user.get("created_at") or "2015-01-01")[:4]
    today = datetime.date.today()
    days, levels = fetch_contributions(int(created), today.year)

    return {
        "contrib":   summarise(days),
        "days":      days,
        "levels":    levels,
        "created_at": user.get("created_at"),
        "repos":     user.get("public_repos"),
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
    """粗略字宽：CJK 按 1em，其余按等宽字体的 0.6em。"""
    w = 0.0
    for ch in text:
        w += 1.0 if ord(ch) > 0x2E80 else 0.6
    return w * size


def icon(kind, x, y, color=ORANGE):
    body = ICONS[kind]
    body = body % ((color, color) if body.count("%s") == 2 else color)
    return '<g transform="translate(%s,%s)">%s</g>' % (x, y, body)


def fetch_contributions(created_year, this_year):
    """从公开的贡献日历页面逐年抓 date -> count 与 date -> level（0-4）。

    不走 API，不吃 60 次/小时的额度。
    """
    days, levels = {}, {}
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
            lvl = re.search(r'data-level="(\d+)"', tag)
            lvl = int(lvl.group(1)) if lvl else 0
            n = tips.get(cid.group(1) if cid else "", None)
            if n is None:                            # 没有 tooltip 时退回 level
                n = 1 if lvl else 0
            days[date.group(1)] = n
            levels[date.group(1)] = lvl if lvl or not n else 1
    return days, levels


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


def pin_card(r):
    """仓库卡：像 ls -l 的一条记录 —— 所在目录、名字、star，下面是语言 / fork / 最近推送。

    中文说明留在 README 里，避免 SVG 缺字体。
    """
    W, H = 430, 104
    group = GROUP_OF.get(r["name"], "misc")
    accent = GROUPS[group][0] if group in GROUPS else ORANGE
    name = r["name"]
    fs = 17 if tw(name, 17) < 290 else 15
    stars = num(r["stars"])

    # 左侧色条 = 所属分组；第一行是路径
    out = [f'<rect x="16" y="18" width="4" height="{H - 36}" rx="2" fill="{accent}"/>',
           mrow(32, 31, 11, [("~/projects/", MUTED), (group + "/", accent)])[0],
           mtext(32, 56, name, fs, GOLD, bold=True),
           f'<g transform="translate({W - 22 - tw(stars, 13) - 20:.1f},18)">{ICONS["star"] % GOLD}</g>',
           mtext(W - 22, 31, stars, 13, GOLD, bold=True, anchor="end"),
           f'<rect x="32" y="66" width="0" height="1.2" fill="url(#ruleP)">'
           f'<animate attributeName="width" from="0" to="{W - 54}" dur=".8s" begin=".15s" fill="freeze"/></rect>']

    foot, x = [], 32
    if r["lang"]:
        foot.append(f'<circle cx="{x + 4}" cy="{H - 20.5}" r="4" fill="{accent}"/>'
                    + mtext(x + 14, H - 16.5, r["lang"], 11.5, INK))
        x += 14 + tw(r["lang"], 11.5) + 18
    forks = num(r["forks"])
    foot.append(f'<g transform="translate({x:.0f},{H - 27}) scale(0.8)">{ICONS["fork"].replace("%s", MUTED)}</g>'
                + mtext(x + 17, H - 16.5, forks, 11.5, INK))
    if r.get("pushed"):
        when = datetime.date.fromisoformat(r["pushed"][:10]).strftime("%b %Y")
        foot.append(mrow(W - 22 - tw("pushed " + when, 11), H - 16.5, 11,
                         [("pushed ", MUTED), (when, INK)])[0])
    out.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".5s" '
               f'begin=".35s" fill="freeze"/>{"".join(foot)}</g>')

    return shell(W, H, "".join(out), "P", "%s — %s stars" % (r["name"], r["stars"]))


def feature_card(r):
    """主项目的全宽横幅：左边名字 / 一句话 / 兼容工具，右边大号 star 数。"""
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
               f'letter-spacing="2">AD-BLOCK FILTER LIST &#183; SINCE {esc(r["since"])}</text>')
    out.append(f'<text x="30" y="90" fill="{GOLD}" font-family="{MONO}" font-size="32" '
               f'font-weight="700">{esc(r["name"])}</text>')
    out.append(f'<text x="32" y="118" fill="{INK}" font-family="{MONO}" font-size="12.5">'
               f'{esc(FEATURE_TAGLINE)}</text>')
    out.append(f'<rect x="32" y="134" width="0" height="1.6" fill="url(#ruleF)">'
               f'<animate attributeName="width" from="0" to="280" dur=".9s" begin=".15s" fill="freeze"/></rect>')

    # 左下：兼容工具标签
    chips, x = [], 32
    for i, name in enumerate(FEATURE_WORKS_WITH):
        w = est(name, 12) + 22
        chips.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".4s" '
                     f'begin="{0.45 + i * 0.07:.2f}s" fill="freeze"/>'
                     f'<rect x="{x:.1f}" y="170" width="{w:.1f}" height="24" rx="12" fill="{PANEL}" '
                     f'stroke="{ORANGE}" stroke-opacity=".45"/>'
                     f'<text x="{x + w / 2:.1f}" y="186" fill="{INK}" font-family="{MONO}" font-size="12" '
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
               f'<text x="{CX:.0f}" y="140" fill="{INK}" font-family="{MONO}" font-size="12" '
               f'font-weight="600" letter-spacing="2.2" text-anchor="middle">STARS</text></g>')
    forks = "%s forks" % num(r["forks"])
    fw = 18 + est(forks, 12)
    fx = CX - fw / 2
    out.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur=".5s" '
               f'begin=".6s" fill="freeze"/>'
               f'<g transform="translate({fx:.0f},{175}) scale(0.8)">{ICONS["fork"].replace("%s", MUTED)}</g>'
               f'<text x="{fx + 18:.0f}" y="186" fill="{MUTED}" font-family="{MONO}" '
               f'font-size="12">{forks}</text></g>')

    return shell(W, H, "\n  ".join(out), "F", "%s — %s stars" % (r["name"], r["stars"]))


def render(data):
    """把取到的数据画成全部 SVG，返回 [(文件名, 内容)]。"""
    from make_hero import hero
    from make_pacman import board, check

    cards = [("hero.svg", hero(data)), ("pacman.svg", board(data["days"], data["levels"]))]
    check(cards[1][1])
    cards.append(("feature-%s.svg" % FEATURE, feature_card(data["feature"])))
    cards += [("pin-%s.svg" % r["name"], pin_card(r)) for r in data["pins"]]
    return cards


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

    if not data["days"]:
        sys.exit("refusing to write cards: contribution calendar came back empty")

    os.makedirs(OUT, exist_ok=True)
    for fname, svg in render(data):
        with open(os.path.join(OUT, fname), "w", encoding="utf-8", newline="\n") as f:
            f.write(svg)
        print("  wrote assets/" + fname)
