"""
Part 3: Chance maps for four creators, one per league (2015/16)

Every pass that led to a shot is drawn as a line from where the pass started to
where it ended. Passes that led to a goal (assists) are highlighted.

Input:  results/key_passes_2015_16.csv (part 1), results/creators_per90.csv (part 2)
Output: figures/chance_maps_creators.png
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from matplotlib.lines import Line2D
from mplsoccer import VerticalPitch

CREATORS = {  # StatsBomb name: (short name, team, league)
    "Mesut Özil": ("Özil", "Arsenal", "Premier League"),
    "Neymar da Silva Santos Junior": ("Neymar", "Barcelona", "La Liga"),
    "Marek Hamšík": ("Hamšík", "Napoli", "Serie A"),
    "Ángel Fabián Di María Hernández": ("Di María", "PSG", "Ligue 1"),
}
X_FROM = 34  # pitch shown from 34 yards (just inside the defending half)

SURFACE, INK, INK_2, INK_3 = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984"
BLUE, GREY = "#2a78d6", "#b9b8b2"


def main():
    os.makedirs("figures", exist_ok=True)
    kp = pd.read_csv("results/key_passes_2015_16.csv")
    p90 = pd.read_csv("results/creators_per90.csv").set_index("player")

    for f in font_manager.findSystemFonts():
        if "Inter" in f:
            font_manager.fontManager.addfont(f)
    plt.rcParams.update({"font.family": "Inter", "text.color": INK,
                         "figure.facecolor": SURFACE})

    pitch = VerticalPitch(pitch_type="statsbomb", half=True, pad_bottom=60 - X_FROM,
                          line_color="#c9c8c2", linewidth=1, pitch_color=SURFACE,
                          goal_type="box")
    fig = plt.figure(figsize=(11, 15.5))
    W_AX, H_AX = 0.43, 0.30
    spots = [(0.05, 0.575), (0.52, 0.575), (0.05, 0.13), (0.52, 0.13)]

    for (left, bottom), (player, (short, team, league)) in zip(spots, CREATORS.items()):
        ax = fig.add_axes([left, bottom, W_AX, H_AX])
        pitch.draw(ax=ax)
        ax.set_anchor("S")
        d = kp[kp.player == player]
        chance, assist = d[~d.goal], d[d.goal]
        pitch.lines(chance.x, chance.y, chance.end_x, chance.end_y, ax=ax, color=GREY,
                    lw=0.9, alpha=0.55, zorder=2)
        pitch.lines(assist.x, assist.y, assist.end_x, assist.end_y, ax=ax, color=BLUE,
                    lw=1.8, alpha=0.9, zorder=3)
        pitch.scatter(assist.end_x, assist.end_y, s=28, ax=ax, color=BLUE,
                      edgecolor=SURFACE, linewidth=0.8, zorder=4)

        r = p90.loc[player]
        top = bottom + H_AX
        fig.text(left, top + 0.03, short, fontsize=16, fontweight="bold")
        fig.text(left, top + 0.014, f"{team} · {league}", fontsize=10, color=INK_3)
        fig.text(left, bottom - 0.01, f"{int(r.assists)} assists from {r.xa:.1f} xA",
                 fontsize=12.5, fontweight="semibold", va="top")
        fig.text(left, bottom - 0.032,
                 f"{int(r.chances)} chances created · {r.minutes:,.0f} minutes",
                 fontsize=10, color=INK_2, va="top")
        fig.text(left + W_AX, bottom - 0.006, f"{r.xa_p90:.2f}", ha="right",
                 fontsize=21, fontweight="bold", color=BLUE, va="top")
        fig.text(left + W_AX, bottom - 0.036, "xA per 90", ha="right", fontsize=9,
                 color=INK_3, va="top")

    handles = [Line2D([], [], color=BLUE, lw=2, marker="o", markersize=5,
                      markevery=[1], label="Assist (pass to the shooter)"),
               Line2D([], [], color=GREY, lw=1.5, label="Pass that led to a shot")]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.04, 0.952),
               ncol=2, frameon=False, fontsize=10.5, labelcolor=INK_2,
               handlelength=2.2, columnspacing=2)
    fig.text(0.05, 0.988, "Who created the most in 2015/16?", fontsize=19,
             fontweight="bold", va="top")
    fig.text(0.05, 0.968, "Every pass that led to a shot, for the player with the most "
             "expected assists (xA) in each league. Attacking upwards.", fontsize=11, color=INK_2, va="top")
    fig.text(0.05, 0.03, "Data: StatsBomb open data, 2015/16 league matches. Includes set "
             "pieces (corners, free kicks). xA = xG of the shot a pass led to.",
             fontsize=8, color=INK_3)
    fig.text(0.05, 0.015, "Assists here are passes directly before a goal in StatsBomb data "
             "and may differ from official counts. Ligue 1 open data is missing 3 matches.",
             fontsize=8, color=INK_3)
    fig.savefig("figures/chance_maps_creators.png", dpi=200)
    print("Saved figures/chance_maps_creators.png")


if __name__ == "__main__":
    main()
