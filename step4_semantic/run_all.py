"""Run the whole Step 4 pipeline.

    python run_all.py verify                    # check metric code reproduces Step 3 (S0 0.872, S5 0.943)
    python run_all.py compare                   # model comparison + LOOCV + paired bootstrap (+ final_config.json)
    python run_all.py ablate                    # one-factor ablations around the main model
    python run_all.py errors figures            # error analysis, figures
    python run_all.py corpus curriculum         # 688 ads + 20 unit PDFs, with audit/label sheets
    python run_all.py report                    # results/summary.md + docs/README_section_student4.md
    (results/ stays tidy: summary.md + audit/ (human labelling) + handoff/ (Students 5, 6) + details/ (all other tables))
    python run_all.py all                       # everything, in order

Options:  --step3 PATH   --models minilm mpnet ...   --device cuda|cpu   --n-boot 2000   --quick (2 models, 300 resamples)
First run downloads the models from Hugging Face (internet needed once); embeddings are cached in cache/.
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict

import pandas as pd

import config
import experiments as ex

STAGES = ["verify", "compare", "ablate", "errors", "figures", "corpus", "curriculum", "report"]


def tic(msg):
    print(f"\n=== {msg}", flush=True)
    return time.time()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stages", nargs="+", choices=STAGES + ["all"])
    ap.add_argument("--step3", default=None)
    ap.add_argument("--models", nargs="+", default=None)
    ap.add_argument("--device", default=None)
    ap.add_argument("--n-boot", type=int, default=config.N_BOOT)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    stages = STAGES if "all" in a.stages else a.stages
    models = a.models or (["hashing", config.MAIN_MODEL] if a.quick else config.COMPARE_MODELS)
    n_boot = 300 if a.quick else a.n_boot
    config.ensure_dirs()

    from data_access import load_context, verify_against_step3
    ctx = load_context(a.step3)
    runner = ex.Runner(ctx, device=a.device)
    R, D, A, H = config.RESULTS, config.DETAILS, config.AUDIT, config.HANDOFF
    print(f"Step 3 folder: {ctx.step3}\n{len(ctx.rows)} gold ads, universe of {len(ctx.universe)} skills")

    for st in stages:
        t = tic(st)
        if st == "verify":
            v = verify_against_step3(ctx)
            print({k: (round(x["F1"], 3) if isinstance(x, dict) else x) for k, x in v.items()})
            ex.baseline_table(ctx).to_csv(D / "baseline_table.csv", index=False)

        elif st == "compare":
            table, boots, results = ex.model_comparison(runner, models, n_boot)
            table.to_csv(D / "model_comparison.csv", index=False)
            ex.flatten_ci(boots).to_csv(D / "model_bootstrap.csv", index=False)
            ex.all_sweeps(results).to_csv(D / "sweeps.csv", index=False)
            main = results[f"{config.MAIN_MODEL} hybrid"] if f"{config.MAIN_MODEL} hybrid" in results else next(
                r for n, r in results.items() if not r["semantic_only"])
            ex.save_json(dict(model=main["model"], cfg=main["cfg"], decision=asdict(main["insample_decision"]),
                              note="decision tuned on all 30 gold ads (optimistic); headline numbers are LOOCV"),
                         D / "final_config.json")
            ex.save_json({str(r): asdict(d) for r, d in main["chosen"].items()}, D / "loocv_chosen_decisions_main.json")
            ex.save_json({str(r): sorted(s) for r, s in main["oof"].items()}, D / "oof_predictions_main.json")
            print(table[["system", "tau_median", "strict_F1", "lenient_P", "lenient_R", "lenient_F1", "I_recall",
                         "n_added", "added_precision"]].round(3).to_string(index=False))

        elif st == "ablate":
            abl, abl_boot = ex.ablation(runner, config.MAIN_MODEL, n_boot)
            abl.to_csv(D / "ablation.csv", index=False)
            ex.flatten_ci(abl_boot).to_csv(D / "ablation_bootstrap.csv", index=False)
            print(abl.round(3).to_string(index=False))

        elif st == "errors":
            import error_analysis as ea
            df, by = ea.error_table(runner, ex.run_config(runner, config.MAIN_MODEL))
            ea.save(df, by)
            print(df.kind.value_counts().to_string())

        elif st == "figures":
            import figures as fg
            base = pd.read_csv(D / "baseline_table.csv").set_index("system").loc[ex.S5]
            mc, mb = pd.read_csv(D / "model_comparison.csv"), pd.read_csv(D / "model_bootstrap.csv")
            _sw = pd.read_csv(D / "sweeps.csv")
            for m in [config.MAIN_MODEL]:            # one sweep figure (main model); other models: results/details/sweeps.csv
                fg.fig_threshold_sweep(_sw[_sw.model == m].drop(columns="model"), m, base["lenient_F1"], base["I_recall"])
            fg.fig_model_comparison(mc, mb, base)
            if (D / "ablation.csv").exists():
                fg.fig_ablation(pd.read_csv(D / "ablation.csv"))

        elif st == "corpus":
            import corpus_extract as ce
            final = ce.load_final()
            print(ce.run(runner, final))

        elif st == "curriculum":
            import curriculum_semantic as cs
            import corpus_extract as ce
            final = ce.load_final()
            hy = ce.build_hybrid(runner, final)
            exact_p, hyb_p, man, adds = cs.load_curriculum_hybrid(ctx.step3, hy.space, hy.encoder, hy.decision,
                                                                   hy.granularity, hy.min_words, hy.max_words)
            runner.save()
            adds.to_csv(D / "curriculum_semantic_additions.csv", index=False)
            if ce._has_labels(A / "curriculum_label_sheet.csv"):
                print("  NOTE: curriculum_label_sheet.csv already has labels - not overwritten")
            else:
                sheet, key = cs.label_sheet(exact_p, hyb_p)
                sheet.to_csv(A / "curriculum_label_sheet.csv", index=False)
                key.to_csv(A / "curriculum_label_key.csv", index=False)       # do NOT show this file to annotators
            cs.all_hits(exact_p, hyb_p).to_csv(D / "curriculum_all_hits.csv", index=False)
            summ = pd.DataFrame([dict(unit_id=u, n_exact=len(exact_p[u].skills),
                                      n_semantic_added=len(hyb_p[u].skills) - len(exact_p[u].skills),
                                      added=", ".join(sorted(set(hyb_p[u].skills) - set(exact_p[u].skills))))
                                 for u in exact_p])
            summ.to_csv(D / "curriculum_unit_summary.csv", index=False)
            checks = cs.named_checks(exact_p, hyb_p, man)
            ex.save_json(checks, D / "curriculum_named_checks.json")
            cs.career_fit_comparison(ctx.step3, ctx.jobs, ctx.s5, hy, exact_p, hyb_p).to_csv(
                D / "curriculum_fit_exact_vs_hybrid.csv", index=False)
            print(summ.to_string(index=False)), print(json.dumps(checks, indent=1, default=str))

        elif st == "report":
            import make_report
            make_report.main()
        print(f"   ({time.time() - t:.0f}s)")
    runner.save()


if __name__ == "__main__":
    main()
