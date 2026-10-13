"""Agreement between the gold labels (LLM annotator) and an independent human annotator.
Usage (from step3_baseline_nlp/):  python3 annotation/human_agreement.py human_merged.xlsx
Needs annotation/human_annotation_key.csv.  Reports Cohen's kappa over the labelled candidate pool
(pool = extractor hits + gold skills + 12 random distractors per ad, so kappa is pool-restricted)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # step3 root on the path
import sys, random
import numpy as np, pandas as pd
SEED=36118
f=sys.argv[1]
lab=pd.read_excel(f,sheet_name="Labels"); lab.columns=["ad_no","job_title","skill","human"]
key=pd.read_csv("annotation/human_annotation_key.csv")
m=key.merge(lab[["ad_no","skill","human"]],on=["ad_no","skill"],how="left")
m["human"]=m.human.astype(str).str.strip().str.upper().replace({"NAN":np.nan})
missing=m.human.isna().sum()
if missing: sys.exit(f"{missing} rows are unlabelled; finish the sheet first")
bad=set(m.human)-set("RPIN")
if bad: sys.exit(f"unexpected labels: {bad}")
def kappa(a,b):
    a=np.asarray(a); b=np.asarray(b); cats=sorted(set(a)|set(b)); po=(a==b).mean()
    pe=sum((a==c).mean()*(b==c).mean() for c in cats)
    return (po-pe)/(1-pe) if pe<1 else 1.0
def boot(fn,n=2000):
    rng=random.Random(SEED); ads=sorted(m.ad_no.unique()); out=[]
    for _ in range(n):
        s=[rng.choice(ads) for _ in ads]; d=pd.concat([m[m.ad_no==a] for a in s])
        try: out.append(fn(d))
        except Exception: pass
    return np.nanpercentile(out,[2.5,97.5])
named=lambda s: s.isin(["R","P"])
tests={"Named and demanded (R or P vs not)":lambda d:kappa(named(d.gold_label),named(d.human)),
       "Required (R vs not)":lambda d:kappa(d.gold_label=="R",d.human=="R"),
       "Implicit (I vs not)":lambda d:kappa(d.gold_label=="I",d.human=="I"),
       "Four classes R/P/I/N":lambda d:kappa(d.gold_label,d.human)}
res=[]
for k,fn in tests.items():
    lo,hi=boot(fn); res.append((k,fn(m),lo,hi))
    print(f"{k:40s} kappa = {res[-1][1]:.2f}  95% CI [{lo:.2f}, {hi:.2f}]")
print(f"\nraw agreement (4 classes) = {(m.gold_label==m.human).mean():.1%} over {len(m)} labels in {m.ad_no.nunique()} ads")
print(pd.crosstab(m.gold_label,m.human,rownames=["gold (LLM)"],colnames=["human"]).to_string())
pd.DataFrame(res,columns=["measure","kappa","ci_low","ci_high"]).to_csv("annotation/human_agreement_results.csv",index=False)
