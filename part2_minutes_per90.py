"""
Part 2: Minutes played for every player, then creators per 90 minutes.

Minutes come from each match's events:
  - starters (Starting XI event) play from kick-off
  - substitutes play from the minute they come on
  - a player stops at the minute he is substituted or sent off
  - match length = time of the last event (so stoppage time counts)

Input:  results/key_passes_2015_16.csv (from part1_extract_key_passes.py)
Output: results/player_minutes_2015_16.csv
        results/creators_per90.csv
        printed per-90 leaders (players with at least 900 minutes)
"""

import concurrent.futures as cf
import json
import os
import time
import urllib.request
from collections import defaultdict

import pandas as pd

BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
LEAGUES = {"Premier League": (2, 27), "La Liga": (11, 27),
           "Serie A": (12, 27), "Ligue 1": (7, 27)}
MIN_MINUTES = 900
RED = {"Red Card", "Second Yellow"}


def get_json(url, retries=6):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt * 2)


def clock(e):
    """Match clock in minutes (StatsBomb minutes already run 45+ in the 2nd half)."""
    return e["minute"] + e["second"] / 60


def match_minutes(m):
    events = get_json(f"{BASE}/events/{m['match_id']}.json")
    end = max(clock(e) for e in events)
    on, off, info = {}, {}, {}
    for e in events:
        t = e["type"]["name"]
        if t == "Starting XI":
            for p in e["tactics"]["lineup"]:
                pid = p["player"]["id"]
                on[pid] = 0.0
                info[pid] = (p["player"]["name"], e["team"]["name"])
        elif t == "Substitution":
            out_id = e["player"]["id"]
            in_p = e["substitution"]["replacement"]
            off[out_id] = clock(e)
            on[in_p["id"]] = clock(e)
            info[in_p["id"]] = (in_p["name"], e["team"]["name"])
        else:
            card = (e.get("foul_committed", {}).get("card", {}).get("name")
                    or e.get("bad_behaviour", {}).get("card", {}).get("name"))
            if card in RED and "player" in e:
                off[e["player"]["id"]] = clock(e)
    return [{"player_id": pid, "player": info[pid][0], "team": info[pid][1],
             "minutes": max(off.get(pid, end) - start, 0)} for pid, start in on.items()]


def main():
    os.makedirs("results", exist_ok=True)
    jobs = [m for cid, sid in LEAGUES.values()
            for m in get_json(f"{BASE}/matches/{cid}/{sid}.json")]
    rows, failed = [], []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(match_minutes, m): m["match_id"] for m in jobs}
        for f in cf.as_completed(futs):
            try:
                rows.extend(f.result())
            except Exception as err:
                failed.append((futs[f], str(err)))
    if failed:
        print("Failed matches:", failed)

    mins = (pd.DataFrame(rows).groupby("player_id")
              .agg(player=("player", "first"), team=("team", "last"),
                   minutes=("minutes", "sum"), apps=("minutes", "size"))
              .reset_index())
    mins.to_csv("results/player_minutes_2015_16.csv", index=False)
    print(f"Players with minutes: {len(mins)}")
    check = ["Lionel Andrés Messi Cuccittini", "Mesut Özil", "Neymar da Silva Santos Junior",
             "Ángel Fabián Di María Hernández", "Marek Hamšík"]
    print("Sanity check (appearances, minutes):")
    print(mins[mins.player.isin(check)][["player", "apps", "minutes"]]
          .round(0).to_string(index=False), "\n")

    kp = pd.read_csv("results/key_passes_2015_16.csv")
    kp["op"] = ~kp.set_piece
    agg = (kp.groupby("player_id")
             .agg(league=("league", "first"), assists=("goal", "sum"),
                  chances=("goal", "size"), xa=("xa", "sum"),
                  op_chances=("op", "sum"),
                  op_xa=("xa", lambda s: s[kp.loc[s.index, "op"]].sum()))
             .reset_index())
    df = mins.merge(agg, on="player_id", how="inner")
    df = df[df.minutes >= MIN_MINUTES].copy()
    for c in ["assists", "chances", "xa", "op_chances", "op_xa"]:
        df[f"{c}_p90"] = df[c] / df.minutes * 90
    df.to_csv("results/creators_per90.csv", index=False)
    print(f"Players with at least {MIN_MINUTES} minutes and a key pass: {len(df)}\n")

    cols = ["player", "team", "minutes", "assists", "xa", "op_xa",
            "assists_p90", "xa_p90", "op_xa_p90", "chances_p90"]
    pd.set_option("display.width", 220)
    for title, key in [("Expected assists per 90", "xa_p90"),
                       ("Open-play expected assists per 90", "op_xa_p90"),
                       ("Assists per 90", "assists_p90"),
                       ("Chances created per 90", "chances_p90")]:
        print(title)
        print(df.sort_values(key, ascending=False).head(10)[cols]
              .round(2).to_string(index=False))
        print()


if __name__ == "__main__":
    main()
