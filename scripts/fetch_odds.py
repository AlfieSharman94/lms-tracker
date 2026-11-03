"""Fetch Premier League 1X2 prices from UK bookmakers via The Odds API and write odds.json.

Run by .github/workflows/odds.yml. Needs the ODDS_API_KEY repository secret.
Each run costs 1 credit (1 market x 1 region). The free plan gives 500 a month.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

key = os.environ.get("ODDS_API_KEY")
if not key:
    sys.exit("ODDS_API_KEY is not set")

url = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds?" + urllib.parse.urlencode(
    {"apiKey": key, "regions": "uk", "markets": "h2h", "oddsFormat": "decimal"}
)
with urllib.request.urlopen(url, timeout=30) as r:
    data = json.load(r)
    remaining = r.headers.get("x-requests-remaining")

events = []
for e in data:
    home, away = e["home_team"], e["away_team"]
    books = []
    for b in e.get("bookmakers", []):
        m = next((m for m in b.get("markets", []) if m["key"] == "h2h"), None)
        if not m:
            continue
        p = {o["name"]: o["price"] for o in m["outcomes"]}
        if home in p and away in p and "Draw" in p:
            books.append({"name": b["title"], "home": p[home], "draw": p["Draw"], "away": p[away]})
    events.append({
        "home": home,
        "away": away,
        "commence": e["commence_time"],
        "bookmakers": sorted(books, key=lambda x: x["name"].lower()),
    })

events.sort(key=lambda x: x["commence"])
out = {
    "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "source": "The Odds API (UK bookmakers)",
    "events": events,
}
with open("odds.json", "w") as f:
    json.dump(out, f, indent=1)
print(f"{len(events)} fixtures written, {remaining} credits left this month")
