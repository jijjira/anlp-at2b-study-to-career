"""Offline tests (no model download, no spaCy): they use the hashing control encoder and a tiny fake Step 3 base.

Run:  cd step4_semantic && python -m pytest -q
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
import metrics
from data_access import Context
from semantic_extractor import (Decision, HashingEncoder, HybridExtractor, SkillSpace, detect, make_units,
                                REQUIRED, DUTY, PREFERRED, COMPANY, UNLABELLED)
import experiments as ex

TABLE = pd.DataFrame([
    ("Model Evaluation", "model evaluation", "Machine Learning & AI"),
    ("Model Evaluation", "model validation", "Machine Learning & AI"),
    ("Experiment Design", "experiment design", "Data Analysis & Statistics"),
    ("Data Visualization", "data visualization", "Data Visualisation / BI"),
    ("Python", "python", "Programming"),
    ("SQL", "sql", "Databases"),
], columns=["canonical_skill", "alias", "category"])


class FakeBase:
    """Minimal stand-in for RequirementAwareExtractor: one line per segment, simple headers."""
    weights = {REQUIRED: 1.0, DUTY: 0.75, PREFERRED: 0.5, UNLABELLED: 0.5, COMPANY: 0.0}
    ALIAS = {"python": "Python", "sql": "SQL", "model evaluation": "Model Evaluation",
             "data visualization": "Data Visualization", "experiment design": "Experiment Design"}

    def segment(self, text):
        state = REQUIRED
        for i, raw in enumerate(text.split("\n")):
            line = raw.strip()
            if not line:
                continue
            if line.lower().startswith("about us"):
                state = COMPANY
                continue
            if line.lower().startswith("preferred"):
                state = PREFERRED
                continue
            if line.lower().startswith("requirements"):
                state = REQUIRED
                continue
            yield i, line, state

    def skill_strengths(self, text):
        out = {}
        for _, line, st in self.segment(text):
            for a, c in self.ALIAS.items():
                if a in line.lower() and c not in out:
                    out[c] = st
        return out

    def extract_skills(self, text, mode="demand"):
        return [s for s, st in self.skill_strengths(text).items() if st != COMPANY]


def test_make_units_drops_company_and_short_lines():
    segs = [(0, "- Own model evaluation and the validation pipeline", REQUIRED), (1, "Hi", REQUIRED),
            (2, "Founded by the creators of Spark and loved by customers", COMPANY)]
    units = make_units(segs, "line+clause")
    assert all(u.strength != COMPANY for u in units)
    assert all(len(u.text.split()) >= 3 for u in units)
    assert units[0].text.startswith("Own model evaluation")
    kinds = {u.kind for u in make_units([(0, "Design experiments, measure uplift, report results to leadership", REQUIRED)], "line+clause")}
    assert kinds == {"line", "clause"}
    assert {u.kind for u in make_units(segs, "line")} == {"line"}


def test_detect_threshold_margin_topk():
    S = np.array([[0.9, 0.85, 0.2], [0.3, 0.2, 0.1]])
    assert set(detect(S, Decision(0.5))) == {0, 1}
    assert set(detect(S, Decision(0.5, delta=0.02))) == {0}
    assert set(detect(S, Decision(0.5, topk=1))) == {0}
    assert detect(S, Decision(0.95)) == {}
    k, (score, row) = next(iter(detect(S, Decision(0.5)).items()))
    assert row == 0 and abs(score - 0.9) < 1e-9


def test_skill_space_filters_categories_and_pools():
    enc = HashingEncoder()
    sp = SkillSpace(TABLE, enc, "aliases", "max", "concept")
    assert "Python" not in sp.skills and "SQL" not in sp.skills and "Model Evaluation" in sp.skills
    sp_all = SkillSpace(TABLE, enc, "aliases", "max", "all")
    assert "Python" in sp_all.skills
    emb = enc.encode(["we validate every model before launch"])
    sim = sp.similarity(emb)
    assert sim.shape == (1, len(sp.skills))
    sp_c = SkillSpace(TABLE, enc, "canonical", "centroid", "concept")
    assert sp_c.similarity(emb).shape == sim.shape


def test_hybrid_adds_only_missing_skills_and_respects_company():
    enc = HashingEncoder()
    sp = SkillSpace(TABLE, enc, "aliases", "max", "concept")
    text = ("Requirements:\nPython and SQL\nOwn the model validation process for our ranking models\n"
            "About us:\nWe love data visualization and experiment design")
    h = HybridExtractor(FakeBase(), sp, enc, Decision(0.30))
    ev = {e.skill: e for e in h.analyse(text)}
    assert ev["Python"].source == "exact" and ev["SQL"].source == "exact"
    assert "Model Evaluation" in ev
    assert "Data Visualization" not in ev and "Experiment Design" not in ev
    assert all(e.strength != COMPANY for e in ev.values())
    w = h.extract_weighted(text)
    assert w["Python"] == 1.0 and set(w) == set(h.extract_skills(text))
    assert h.skill_strengths(text)["Python"] == REQUIRED


def test_metrics_match_step3_definitions():
    GOLD = {1: dict(R={"A", "B"}, P={"C"}, I={"D"}, OTHER={"Z"}), 2: dict(R={"A"}, P=set(), I=set(), OTHER=set())}
    U = {"A", "B", "C", "D"}
    v = metrics.gold_views(GOLD, [1, 2], U)
    pred = {1: {"A", "D", "E"}, 2: {"A"}}
    s = metrics.prf(pred, v["strict"], [1, 2])
    assert (s["TP"], s["FP"], s["FN"]) == (2, 2, 2) and abs(s["P"] - 0.5) < 1e-9
    l = metrics.prf(pred, v["lenient"], [1, 2])
    assert (l["TP"], l["FP"], l["FN"]) == (3, 1, 2)
    assert metrics.i_recall(pred, v["I"], [1, 2]) == 1.0
    base = {1: {"A"}, 2: {"A"}}
    a = metrics.additions_precision(pred, base, v["lenient"], v["I"], [1, 2])
    assert a["n_added"] == 2 and a["added_correct"] == 1 and a["added_I"] == 1
    lo, hi = metrics.wilson(8, 10)
    assert 0.4 < lo < 0.8 < hi < 1.0


def test_bootstrap_detects_improvement():
    rows = list(range(20))
    GOLD = {r: dict(R={"A"}, P=set(), I={"B"}, OTHER=set()) for r in rows}
    v = metrics.gold_views(GOLD, rows, {"A", "B"})
    base = {r: {"A"} for r in rows}
    better = {r: {"A", "B"} for r in rows}
    res = metrics.paired_bootstrap(base, better, metrics.metric_fn("I_recall", v), rows, 200, 1)
    assert res["delta"] == 1.0 and res["delta_CI"][0] > 0.9 and res["p_delta_le_0"] == 0.0


def _tiny_context():
    texts = []
    for i in range(8):
        texts.append("Requirements:\nPython and SQL\nOwn model validation for ranking models\n"
                     "Preferred:\nRun experiment design reviews with product\nAbout us:\nWe love data visualization")
    jobs = pd.DataFrame({"job_description": texts})
    GOLD = {r: dict(R={"Python", "SQL"}, P=set(), I={"Model Evaluation"}, OTHER=set()) for r in range(8)}
    universe = set(TABLE.canonical_skill)
    fb = FakeBase()
    base_pred = {r: set(fb.extract_skills(texts[r])) & universe for r in range(8)}
    ctx = Context(Path("."), jobs, GOLD, list(range(8)), TABLE, universe, fb, fb,
                  metrics.gold_views(GOLD, list(range(8)), universe))
    ctx.base_preds = {ex.S0: base_pred, ex.S5: base_pred}
    return ctx


def test_loocv_pipeline_end_to_end_offline(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "TAU_GRID_RAW", [0.2, 0.3, 0.4, 0.5, 0.6])
    ctx = _tiny_context()
    runner = ex.Runner(ctx)
    res = ex.run_config(runner, "hashing")
    assert set(res["oof"]) == set(ctx.rows) and set(res["chosen"]) == set(ctx.rows)
    assert 0 <= res["oof_summary"]["lenient_F1"] <= 1
    assert all(ctx.base_preds[ex.S5][r] <= res["oof"][r] for r in ctx.rows)
    assert res["oof_summary"]["I_recall"] >= metrics.i_recall(ctx.base_preds[ex.S5], ctx.views["I"], ctx.rows)
    bt = ex.compare_to_baselines(ctx, res["oof"], n_boot=50)
    assert {"vs", "metric", "delta", "delta_CI"} <= set(bt.columns)
    sem_only = ex.run_config(runner, "hashing", semantic_only=True)
    assert sem_only["semantic_only"]


def test_selection_never_sees_held_out_ad():
    decisions = [Decision(0.3), Decision(0.9)]
    lenient = {0: set(), 1: {"X"}, 2: {"X"}}
    p_low = {0: {"X"}, 1: {"X"}, 2: {"X"}}
    p_high = {0: set(), 1: set(), 2: set()}
    oof, chosen = ex.loocv(decisions, [p_low, p_high], {"lenient": lenient}, [0, 1, 2])
    assert chosen[0].tau == 0.3 and oof[0] == {"X"}


def test_z_normalisation_requires_reference():
    enc = HashingEncoder()
    sp = SkillSpace(TABLE, enc, "aliases", "max", "concept")
    emb = enc.encode(["model validation process"])
    try:
        sp.normalise(sp.similarity(emb), "z")
        raise AssertionError("expected RuntimeError")
    except RuntimeError:
        pass
    sp.fit_reference(enc.encode(["a b c", "model validation", "sql tables", "random words here"]))
    assert sp.normalise(sp.similarity(emb), "z").shape == (1, len(sp.skills))


# ----------------------------------------------------------------------------- unit-text label sheet
class _Prof:
    def __init__(self, skills):
        self.skills = skills


def _fake_profiles():
    def d(src, score=None):
        return dict(pages=[1], level="taught", evidence="some evidence sentence", source=src, score=score, weight=0.75,
                    mentions=1, category="x")
    exact = {f"U{u}": _Prof({f"E{u}_{i}": d("exact") for i in range(30)}) for u in range(3)}
    hyb = {}
    for u, p in exact.items():
        sk = dict(p.skills)
        sk[f"S_{u}_a"], sk[f"S_{u}_b"] = d("semantic", 0.7), d("semantic", 0.68)
        hyb[u] = _Prof(sk)
    return exact, hyb


def test_label_sheet_is_blinded_sampled_and_keyed(tmp_path):
    import curriculum_semantic as cs
    exact, hyb = _fake_profiles()
    sheet, key = cs.label_sheet(exact, hyb, n_exact=20, seed=1)
    assert "source" not in sheet.columns and "score" not in sheet.columns        # annotators must not see the method
    assert len(sheet) == 6 + 20                                                  # all 6 semantic + 20 sampled exact
    assert set(key.item_id) == set(sheet.item_id) and (key.source == "semantic").sum() == 6
    assert sheet.item_id.is_unique
    sheet2, _ = cs.label_sheet(exact, hyb, n_exact=20, seed=1)
    assert list(sheet.item_id) == list(sheet2.item_id) and list(sheet.skill) == list(sheet2.skill)   # reproducible
    # fill labels: all semantic correct, exact half correct
    filled = sheet.merge(key[["item_id", "source"]], on="item_id")
    labels, k = [], 0
    for src in filled.source:
        if src == "semantic":
            labels.append(1)
        else:
            labels.append(k % 2)
            k += 1
    filled["human_label"] = labels
    sp, kp = tmp_path / "sheet.csv", tmp_path / "key.csv"
    filled.drop(columns="source").to_csv(sp, index=False)
    key.to_csv(kp, index=False)
    out = cs.evaluate_unit_labels(sp, kp).set_index("source")
    assert out.loc["semantic", "n_labelled"] == 6 and out.loc["semantic", "precision"] == 1.0
    assert out.loc["exact", "n_labelled"] == 20 and abs(out.loc["exact", "precision"] - 0.5) < 1e-9
    assert out.loc["semantic", "ci_lo"] < 1.0


def test_step3_bootstrap_returns_none_when_step3_unavailable(tmp_path):
    from data_access import step3_bootstrap
    ctx = _tiny_context()
    ctx.step3 = tmp_path                                                         # no evaluate.py here
    assert step3_bootstrap(ctx, ctx.base_preds[ex.S5], ctx.base_preds[ex.S5], n=10) is None
    bt = ex.compare_to_baselines(ctx, ctx.base_preds[ex.S5], n_boot=20)            # must still work (just without the rows)
    assert not bt.metric.str.contains("Step 3").any()


def test_report_and_audit_defaults_use_new_folders(tmp_path, monkeypatch):
    import corpus_extract as ce
    import curriculum_semantic as cs
    for k, v in dict(RESULTS=tmp_path, DETAILS=tmp_path / "details", AUDIT=tmp_path / "audit", HYBRID=tmp_path / "hybrid_job_skills").items():
        monkeypatch.setattr(config, k, v)
    for d in (config.DETAILS, config.AUDIT, config.HYBRID):
        d.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"item_id": ["J1", "J2", "J3"], "skill": ["A", "A", "B"], "human_label": [1, 0, 1]}).to_csv(
        config.AUDIT / "job_audit_sheet.csv", index=False)
    pd.DataFrame({"item_id": ["J1", "J2", "J3"], "source": ["exact", "semantic", "semantic"]}).to_csv(
        config.AUDIT / "job_audit_key.csv", index=False)
    out = ce.evaluate_job_audit().set_index("source")                             # default paths = results/audit/
    assert out.loc["exact", "precision"] == 1.0 and out.loc["semantic", "n_labelled"] == 2


# ----------------------------------------------------------------------------- centroid default + pool chosen in CV
def test_default_pool_is_centroid_and_pool_can_be_chosen_inside_cv(monkeypatch):
    assert config.DEFAULTS["pool"] == "centroid"
    monkeypatch.setattr(config, "TAU_GRID_RAW", [0.2, 0.3, 0.4, 0.5, 0.6])
    ctx = _tiny_context()
    runner = ex.Runner(ctx)
    res = ex.run_pool_cv(runner, "hashing")
    assert set(res["oof"]) == set(ctx.rows) and set(res["pool_chosen"].values()) <= {"max", "centroid"}
    assert all(ctx.base_preds[ex.S5][r] <= res["oof"][r] for r in ctx.rows)          # hybrid never drops exact hits
    assert "/8" in res["pool_note"]
    row = ex.row_for("x", res)                                                        # fits the comparison table
    assert 0 <= row["lenient_F1"] <= 1


def test_cv_pool_selection_uses_only_other_ads():
    # two candidate rules: rule 0 is right on ads 1-2, rule 1 only on ad 0 -> ad 0 must get rule 0 (chosen on ads 1-2)
    lenient = {0: {"X"}, 1: {"X"}, 2: {"X"}}
    p0 = {0: set(), 1: {"X"}, 2: {"X"}}
    p1 = {0: {"X"}, 1: set(), 2: set()}
    tp, fp, fn = ex._counts_lenient([p0, p1], lenient, [0, 1, 2])
    best_for_0 = ex._pick(tp[:, [1, 2]], fp[:, [1, 2]], fn[:, [1, 2]], [0.5, 0.5])
    assert best_for_0 == 0


# ----------------------------------------------------------------------------- exact hits carry evidence lines
class _M:
    def __init__(self, canonical, strength, line, line_no):
        self.canonical, self.strength, self.line, self.line_no = canonical, strength, line, line_no


class FakeBaseWithAnalyse(FakeBase):
    def analyse(self, text):
        out = []
        for i, line, st in self.segment(text):
            for a, c in self.ALIAS.items():
                if a in line.lower():
                    out.append(_M(c, st, line, i))
        return out


def test_exact_hits_get_their_evidence_line():
    enc = HashingEncoder()
    sp = SkillSpace(TABLE, enc, "aliases", "centroid", "concept")
    text = "Requirements:\n- Python and SQL daily\nOwn the model validation process for our ranking models"
    ev = {e.skill: e for e in HybridExtractor(FakeBaseWithAnalyse(), sp, enc, Decision(0.99)).analyse(text)}
    assert ev["Python"].unit == "Python and SQL daily" and ev["Python"].line_no == 1     # bullet removed, line kept
    ev_old = {e.skill: e for e in HybridExtractor(FakeBase(), sp, enc, Decision(0.99)).analyse(text)}
    assert ev_old["Python"].unit is None                                               # bases without analyse still work


# ----------------------------------------------------------------------------- blinded job-ad audit (single annotator)
def _fake_long():
    jobs = pd.DataFrame({"job_title": [f"T{r}" for r in range(10)],
                         "job_description": [f"Requirements:\nWe use python {r}\nvalidate models carefully, report {r}"
                                             for r in range(10)]})
    recs = []
    for r in range(10):
        recs.append(dict(row=r, job_id=f"j{r}", canonical_skill="Python", source="exact", strength="required",
                         evidence=f"We use python {r}", score=None, line_no=1))
        recs.append(dict(row=r, job_id=f"j{r}", canonical_skill="Model Evaluation", source="semantic",
                         strength="required", evidence="validate models carefully", score=0.7, line_no=2))
    return pd.DataFrame(recs), jobs


def test_blind_job_audit_is_blinded_excludes_gold_and_reproducible():
    import corpus_extract as ce
    long, jobs = _fake_long()
    sheet, key = ce.blind_job_audit(long, jobs, gold_rows={0, 1}, n_sem=5, n_exact=5, seed=1)
    assert not {"source", "score", "row"} & set(sheet.columns)                         # annotator cannot see the method
    assert len(sheet) == 10 and (key.source == "semantic").sum() == 5 and set(key.row).isdisjoint({0, 1})
    assert set(sheet.item_id) == set(key.item_id) and sheet.item_id.is_unique
    sem_ev = sheet.merge(key, on="item_id").query("source == 'semantic'").evidence
    assert all(e.startswith("validate models carefully, report") for e in sem_ev)     # full line, not the clause
    sheet2, _ = ce.blind_job_audit(long, jobs, gold_rows={0, 1}, n_sem=5, n_exact=5, seed=1)
    assert list(sheet.item_id) == list(sheet2.item_id) and list(sheet.skill) == list(sheet2.skill)


def test_evaluate_job_audit_and_label_guard(tmp_path):
    import corpus_extract as ce
    long, jobs = _fake_long()
    sheet, key = ce.blind_job_audit(long, jobs, gold_rows=set(), n_sem=10, n_exact=10, seed=1)
    sp, kp = tmp_path / "job_audit_sheet.csv", tmp_path / "job_audit_key.csv"
    sheet.to_csv(sp, index=False), key.to_csv(kp, index=False)
    assert not ce._has_labels(sp)
    src = sheet.merge(key, on="item_id").source
    sheet["human_label"] = [1 if s == "exact" else (i % 2) for i, s in enumerate(src)]
    sheet.to_csv(sp, index=False)
    assert ce._has_labels(sp)
    out = ce.evaluate_job_audit(sp, kp).set_index("source")
    assert out.loc["exact", "precision"] == 1.0 and out.loc["semantic", "n_labelled"] == 10



def test_extractor_uses_same_exclusion_rule_as_evaluation():
    # a skill named only in company text must not block a semantic addition from role text (as in experiments.predictions)
    enc = HashingEncoder()
    sp = SkillSpace(TABLE, enc, "aliases", "centroid", "concept")
    text = "Requirements:\nBuild dashboards that visualise product metrics\nAbout us:\nWe love data visualization"
    base = FakeBase()
    assert base.skill_strengths(text).get("Data Visualization") == COMPANY
    ev = {e.skill: e for e in HybridExtractor(base, sp, enc, Decision(-1.0)).analyse(text)}
    assert ev["Data Visualization"].source == "semantic" and ev["Data Visualization"].strength == REQUIRED
