"""Regenerates the demand figures and table used in report Section 4.1 and the fit-gain figure in Section 4.4.

Run from step5_matching/:  python report_figures.py

Reads
  ../step1_data/job_cleaned.csv
  ../step4_semantic/results/hybrid_job_skills/job_skills_hybrid_long.csv   (rows with source == "exact" are Baseline++)
  outputs/supplementary/A_exact_vs_hybrid.csv, B_leave_one_skill_out.csv, G_false_match_only.csv
Writes
  outputs/supplementary/H_demand_exact.csv     per-career share of advertisements naming each skill (Baseline++ exact hits)
  figures/fig3_demand_exact.png                report Figure 3 (15 most demanded skills; skills found per advertisement)
  figures/fig9_fit_gain.png                    report Figure 9 (exact vs hybrid fit, with like-for-like gains)

Demand here uses the same Baseline++ exact hits that feed the exact career fit, so Section 4.1 and Sections 4.3 to 4.4
describe one extraction. Exact fit values come from Part 5 (A_exact_vs_hybrid.csv) so every gain compares like with like.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BLUE = "#2a78d6"
SUP = HERE / "outputs" / "supplementary"
(HERE / "figures").mkdir(exist_ok=True)

jobs = pd.read_csv(ROOT / "step1_data" / "job_cleaned.csv")
hits = pd.read_csv(ROOT / "step4_semantic" / "results" / "hybrid_job_skills" / "job_skills_hybrid_long.csv")
exact = hits[hits["source"].eq("exact")].drop_duplicates(["job_id", "canonical_skill"])
n_career = jobs["career_category"].value_counts()

# ---- demand table (Section 4.1, Table 4) -----------------------------------------------------------------
overall = exact.groupby("canonical_skill")["job_id"].nunique().div(len(jobs)).mul(100).sort_values(ascending=False)
per_career = (exact.groupby(["career_category", "canonical_skill"])["job_id"].nunique().reset_index(name="ads")
              .assign(n_ads=lambda d: d["career_category"].map(n_career))
              .assign(pct_of_ads=lambda d: 100 * d["ads"] / d["n_ads"])
              .sort_values(["career_category", "pct_of_ads"], ascending=[True, False]))
per_career.round(1).to_csv(SUP / "H_demand_exact.csv", index=False)
skills_per_ad = (exact.groupby("career_category").size() / n_career).sort_values(ascending=False)
print("Overall top 6:", overall.head(6).round(1).to_dict())
print("Skills per ad:", skills_per_ad.round(2).to_dict())
for c in ("Data Scientist", "ML Engineer"):
    print(c, per_career[per_career.career_category == c].head(6)[["canonical_skill", "pct_of_ads"]].round(1).values.tolist())

# ---- Figure 3 -------------------------------------------------------------------------------------------
plt.rcParams.update({"font.size": 6.5})
fig, ax = plt.subplots(1, 2, figsize=(6.83, 2.57), gridspec_kw={"width_ratios": [1.15, 1]})
top = overall.head(15)[::-1]
ax[0].barh(top.index, top.values, color=BLUE, height=0.65)
for y, v in enumerate(top.values):
    ax[0].text(v + 1, y, f"{v:.0f}%", va="center", fontsize=6)
ax[0].set_title("15 most demanded skills (% of ads)", loc="left", fontsize=7)
sp = skills_per_ad[::-1]
ax[1].barh(sp.index, sp.values, color=BLUE, height=0.65)
for y, v in enumerate(sp.values):
    ax[1].text(v + 0.2, y, f"{v:.1f}", va="center", fontsize=6)
ax[1].set_title("Average skills found per ad, by career", loc="left", fontsize=7)
ax[1].set_xlim(0, 15.5)
for a in ax:
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(HERE / "figures" / "fig3_demand_exact.png", dpi=300)
plt.close(fig)

# ---- Figure 9 -------------------------------------------------------------------------------------------
a = pd.read_csv(SUP / "A_exact_vs_hybrid.csv").set_index("career")
b = pd.read_csv(SUP / "B_leave_one_skill_out.csv")
b = b[b["dropped_skill"].eq("AI Agents")].set_index("career")
g = pd.read_csv(SUP / "G_false_match_only.csv").set_index("career")
order = ["Data Scientist", "Data Engineer", "Data Analyst", "ML Engineer", "AI Engineer"]
plt.rcParams.update({"font.size": 7})
fig, ax = plt.subplots(figsize=(5.65, 3.22))
for i, c in enumerate(order):
    y = len(order) - 1 - i
    ex, hy, wo = a.loc[c, "exact"], a.loc[c, "hybrid"], b.loc[c, "without_skill"]
    ax.plot([ex, hy], [y, y], color="#b6c1d6", lw=2.2, zorder=1)
    ax.scatter([ex], [y], s=38, color="#27487d", zorder=3)
    ax.scatter([hy], [y], s=38, color="#1f9e89", zorder=3)
    ax.scatter([wo], [y], s=48, marker="D", facecolor="white", edgecolor="#d98324", lw=1.4, zorder=4)
    ax.text(ex - 0.9, y + 0.2, f"{ex:.1f}", color="#27487d", ha="right", fontsize=6.5)
    ax.text(hy + 0.9, y + 0.2, f"{hy:.1f}", color="#14705f", ha="left", fontsize=6.5)
    ax.text(wo, y - 0.5, f"{wo:.1f}", color="#8a4b0f", ha="center", va="center", fontsize=6.5)
    ax.text(1.08, y, f"+{hy - ex:.1f}", transform=ax.get_yaxis_transform(), ha="center", va="center", fontweight="bold", color="#14213d")
    ax.text(1.27, y, f"+{wo - ex:.1f}", transform=ax.get_yaxis_transform(), ha="center", va="center", fontweight="bold", color="#8a4b0f")
fm = g.loc["AI Engineer", "false_match_removed"]
ax.scatter([fm], [0], s=34, marker="^", color="#6b6b6b", zorder=5)
ax.annotate(f"only the audit-wrong match\nremoved: {fm:.1f}", xy=(fm, 0), xytext=(fm + 6, -0.62), fontsize=6.5, color="#444",
            arrowprops=dict(arrowstyle="-", color="#888", lw=0.7))
ax.text(1.08, len(order) - 0.35, "Gain from\nsemantic\n(points)", transform=ax.get_yaxis_transform(), ha="center", va="bottom", fontsize=6, color="#666")
ax.text(1.27, len(order) - 0.35, "Gain with\nAI Agents\nremoved", transform=ax.get_yaxis_transform(), ha="center", va="bottom", fontsize=6, color="#666")
ax.set_yticks(range(len(order)))
ax.set_yticklabels(order[::-1])
ax.set_ylim(-1.0, len(order) + 0.35)
ax.set_xlim(26, 74)
ax.set_xlabel("Career fit (% of top-30 demand-weighted skills covered; exact fit from Part 5)")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
from matplotlib.lines import Line2D
leg = [Line2D([], [], marker="o", ls="", color="#27487d", label="Exact matching only"),
       Line2D([], [], marker="o", ls="", color="#1f9e89", label="With semantic additions"),
       Line2D([], [], marker="^", ls="", color="#6b6b6b", label="Only the audit-wrong match removed"),
       Line2D([], [], marker="D", ls="", markerfacecolor="white", markeredgecolor="#d98324", label="AI Agents removed entirely (conservative bound)")]
fig.legend(handles=leg, loc="lower center", ncol=2, frameon=False, fontsize=6.3, bbox_to_anchor=(0.45, 0.0))
fig.subplots_adjust(left=0.2, right=0.78, top=0.97, bottom=0.27)
fig.savefig(HERE / "figures" / "fig9_fit_gain.png", dpi=300)
plt.close(fig)
print("figures written")
