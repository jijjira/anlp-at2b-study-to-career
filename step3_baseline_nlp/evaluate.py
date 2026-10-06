"""Held-out evaluation of the extraction variants against the hand-annotated sample."""
import json, random
import numpy as np, pandas as pd
from skill_extractor import SkillExtractor
from skill_extractor_v2 import RequirementAwareExtractor, REQUIRED, DUTY, PREFERRED
from gold_annotations import GOLD

jobs = pd.read_csv("job_cleaned.csv", encoding="utf-8-sig")
BASE = set(pd.read_csv("skills_dictionary.csv").canonical_skill)
EXTRA = "extra_aliases_reviewed.csv"
EXT_UNIVERSE = BASE | set(pd.read_csv(EXTRA).canonical_skill)
ROWS = sorted(GOLD)

def systems():
    v1 = SkillExtractor()
    return {
        "S0 Baseline (v1: all PhraseMatcher hits)": lambda t: v1.extract_skills(t),
        "S1 + URL/ambiguity guard only":  RequirementAwareExtractor(tag_context=False).extract_skills,
        "S2 + section-aware demand filter": RequirementAwareExtractor(guard_ambiguous=False).extract_skills,
        "S3 = S1 + S2 (context-aware)":   RequirementAwareExtractor().extract_skills,
        "S4 + reviewed extra aliases":    RequirementAwareExtractor(extra_aliases_path=EXTRA).extract_skills,
        "S5 + plural/singular variants":  RequirementAwareExtractor(extra_aliases_path=EXTRA, expand_morphology=True).extract_skills,
    }

def gold_sets(universe, drop=()):
    return {r: ((GOLD[r]["R"] | GOLD[r]["P"]) & universe) - set(drop) for r in ROWS}

def prf(pred, gold):
    tp = sum(len(pred[r] & gold[r]) for r in ROWS); fp = sum(len(pred[r] - gold[r]) for r in ROWS); fn = sum(len(gold[r] - pred[r]) for r in ROWS)
    p = tp / (tp + fp) if tp + fp else 0.0; rc = tp / (tp + fn) if tp + fn else 0.0
    return dict(TP=tp, FP=fp, FN=fn, P=p, R=rc, F1=2 * p * rc / (p + rc) if p + rc else 0.0)

def run(drop_ai=False):
    preds = {name: {r: set(fn(jobs.job_description[r])) for r in ROWS} for name, fn in systems().items()}
    out = {}
    for scope, universe in [("extended (132 + reviewed extras)", EXT_UNIVERSE), ("base dictionary only (132)", BASE)]:
        g = gold_sets(universe, drop=("Artificial Intelligence",) if drop_ai else ())
        for name, pr in preds.items():
            pr_s = {r: {s for s in v if s in universe and not (drop_ai and s == "Artificial Intelligence")} for r, v in pr.items()}
            out[(scope, name)] = prf(pr_s, g)
    return preds, pd.DataFrame(out).T

def bootstrap(preds, a, b, universe=EXT_UNIVERSE, n=2000, seed=36118):
    g = gold_sets(universe); rng = random.Random(seed); d = []; fa = []; fb = []
    pa = {r: preds[a][r] & universe for r in ROWS}; pb = {r: preds[b][r] & universe for r in ROWS}
    def f1(pr, rows):
        tp = sum(len(pr[r] & g[r]) for r in rows); fp = sum(len(pr[r] - g[r]) for r in rows); fn = sum(len(g[r] - pr[r]) for r in rows)
        return 2 * tp / (2 * tp + fp + fn) if tp else 0.0
    for _ in range(n):
        rows = [rng.choice(ROWS) for _ in ROWS]; x, y = f1(pa, rows), f1(pb, rows); fa.append(x); fb.append(y); d.append(y - x)
    q = lambda v: tuple(np.percentile(v, [2.5, 97.5]).round(3))
    return dict(F1_a=q(fa), F1_b=q(fb), delta=round(float(np.mean(d)), 3), delta_CI=q(d), p_delta_le_0=float(np.mean(np.array(d) <= 0)))

if __name__ == "__main__":
    pd.set_option("display.width", 200); pd.set_option("display.float_format", "{:.3f}".format)
    preds, res = run(); print(res.to_string())
    print("\nWithout 'Artificial Intelligence' in gold/pred (annotation-sensitivity check)"); print(run(drop_ai=True)[1].to_string())
    names = list(preds)
    for a, b in [(names[0], names[3]), (names[3], names[4]), (names[4], names[5]), (names[0], names[5])]:
        print("\nbootstrap", a, "->", b, bootstrap(preds, a, b))
