"""
Part 1: Extract every pass that led to a shot (a "key pass") in the 2015/16
Premier League, La Liga, Serie A and Ligue 1 (StatsBomb open data).

Each key pass is linked to the shot it created through the shot's key_pass_id,
so we know the xG of the chance and whether it was scored.

Expected assists (xA) here = xG of the shot a pass led to.
Penalty shots have no key pass, so they are never counted.

Output: results/key_passes_2015_16.csv (one row per key pass)
        printed leaders: assists, chances created and xA
"""

import concurrent.futures as cf
import json
import os
import time
import urllib.request

import pandas as pd

BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
LEAGUES = {"Premier League": (2, 27), "La Liga": (11, 27),
           "Serie A": (12, 27), "Ligue 1": (7, 27)}
OUT = "results/key_passes_2015_16.csv"
SET_PIECES = {"Corner", "Free Kick", "Throw-in", "Kick Off", "Goal Kick"}


def get_json(url, retries=6):
    """Download JSON, waiting and retrying if GitHub rate-limits (HTTP 429)."""
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt * 2)


def match_key_passes(league, m):
    events = get_json(f"{BASE}/events/{m['match_id']}.json")
    passes = {e["id"]: e for e in events if e["type"]["name"] == "Pass"}
    rows = []
    for e in events:
        if e["type"]["name"] != "Shot" or "key_pass_id" not in e["shot"]:
            continue
        p = passes.get(e["shot"]["key_pass_id"])
        if p is None:
            continue
        pdata = p["pass"]
        ptype = pdata.get("type", {}).get("name")  # Corner, Free Kick, ... or None
        rows.append({
            "league": league,
            "match_id": m["match_id"],
            "team": p["team"]["name"],
            "player": p["player"]["name"],
            "player_id": p["player"]["id"],
            "x": p["location"][0], "y": p["location"][1],
            "end_x": pdata["end_location"][0], "end_y": pdata["end_location"][1],
            "pass_type": ptype or "Open play",
            "set_piece": ptype in SET_PIECES,
            "cross": pdata.get("cross", False),
            "through_ball": pdata.get("technique", {}).get("name") == "Through Ball",
            "cut_back": pdata.get("cut_back", False),
            "height": pdata.get("height", {}).get("name"),
            "shooter": e["player"]["name"],
            "xa": e["shot"].get("statsbomb_xg", 0),
            "goal": e["shot"]["outcome"]["name"] == "Goal",
        })
    return rows


def main():
    os.makedirs("results", exist_ok=True)
    jobs = [(lg, m) for lg, (cid, sid) in LEAGUES.items()
            for m in get_json(f"{BASE}/matches/{cid}/{sid}.json")]
    print(f"Matches: {len(jobs)}")
    rows, failed = [], []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(match_key_passes, lg, m): m["match_id"] for lg, m in jobs}
        for f in cf.as_completed(futs):
            try:
                rows.extend(f.result())
            except Exception as err:
                failed.append((futs[f], str(err)))
    if failed:
        print("Failed matches:", failed)

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    print(f"Saved {len(df)} key passes to {OUT}\n")

    df["op"] = ~df.set_piece
    lead = (df.groupby(["player", "team"])
              .agg(league=("league", "first"),
                   assists=("goal", "sum"),
                   chances=("goal", "size"),
                   xa=("xa", "sum"),
                   op_chances=("op", "sum"),
                   op_xa=("xa", lambda s: s[df.loc[s.index, "op"]].sum()))
              .reset_index())
    lead["assists_minus_xa"] = lead.assists - lead.xa
    cols = ["player", "team", "league", "assists", "chances", "xa", "op_chances", "op_xa"]
    pd.set_option("display.width", 200)
    for title, key in [("Most assists", "assists"), ("Most expected assists (xA)", "xa"),
                       ("Most chances created", "chances")]:
        print(title)
        print(lead.sort_values([key, "xa"], ascending=False).head(10)[cols]
              .round(1).to_string(index=False))
        print()
    print("Top assist provider in each league")
    for lg in LEAGUES:
        t = lead[lead.league == lg].sort_values(["assists", "xa"], ascending=False).head(3)
        print(f"  {lg}: " + "; ".join(f"{r.player} ({r.team}) {r.assists} ast, {r.xa:.1f} xA"
                                      for r in t.itertuples()))


if __name__ == "__main__":
    main()
