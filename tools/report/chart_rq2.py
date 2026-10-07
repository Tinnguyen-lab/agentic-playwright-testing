"""Biểu đồ RQ2: tỉ lệ đạt lần đầu theo website, baseline vs DOM-aware. python chart_rq2.py <results.json>"""
import json
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from build_report import SITE_NAME

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e7e6e2"
C_NONE, C_ARIA = "#2a78d6", "#eb6834"  # categorical slot 1, 2 (đã validate)

res = json.load(open(sys.argv[1], encoding="utf-8"))
none, aria = res["conditions"]["none"], res["conditions"]["aria"]
sites = sorted(none["by_site"], key=lambda s: none["by_site"][s]["n"])  # site nhiều target ở trên
rows = [("Tổng", none["passed"], aria["passed"], none["n"])] + [
    (SITE_NAME[s], none["by_site"][s]["passed"], aria["by_site"][s]["passed"], none["by_site"][s]["n"]) for s in sites]
rows = rows[::-1]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
fig, ax = plt.subplots(figsize=(8, 4.6), facecolor=SURFACE)
ax.set_facecolor(SURFACE)
h = 0.36
for i, (name, pn, pa, n) in enumerate(rows):
    for off, val, color in ((h / 2 + 0.02, pn, C_NONE), (-h / 2 - 0.02, pa, C_ARIA)):
        ax.barh(i + off, val / n * 100, height=h, color=color, edgecolor=SURFACE, linewidth=1)
        ax.text(val / n * 100 + 1, i + off, f"{val}/{n}", va="center", fontsize=8, color=INK2)
ax.set_yticks(range(len(rows)), [r[0] for r in rows], color=INK)
for lbl in ax.get_yticklabels():
    if lbl.get_text() == "Tổng":
        lbl.set_fontweight("bold")
ax.set_xlim(0, 110)
ax.set_xticks(range(0, 101, 20), [f"{x}%" for x in range(0, 101, 20)], color=INK2)
ax.xaxis.grid(True, color=GRID, lw=0.8)
ax.set_axisbelow(True)
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_color(GRID)
ax.tick_params(length=0)
ax.set_xlabel("Tỉ lệ script đạt ngay lần chạy đầu", color=INK2)
ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=C_NONE), plt.Rectangle((0, 0), 1, 1, color=C_ARIA)],
          labels=["Baseline (chỉ test case)", "DOM-aware (+ aria snapshot)"], loc="lower center",
          bbox_to_anchor=(0.45, 1.0), ncol=2, frameon=False)
fig.tight_layout()
fig.savefig("fig_rq2_sites.png", dpi=200, facecolor=SURFACE)
print("ok")
