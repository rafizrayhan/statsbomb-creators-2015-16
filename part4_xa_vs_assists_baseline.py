"""
Part 4: Where do the four creators sit among all players?

Every player with at least 900 minutes and a key pass in 2015/16
(Premier League, La Liga, Serie A, Ligue 1): expected assists per 90 against
assists per 90. Above the line = more assists than the chances were worth
(helped by finishers); below = fewer (let down by finishers).

Input:  results/creators_per90.csv (from part2_minutes_per90.py)
Output: printed ranks, figures/xa_vs_assists_baseline.png
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

CREATORS = {"Mesut Özil": "Özil", "Neymar da Silva Santos Junior": "Neymar",
            "Marek Hamšík": "Hamšík", "Ángel Fabián Di María Hernández": "Di María"}
OTHERS = {"Lionel Andrés Messi Cuccittini": "Messi", "Kevin De Bruyne": "De Bruyne",
          "James David Rodríguez Rubio": "James"}

SURFACE, INK, INK_2, INK_3 = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
BLUE, GREY, GRID = "#2a78d6", "#c9c8c2", "#e6e5e1"


def report(d):
    n = len(d)
    d = d.assign(xa_rank=d.xa_p90.rank(ascending=False, method="min").astype(int),
                 ast_rank=d.assists_p90.rank(ascending=False, method="min").astype(int))
    print(f"Players with at least 900 minutes and a key pass: {n}")
    print(f"Median xA per 90: {d.xa_p90.median():.2f}   "
          f"Median assists per 90: {d.assists_p90.median():.2f}\n")
    show = d[d.player.isin(CREATORS) | d.player.isin(OTHERS)].copy()
    show["name"] = show.player.map({**CREATORS, **OTHERS})
    show["xA/90 rank"] = show.xa_rank.astype(str) + f" of {n}"
    show["assists/90 rank"] = show.ast_rank.astype(str) + f" of {n}"
    print(show.sort_values("xa_p90", ascending=False)[
        ["name", "minutes", "xa_p90", "assists_p90", "xA/90 rank", "assists/90 rank"]]
        .round(2).to_string(index=False))


def chart(d):
    for f in font_manager.findSystemFonts():
        if "Inter" in f:
            font_manager.fontManager.addfont(f)
    plt.rcParams.update({"font.family": "Inter", "text.color": INK,
                         "figure.facecolor": SURFACE, "axes.facecolor": SURFACE})
    fig, ax = plt.subplots(figsize=(10, 9))
    lim = 0.82
    xs = np.array([0, lim])
    ax.plot(xs, xs, color=INK_3, lw=1.2, ls="--", zorder=1)
    ax.text(0.70, 0.672, "assists = xA", rotation=45, rotation_mode="anchor",
            fontsize=9.5, color=INK_3, ha="left", va="top")

    rest = d[~d.player.isin(CREATORS) & ~d.player.isin(OTHERS)]
    ax.scatter(rest.xa_p90, rest.assists_p90, s=22, color=GREY, edgecolor=SURFACE,
               linewidth=0.5, alpha=0.8, zorder=2)
    oth = d[d.player.isin(OTHERS)]
    ax.scatter(oth.xa_p90, oth.assists_p90, s=50, color=INK_3, edgecolor=SURFACE,
               linewidth=1, zorder=3)
    top = d[d.player.isin(CREATORS)]
    ax.scatter(top.xa_p90, top.assists_p90, s=120, color=BLUE, edgecolor=SURFACE,
               linewidth=1.6, zorder=4)

    place = {"Di María": (-0.012, 0, "right"), "Özil": (0.012, 0, "left"),
             "Neymar": (0.012, -0.012, "left"), "Hamšík": (-0.012, 0.012, "right"),
             "Messi": (-0.012, 0, "right"), "De Bruyne": (0.012, -0.01, "left"),
             "James": (0.012, 0.012, "left")}
    for names, style in [(CREATORS, dict(fontsize=12, fontweight="bold", color=BLUE)),
                         (OTHERS, dict(fontsize=10, color=INK_2))]:
        for _, r in d[d.player.isin(names)].iterrows():
            nm = names[r.player]
            dx, dy, ha = place[nm]
            ax.text(r.xa_p90 + dx, r.assists_p90 + dy, nm, ha=ha, va="center",
                    zorder=5, bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1),
                    **style)

    ax.text(0.03, 0.78, "More assists than the chances\nwere worth: helped by finishers",
            fontsize=9.5, color=INK_3, va="top")
    ax.text(0.79, 0.04, "Fewer assists than the chances\nwere worth: let down by finishers",
            fontsize=9.5, color=INK_3, ha="right", va="bottom")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_aspect("equal")
    ax.set_xlabel("Expected assists (xA) per 90: quality of chances created",
                  fontsize=11, color=INK_2)
    ax.set_ylabel("Assists per 90", fontsize=11, color=INK_2)
    ax.tick_params(length=0, labelsize=9, colors=INK_3)
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    for sp in ["left", "bottom"]:
        ax.spines[sp].set_color(GRID)
    ax.grid(color=GRID, lw=0.6)
    ax.set_axisbelow(True)

    fig.text(0.07, 0.975, "Di María created more per 90 minutes than anyone",
             fontsize=18, fontweight="bold", va="top")
    fig.text(0.07, 0.94, f"Every player with at least 900 minutes and one chance created "
             f"in the 2015/16 Premier League, La Liga,\nSerie A and Ligue 1 ({len(d)} "
             "players). Blue = the xA leader in each league.", fontsize=10.5, color=INK_2, va="top", linespacing=1.4)
    fig.text(0.07, 0.015, "Data: StatsBomb open data, 2015/16 league matches. xA = xG of "
             "the shot a pass led to. Assists may differ from official counts.",
             fontsize=8, color=INK_3)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.86, bottom=0.08)
    fig.savefig("figures/xa_vs_assists_baseline.png", dpi=200)
    print("\nSaved figures/xa_vs_assists_baseline.png")


if __name__ == "__main__":
    os.makedirs("figures", exist_ok=True)
    data = pd.read_csv("results/creators_per90.csv")
    report(data)
    chart(data)
