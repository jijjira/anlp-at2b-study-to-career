"""Innovation analyses on the full 688-job corpus + 30-job gold set (all reproducible)."""
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from skill_extractor import SkillExtractor
from skill_extractor_v2 import RequirementAwareExtractor, REQUIRED, DUTY, PREFERRED, UNLABELLED, COMPANY, DEFAULT_WEIGHTS
from gold_annotations import GOLD
from evaluate import jobs, EXT_UNIVERSE, ROWS

V1 = SkillExtractor()
V2 = RequirementAwareExtractor(extra_aliases_path="extra_aliases_reviewed.csv", expand_morphology=True)

def corpus_tables():
    strengths = [V2.skill_strengths(t) for t in jobs.job_description]
    raw = [set(V1.extract_skills(t)) for t in jobs.job_description]
    return strengths, raw

def profiles(strengths, raw, weights=DEFAULT_WEIGHTS):
    cats = jobs.career_category.values; rows = []
    for c in sorted(set(cats)):
        idx = np.where(cats == c)[0]; n = len(idx)
        sk = set().union(*[strengths[i].keys() for i in idx]) | set().union(*[raw[i] for i in idx])
        for s in sk:
            rf = sum(s in raw[i] for i in idx) / n
            dw = sum(weights.get(strengths[i].get(s, COMPANY), 0) for i in idx) / n
            rq = sum(strengths[i].get(s) in (REQUIRED, DUTY) for i in idx) / n
            rows.append((c, s, rf, dw, rq))
    return pd.DataFrame(rows, columns=["career", "skill", "raw_freq", "demand_weight", "core_share"])

def tag_accuracy(strengths):
    rows = []
    for r in ROWS:
        for s, st in strengths[r].items():
            if s in GOLD[r]["R"] or s in GOLD[r]["P"]:
                gold = "P" if s in GOLD[r]["P"] and s not in GOLD[r]["R"] else "R"
                pred = "P" if st == PREFERRED else "R"
                rows.append((r, s, gold, pred, st))
    return pd.DataFrame(rows, columns=["row", "skill", "gold", "pred", "strength"])

if __name__ == "__main__":
    pd.set_option("display.width", 200)
    S, RAW = corpus_tables()
    P = profiles(S, RAW)
    print("n profile rows", len(P))
    # rank change
    for c, g in P.groupby("career"):
        rho = spearmanr(g.raw_freq, g.demand_weight)[0]
        top_raw = set(g.nlargest(15, "raw_freq").skill); top_dw = set(g.nlargest(15, "demand_weight").skill)
        print(c, "spearman", round(rho, 3), "top15 overlap", len(top_raw & top_dw), "| dropped:", sorted(top_raw - top_dw), "| entered:", sorted(top_dw - top_raw))
    # strength distribution
    allst = pd.Series([v for d in S for v in d.values()]).value_counts(); print(allst, allst / allst.sum())
    # weight sensitivity
    alts = {"default": DEFAULT_WEIGHTS, "strict": {REQUIRED:1, DUTY:.5, PREFERRED:.25, UNLABELLED:.25, COMPANY:0},
            "flat": {REQUIRED:1, DUTY:1, PREFERRED:1, UNLABELLED:1, COMPANY:0}, "pref-heavy": {REQUIRED:1, DUTY:.9, PREFERRED:.8, UNLABELLED:.8, COMPANY:0}}
    base = profiles(S, RAW, alts["default"])
    for k, w in alts.items():
        p = profiles(S, RAW, w); m = base.merge(p, on=["career", "skill"])
        rs = [spearmanr(g.demand_weight_x, g.demand_weight_y)[0] for _, g in m.groupby("career")]
        ov = np.mean([len(set(g.nlargest(15, "demand_weight_x").skill) & set(g.nlargest(15, "demand_weight_y").skill)) for _, g in m.groupby("career")])
        print(k, "mean spearman", round(np.mean(rs), 3), "mean top15 overlap", ov)
    T = tag_accuracy(S); print(len(T), (T.gold == T.pred).mean()); print(pd.crosstab(T.gold, T.pred))
    # gold tiers
    tot = {k: sum(len(GOLD[r][k]) for r in ROWS) for k in "R P I OTHER".split()}; print(tot)
    # errors S5
    for r in ROWS:
        pred = set(V2.extract_skills(jobs.job_description[r])) & EXT_UNIVERSE; gold = (GOLD[r]["R"] | GOLD[r]["P"]) & EXT_UNIVERSE
        if pred - gold or gold - pred: print(r, jobs.career_category[r], "FP", sorted(pred - gold), "FN", sorted(gold - pred))
