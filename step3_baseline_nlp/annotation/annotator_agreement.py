"""Three-rater agreement on 10 of the 30 gold advertisements, plus a check of the extractor against each rater.

Raters (same 216 ad-skill candidates, labels R / P / I / N):
  gold   LLM annotator 1   gold_annotations.py (key: annotation/human_annotation_key.csv)
  human  human annotator  human_merged.xlsx  (pass 1 = human_annotation_sheet_FILLED.xlsx, pass 2 = pass2_filled.xlsx)
  llm2    LLM annotator 2   llm_second_annotator_FILLED.xlsx (not independent of gold in the
                          sense of a different person: same model family, so its agreement with gold shows consistency, not validity)

Run from step3_baseline_nlp/:  python3 annotation/annotator_agreement.py
Writes annotator_agreement_results.csv, annotator_confusions.csv, extractor_vs_annotators.csv and figures/fig7_annotator_agreement.png.
Uncertainty: cluster bootstrap over the 10 advertisements (2000 resamples, seed 36118)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # step3 root on the path
import random, re
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 36118
key = pd.read_csv("annotation/human_annotation_key.csv")
def load(f, name):
    d = pd.read_excel(f, sheet_name="Labels"); d.columns = ["ad_no", "job_title", "skill", name]
    d[name] = d[name].astype(str).str.strip().str.upper(); return d[["ad_no", "skill", name]]
m = (key.rename(columns={"gold_label": "gold"})
        .merge(load("annotation/human_merged.xlsx", "human"), on=["ad_no", "skill"])
        .merge(load("annotation/llm_second_annotator_FILLED.xlsx", "llm2"), on=["ad_no", "skill"]))
assert len(m) == len(key) == 216 and all(set(m[c]) <= set("RPIN") for c in ("gold", "human", "llm2"))
ads = pd.read_excel("annotation/human_annotation_sheet.xlsx", sheet_name="Ads").set_index("ad_no").advertisement_text.to_dict()
m["literal"] = [bool(re.search(r"(?<![A-Za-z0-9])" + re.escape(s.lower()) + r"(?![A-Za-z0-9])", ads[n].lower()))
                for n, s in zip(m.ad_no, m.skill)]

def kappa(a, b):
    a = np.asarray(a); b = np.asarray(b); po = (a == b).mean()
    pe = sum((a == c).mean() * (b == c).mean() for c in set(a) | set(b))
    return (po - pe) / (1 - pe) if pe < 1 else 1.0
def ac1(a, b):  # Gwet's AC1 for two binary raters: robust to the kappa paradox at extreme prevalence
    a = np.asarray(a, bool); b = np.asarray(b, bool); po = (a == b).mean(); pi = (a.mean() + b.mean()) / 2
    pe = 2 * pi * (1 - pi); return (po - pe) / (1 - pe) if pe < 1 else 1.0

MEASURES = {  # name: (transform applied to both raters, statistic)
    "Named and demanded (R/P vs I/N)": (lambda s: s.isin(["R", "P"]), kappa),
    "Required (R vs rest)":            (lambda s: s == "R", kappa),
    "Implicit (I vs rest)":            (lambda s: s == "I", kappa),
    "Any demand (R/P/I vs N)":         (lambda s: s != "N", kappa),
    "Four classes R/P/I/N":            (lambda s: s, kappa),
}
PAIRS = [("gold", "human", "LLM-1 (gold) vs human"), ("gold", "llm2", "LLM-1 (gold) vs LLM-2"), ("human", "llm2", "Human vs LLM-2")]

def boot(fn, d, n=2000):
    rng = random.Random(SEED); ids = sorted(d.ad_no.unique()); g = {a: d[d.ad_no == a] for a in ids}; out = []
    for _ in range(n):
        s = pd.concat([g[rng.choice(ids)] for _ in ids])
        try: out.append(fn(s))
        except Exception: pass
    return np.nanpercentile(out, [2.5, 97.5])

rows = []
for x, y, label in PAIRS:
    for mname, (tf, stat) in MEASURES.items():
        fn = lambda d, x=x, y=y, tf=tf, stat=stat: stat(tf(d[x]), tf(d[y]))
        lo, hi = boot(fn, m)
        agree = (tf(m[x]) == tf(m[y])).mean()
        row = dict(pair=label, measure=mname, kappa=fn(m), ci_low=lo, ci_high=hi, raw_agreement=agree)
        if mname.startswith(("Named", "Required", "Implicit", "Any")):
            row["gwet_ac1"] = ac1(tf(m[x]), tf(m[y]))
        rows.append(row)
res = pd.DataFrame(rows); res.round(3).to_csv("annotation/annotator_agreement_results.csv", index=False)
print(res.round(2).to_string(index=False))

conf = []
for x, y, label in PAIRS:
    ct = pd.crosstab(m[x], m[y]).reindex(index=list("RPIN"), columns=list("RPIN"), fill_value=0)
    for a in "RPIN":
        for b in "RPIN": conf.append(dict(pair=label, row_rater=x, col_rater=y, row_label=a, col_label=b, n=int(ct.loc[a, b])))
pd.DataFrame(conf).to_csv("annotation/annotator_confusions.csv", index=False)

print("\nLabel use (n of 216):"); print(pd.DataFrame({c: m[c].value_counts() for c in ("gold", "human", "llm2")}).reindex(list("RPIN")).fillna(0).astype(int).to_string())
print("\nPer-ad raw 4-class agreement:"); print(m.groupby("ad_no").apply(lambda d: pd.Series({f"{x}-{y}": (d[x] == d[y]).mean() for x, y, _ in PAIRS})).round(2).to_string())

# Where the human and LLM labels split: is the skill literally in the advertisement?
d = m[(m.gold == "R") & (m.human != "R")]
print(f"\nGold R but human not R: {len(d)} rows; skill named verbatim in the ad in {int(d.literal.sum())}; LLM-2 also R in {(d.llm2 == 'R').sum()}")
d = m[(m.human == "I") & (m.gold == "N") & (m.llm2 == "N")]
print(f"Human I but both LLM raters N: {len(d)} rows; skill named verbatim in the ad in {int(d.literal.sum())} (an 'I' label means the skill is NOT named)")
print("Human P labels:", int((m.human == 'P').sum()), "| human R-labelled skills:", int((m.human == 'R').sum()))

# Extractor (Baseline++ with reviewed aliases) scored against each rater on the same candidate pool: positive = R or P
from skill_extractor_v2 import RequirementAwareExtractor
jobs = pd.read_csv("job_cleaned.csv", encoding="utf-8-sig")
ext = RequirementAwareExtractor(extra_aliases_path="extra_aliases_reviewed.csv")
m["pred"] = False
for n, g in m.groupby("ad_no"):
    hits = set(ext.extract_skills(ads[n])); m.loc[g.index, "pred"] = g.skill.isin(hits).values
def prf(d, r):
    pos = d[r].isin(["R", "P"]); tp = (d.pred & pos).sum(); fp = (d.pred & ~pos).sum(); fn = (~d.pred & pos).sum()
    p = tp / (tp + fp) if tp + fp else 0; rc = tp / (tp + fn) if tp + fn else 0
    return dict(TP=int(tp), FP=int(fp), FN=int(fn), precision=p, recall=rc, F1=2 * p * rc / (p + rc) if p + rc else 0)
ev = []
for r, lab in [("gold", "LLM-1 (gold)"), ("llm2", "LLM-2"), ("human", "Human")]:
    s = prf(m, r); f1 = lambda d, r=r: prf(d, r)["F1"]; lo, hi = boot(f1, m, 1000)
    ev.append(dict(reference=lab, **s, F1_ci_low=lo, F1_ci_high=hi))
ev = pd.DataFrame(ev); ev.round(3).to_csv("annotation/extractor_vs_annotators.csv", index=False)
print("\nExtractor on the 216-candidate pool (positive = R or P):"); print(ev.round(3).to_string(index=False))

# Figure: kappa with CI for three pairs, and the human-vs-gold confusion matrix
plt.rcParams.update({"font.size": 9})
fig, ax = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1.5, 1]})
meas = [k for k in MEASURES]; cols = ["#1f3864", "#7f9fcf", "#c0504d"]; h = 0.26
for i, (_, _, label) in enumerate(PAIRS):
    d = res[res.pair == label].set_index("measure").loc[meas]
    y = np.arange(len(meas)) + (i - 1) * h
    ax[0].barh(y, d.kappa, height=h, color=cols[i], label=label)
    ax[0].errorbar(d.kappa, y, xerr=[d.kappa - d.ci_low, d.ci_high - d.kappa], fmt="none", ecolor="black", lw=.8, capsize=2)
ax[0].set_yticks(range(len(meas))); ax[0].set_yticklabels(meas); ax[0].invert_yaxis(); ax[0].axvline(0, color="grey", lw=.6)
ax[0].set_xlabel("Cohen's kappa (95% CI, bootstrap over 10 ads)"); ax[0].legend(loc="upper center", bbox_to_anchor=(0.45, -0.16), ncol=3, frameon=False); ax[0].set_xlim(-0.2, 1.05)
ax[0].set_title("Agreement between annotators")
ct = pd.crosstab(m.gold, m.human).reindex(index=list("RPIN"), columns=list("RPIN"), fill_value=0)
ax[1].imshow(ct.values, cmap="Blues")
for i in range(4):
    for j in range(4): ax[1].text(j, i, ct.values[i, j], ha="center", va="center", color="white" if ct.values[i, j] > 60 else "black")
ax[1].set_xticks(range(4)); ax[1].set_xticklabels(list("RPIN")); ax[1].set_yticks(range(4)); ax[1].set_yticklabels(list("RPIN"))
ax[1].set_xlabel("Human label"); ax[1].set_ylabel("LLM-1 (gold) label"); ax[1].set_title("Gold vs human (216 labels)")
fig.tight_layout(); fig.savefig("figures/fig7_annotator_agreement.png", dpi=300); print("figure saved")
