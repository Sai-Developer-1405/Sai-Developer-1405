#!/usr/bin/env python3
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from html import escape

USER = os.environ.get("GH_USER", "Sai-Developer-1405")
TOKEN = os.environ.get("GH_TOKEN", "")
OUT = Path("assets")
OUT.mkdir(parents=True, exist_ok=True)

BG = "#0b0e11"
PANEL = "#0f141a"
GRID = "#202832"
TEXT = "#eaecef"
MUTED = "#8b949e"
ACCENT = "#36bcf7"
GREEN = "#39d353"
PURPLE = "#8b7cf6"
RED = "#f85149"


def api_get(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-actions-live-dashboard",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def contribution_data():
    query = """
    query($login:String!){
      user(login:$login){
        contributionsCollection{
          contributionCalendar{
            totalContributions
            weeks{contributionDays{date contributionCount}}
          }
        }
      }
    }
    """
    payload = {"query": query, "variables": {"login": USER}}
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "github-actions-live-dashboard",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return cal["totalContributions"], [d for w in cal["weeks"] for d in w["contributionDays"]]


def search_count(query):
    url = "https://api.github.com/search/issues?" + urllib.parse.urlencode({"q": query, "per_page": 1})
    return int(api_get(url).get("total_count", 0))


def current_streak(days):
    counts = {d["date"]: d["contributionCount"] for d in days}
    today = datetime.now(timezone.utc).date()
    streak = 0
    while counts.get(today.isoformat(), 0) > 0:
        streak += 1
        today = today.fromordinal(today.toordinal() - 1)
    return streak


def fallback_stats():
    return {
        "stars": 6,
        "repos": 16,
        "contrib": 27,
        "followers": 1,
        "prs": 0,
        "issues": 0,
        "streak": 1,
    }


def collect():
    try:
        user = api_get(f"https://api.github.com/users/{USER}")
        repos = api_get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&sort=updated")
        contrib_total, days = contribution_data()
        stars = sum(int(r.get("stargazers_count", 0)) for r in repos if not r.get("fork"))
        prs = search_count(f"author:{USER} is:pr")
        issues = search_count(f"author:{USER} is:issue")
        return {
            "stars": stars,
            "repos": int(user.get("public_repos", len(repos))),
            "contrib": int(contrib_total),
            "followers": int(user.get("followers", 0)),
            "prs": prs,
            "issues": issues,
            "streak": current_streak(days),
        }
    except Exception:
        return fallback_stats()


def stats_svg(stats):
    cells = [
        ("STARS", stats["stars"], ACCENT, 24, 98),
        ("REPOSITORIES", stats["repos"], PURPLE, 170, 98),
        ("CONTRIBUTIONS", stats["contrib"], GREEN, 335, 98),
        ("FOLLOWERS", stats["followers"], ACCENT, 24, 196),
        ("PULL REQUESTS", stats["prs"], PURPLE, 170, 196),
        ("CURRENT STREAK", stats["streak"], GREEN, 335, 196),
    ]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 255" width="500" height="255">',
        f'<rect width="500" height="255" rx="16" fill="{BG}" stroke="{GRID}"/>',
        f'<text x="24" y="31" fill="{ACCENT}" font-family="ui-monospace,monospace" font-size="11" font-weight="700">{escape(USER.upper())} · LIVE GITHUB TELEMETRY</text>',
        f'<text x="24" y="52" fill="{MUTED}" font-family="ui-sans-serif,system-ui" font-size="11">Auto-refreshed from GitHub Actions</text>',
    ]
    for label, value, color, x, y in cells:
        parts.append(f'<rect x="{x-8}" y="{y-25}" width="144" height="72" rx="10" fill="{PANEL}" stroke="{GRID}"/>')
        parts.append(f'<text x="{x+64}" y="{y-2}" text-anchor="middle" fill="{color}" font-family="ui-monospace,monospace" font-size="24" font-weight="800">{value}</text>')
        parts.append(f'<text x="{x+64}" y="{y+20}" text-anchor="middle" fill="{MUTED}" font-family="ui-sans-serif,system-ui" font-size="9" font-weight="700">{label}</text>')
    now = datetime.now().strftime("%d %b %Y · %H:%M")
    parts.append(f'<text x="476" y="240" text-anchor="end" fill="{MUTED}" font-family="ui-monospace,monospace" font-size="9">REFRESHED {escape(now)}</text>')
    parts.append('</svg>')
    return ''.join(parts)


def daily_svg():
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist)
    messages = [
        "BUILD · LEARN · SHIP",
        "CODE WITH CURIOSITY",
        "SMALL COMMITS · BIG PROGRESS",
        "KEEP BUILDING",
        "LEARN · BUILD · ITERATE",
        "MAKE SOMETHING USEFUL",
    ]
    msg = messages[now.timetuple().tm_yday % len(messages)]
    date = now.strftime("%d %b %Y").upper()
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 255" width="320" height="255">
<rect width="320" height="255" rx="16" fill="%s" stroke="%s"/>
<circle cx="28" cy="30" r="7" fill="%s"/>
<text x="45" y="34" fill="%s" font-family="ui-monospace,monospace" font-size="10" font-weight="700">DAILY DEVELOPER SIGNAL</text>
<text x="24" y="85" fill="%s" font-family="ui-sans-serif,system-ui" font-size="17" font-weight="800">%s</text>
<text x="24" y="111" fill="%s" font-family="ui-sans-serif,system-ui" font-size="17" font-weight="800">%s</text>
<text x="24" y="157" fill="%s" font-family="ui-sans-serif,system-ui" font-size="11">A small prompt, refreshed daily.</text>
<text x="24" y="193" fill="%s" font-family="ui-monospace,monospace" font-size="11">%s</text>
<text x="24" y="214" fill="%s" font-family="ui-monospace,monospace" font-size="9">ASIA/KOLKATA</text>
</svg>""" % (
        BG, GRID, ACCENT, MUTED, TEXT,
        escape(msg.split(" · ")[0]), ACCENT,
        escape(" · ".join(msg.split(" · ")[1:])),
        MUTED, TEXT, date, MUTED
    )


stats = collect()
(OUT / "github-stats.svg").write_text(stats_svg(stats), encoding="utf-8")
(OUT / "daily-signal.svg").write_text(daily_svg(), encoding="utf-8")
print("Generated dashboard assets", stats)
