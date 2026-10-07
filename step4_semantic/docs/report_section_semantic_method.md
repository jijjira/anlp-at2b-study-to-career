# Semantic NLP Methodology and Evaluation (Member 4)

## Y.1 Motivation
Step 3's dictionary matcher reaches micro-F1 0.943 on explicit skills, but 27% of the skills a human reads in the 30 gold
ads are implicit (12.6%) or outside the dictionary (14.3%) (Step 3 error analysis). Exact matching cannot find a skill an ad
describes without naming, for example "measure how well models generalise" for Model Evaluation, or a database unit whose
handbook text never says "SQL". Sentence embeddings place paraphrases close together, so they can recover such skills.
This section tests whether that gain is real, how much precision it costs, and whether it transfers to unit text.

## Y.2 Method
**Hybrid design.** Baseline++ output is kept unchanged; the semantic layer only adds skills the exact matcher did not
find. This guarantees no explicit hit is lost and isolates the contribution of embeddings.

**Units.** Each ad is segmented with Step 3's section-aware segmenter; company/benefit lines are discarded, so
"founded by the creators of Spark" can never become semantic evidence, and every addition inherits a requirement strength
(required, duty, preferred) and hence a demand weight. Units are lines and comma/semicolon-separated clauses (min. 3 words).
Clauses give phrase-level matches; lines give context.

**Skill space.** Each dictionary skill is represented by its name and aliases (aliases under four characters stay with
the exact matcher, because embeddings of tokens such as "ml" or "go" are unreliable). A skill's prototype embeddings are
averaged into one centroid vector, and a unit's score for that skill is the cosine to the centroid (adopted after the
ablation in Y.4.4; see Y.5). Only skills in concept-like categories (statistics, ML, MLOps, methods, NLP/GenAI, data
engineering, BI) may be added; named languages, databases, cloud services, frameworks and developer tools
are always stated explicitly and stay with the exact matcher. This restriction was fixed before any result was seen.

**Decision rule.** A skill is added if a unit scores at least tau, optionally also within a margin delta of that unit's
best skill (to stop one sentence activating many related skills). Optionally, scores are z-normalised per skill against
4,000 unlabelled ad units (gold ads excluded) to remove hub skills that are close to everything.

**Models.** all-MiniLM-L6-v2, all-mpnet-base-v2 (pre-specified headline), bge-base-en-v1.5, plus a
character-hashing lexical control that has no semantic knowledge. If a neural model does not clearly beat the control, its
gain is surface similarity, not semantics.

## Y.3 Experimental design
**Gold data and definitions** are Step 3's (30 ads, R/P/I/OTHER tiers; extended dictionary scope). We report
(i) *strict* P/R/F1 against R+P (Step 3's metric), where valid implicit skills are counted as errors, so strict precision is
a pessimistic view for this method; (ii) *lenient* P/R/F1 against R+P+I, because an ad that demands a skill implicitly does
demand it; (iii) *I-recall*, the share of the 43 implicit labels recovered; (iv) the precision of the *additions* alone.

**Tuning without scoring on the tuning ad.** With only 30 labelled ads there is no separate development set. Tau and delta are chosen by
leave-one-ad-out cross-validation: for each ad the rule that maximises lenient micro-F1 on the other 29 is applied to that
ad, and all reported numbers use the pooled out-of-fold predictions. Ties favour the more conservative (higher) tau. Rules
tuned on all 30 ads are reported only as an optimistic reference and are used to process the unlabelled corpus.

**Inference.** Paired bootstrap over ads (2,000 resamples, seed 36118) for differences to Baseline++ and the original
baseline. Strict-F1 comparisons are computed with Step 3's own `evaluate.bootstrap` and checked against our
implementation, which also covers the lenient, precision and I-recall metrics that Step 3 does not define.
**Ablations** change one factor at a time (granularity, prototypes, pooling, allowed skills, normalisation, margin rule),
each re-tuned by cross-validation.

**Beyond the gold ads.** (a) All 688 ads are processed; 50 random semantic additions and 50 random exact hits from
non-gold ads are shuffled into one sheet that hides the source and score, and are labelled by one human annotator (the
method developer; ambiguous items resolved with an AI assistant applying a fixed written rule), giving the
precision of each method on unseen ads with Wilson 95% intervals. (b) The 20 real unit PDFs are processed;
the two cases flagged by Step 3 (COMP9311 "SQL", 36103 "Statistics") are reported, and all semantic additions plus 30
random exact hits are labelled by the same blinded procedure. Recall on unit text is not measurable.

## Y.4 Results
Gold-ad results are out-of-fold (leave-one-ad-out), with 95% paired-bootstrap intervals over ads (2,000 resamples).

**Y.4.1 Baselines reproduced.** Our metric code reproduces Step 3 exactly: PhraseMatcher strict F1 0.872 and Baseline++
0.943 on the 30 gold ads. Under the lenient view (R+P+I gold), they score 0.805 and 0.874, and both recall only 1 of the
43 implicit skills (0.023): exact matching almost never finds a skill that the ad does not name.

**Y.4.2 Model comparison (Table Y.1, Figure Y.1).**

*Table Y.1. Hybrid extractors vs Baseline++ on the 30 gold ads (out-of-fold).*

| System | Lenient P | Lenient R | Lenient F1 | I-recall | Additions | Additions precision |
|---|---|---|---|---|---|---|
| PhraseMatcher baseline (Step 3) | 0.906 | 0.724 | 0.805 | 0.023 | - | - |
| Baseline++ (Step 3) | 0.908 | 0.843 | 0.874 | 0.023 | - | - |
| Hashing hybrid (lexical control) | 0.908 | 0.843 | 0.874 | 0.023 | 0 | - |
| MiniLM hybrid | 0.891 | 0.867 | 0.879 | 0.186 | 13 | 0.538 |
| **MPNet hybrid (pre-specified)** | **0.888** | **0.891** | **0.889** | **0.349** | 22 | **0.636** |
| BGE-base hybrid | 0.887 | 0.881 | 0.884 | 0.279 | 19 | 0.579 |
| MPNet semantic-only (no exact matcher) | 0.585 | 0.457 | 0.513 | 0.605 | 116 | 0.224 |

The pre-specified MPNet hybrid is the best system. Against Baseline++ it raises lenient F1 from 0.874 to 0.889
(+0.015, 95% CI [0.003, 0.028]) and I-recall from 0.023 to 0.349 (+0.326, CI [0.204, 0.463]): about one in three skills
that ads imply without naming is now recovered. The price is precision: lenient precision falls from 0.908 to 0.888
(-0.020, CI [-0.038, -0.005]), and 64% of the 22 skills the semantic layer adds are correct. MiniLM and BGE-base move
in the same direction, but their lenient-F1 gains over Baseline++ are not significant (CIs include 0).

Against Step 3's original PhraseMatcher baseline, the combined gain of Step 3's dictionary work and the semantic layer is
larger: lenient F1 rises from 0.805 to 0.889 (+0.085, CI [0.052, 0.117]), while strict F1 is 0.904 against 0.872, a
difference that is not significant (+0.033, CI [-0.008, 0.071]).

Two controls make the result interpretable. The character-hashing encoder, which has no semantic knowledge, adds nothing
at its cross-validated threshold, so the gain is not fuzzy string matching. Without the exact matcher, MPNet alone reaches
the highest I-recall (0.605) but its precision collapses (0.585; additions precision 0.224), so embeddings work as a
complement to the dictionary, not a replacement.

**Y.4.3 Strict versus lenient.** Under Step 3's strict metric (R+P gold only), the hybrid scores 0.904 against 0.943
(-0.038, CI [-0.055, -0.023]). This is expected rather than a failure: Baseline++ already has R+P recall 0.984, so the
strict view can only count the newly found implicit skills as false positives. The strict number is reported for
comparability with Step 3; the lenient view and I-recall measure what the semantic layer is for.

**Y.4.4 Ablation (Figure Y.2).** Each design factor was changed one at a time and re-tuned by cross-validation.
* *Pooling* matters most. Averaging a skill's name and aliases into one centroid gives lenient F1 0.889 and additions
  precision 0.636, against 0.873 and 0.412 for taking the maximum over aliases: the maximum lets one loosely related
  alias trigger a match. Centroid pooling became the default after this ablation; when the pooling is instead chosen
  inside each cross-validation fold, centroid is selected in all 30 folds.
* *Granularity* trades recall for precision. Whole lines alone give the most precise additions (0.857, 7 additions) but
  recover fewer implicit skills (I-recall 0.163); combining lines and clauses gives the best balance (0.349).
* Representing a skill by its *name only* (0.869) or adding *category context* to aliases (0.870) is worse than names
  plus aliases (0.889). Allowing the layer to add *named tools* as well as concepts lowers both F1 (0.878) and additions
  precision (0.500), supporting the a-priori choice to leave tools and languages to the exact matcher.
* The *margin rule* helps (0.889 vs 0.877 without it). Per-skill *z-normalisation* never added a skill within the
  threshold grid (the selected threshold sat at the grid maximum), so it is equivalent to switching the semantic layer
  off; it is reported but not interpreted.

**Y.4.5 Error analysis.** Of the 43 implicit labels, 15 are found (1 by the exact matcher, 14 by the semantic layer)
and 28 are missed. Misses concentrate in skills whose wording in ads is far from any alias: Experiment Design (4 missed),
Prompt Engineering (3), Model Evaluation (3), and RAG and Recommendation Systems (2 each). Recoveries concentrate in
Model Evaluation (3), Cloud Computing, Data Modeling, Data Pipelines and Data Visualization (2 each). The 8 wrong
additions share one pattern: a short or generic unit that shares a key word with a skill but not its meaning, e.g.
"clean data models." -> Data Cleaning, "Partner with AI" -> AI Agents, or "market data infrastructure" -> Data
Warehousing.

**Y.4.6 Precision on unseen ads (human audit).** On a blinded, shuffled sample from the 658 non-gold ads, 32 of 50
semantic additions were judged correct (precision 0.640, Wilson 95% CI [0.501, 0.759]), against 48 of 50 exact-match
hits (0.960, CI [0.865, 0.989]), which also confirms on unseen ads that Step 3's matcher is highly precise. The semantic precision on unseen ads matches the cross-validated estimate on the gold
ads (0.636), which suggests the gold-ad result generalises beyond the tuning set. The 18 wrong additions fall into three
groups. (i) A related but different skill (12): general descriptions of data platforms or "data infrastructure" gave
Data Warehousing (0 of 3 correct), working with "infrastructure engineers" gave Infrastructure as Code (1 of 3),
"containerized services" gave Kubernetes, and "diagnose failures" gave Model Monitoring. (ii) A different word sense (2):
"generate and test hypotheses" (informal) gave the statistical skill Hypothesis Testing, and "developing models" (ML
models) gave Data Modeling. (iii) Team or company descriptions rather than the role (3): introductions of the Pinterest,
BILL and Databricks organisations that Step 3's section segmenter did not mark as company text; one further addition
described work done by an automated agent rather than by the person hired. Most errors are therefore plausible
neighbours of the right skill, which is what a similarity threshold cannot separate; a verification step (for example an
entailment model asking "does this line require skill X?") is the natural next improvement.

**Y.4.7 Unit PDFs (student side).** On the 20 real unit PDFs, the semantic layer adds 1 to 5 skills to 10 units. Of the
two cases flagged by Step 3, UTS 36103 now gets Statistics ("This subject instills the statistical thinking central to
data science", cosine 0.71), but UNSW COMP9311 still does not get SQL; instead it receives Data Warehousing, the skill
the audit found least reliable. Using the hybrid on both sides raises curriculum fit for every career (for example AI
Engineer 0.326 -> 0.408 and Data Scientist 0.654 -> 0.685), but leaves Step 3's ranking unchanged: Data Scientist
highest, AI Engineer lowest. The same blinded
audit on unit text (all 22 semantic additions plus 30 random exact hits) found 17 of 22 semantic additions correct
(precision 0.773, Wilson 95% CI [0.566, 0.899]) against 29 of 30 exact hits (0.967, [0.833, 0.994]). Three of the five
wrong additions are Data Warehousing given to database or data-systems units (COMP9311, COMP9321, 41091), the same skill
that failed in the job-ad audit; the others are Vector Search and AI Agents. The career-fit increases are therefore
exploratory estimates: false-positive additions can inflate them, and because recall on unit text is not measured, they
are not a bound in either direction.

**Y.4.8 Summary.** Sentence embeddings recover about a third of the skills that ads imply without naming, with a small
but significant gain in lenient F1. Each added skill is right about two times in three, on both the gold ads and unseen
ads (and about three times in four on unit text), whereas exact matching is right about 24 times in 25. The hybrid is
therefore suited to finding candidate skills for a student to review, with source and evidence shown, rather than to
producing a definitive profile.

## Y.5 Limitations
* **Gold labels**: one AI annotator working blind to system output, silver standard; n = 30 and only 43 implicit labels,
  so intervals are wide and per-skill claims are anecdotal.
* **Repeated use of the 30 gold ads**: model comparison, ablations and error analysis were all run on them, and centroid
  pooling replaced max pooling after the first ablation. Leave-one-ad-out selection keeps the threshold (and, in the
  "pool chosen in CV" check, the pooling) from seeing the ad being scored, but not the optimism of choosing models, grids
  and design on these ads, so the comparison is partly exploratory. The headline model was fixed in advance.
* **Step 3 optimism inherited**: one header-parsing rule in the Baseline++ was fixed after looking at a gold ad, a small
  source of optimism in the baseline we compare against.
* **Strict metric ceiling**: Baseline++ already has R+P recall 0.984, so strict F1 cannot improve materially; the gain
  must be read on lenient F1, I-recall and additions precision.
* **Lenient gold uses the I tier**, which was labelled as "the target for the semantic method"; the circularity is mild
  (labelled blind to system output) but should be stated.
* **No unit-text gold**: only precision of hits is audited; skills taught without any wording close to a dictionary
  prototype remain undetected, and handbook pages are shorter than full outlines.
* **Single human annotator** for the precision audits (the method developer, blinded to the method that produced each
  item; ambiguous items AI-assisted under a fixed rule); no inter-annotator agreement. Exact-hit evidence lines contain
  the skill name, so blinding is partial.
* **Out-of-dictionary skills (OTHER tier)** cannot be recovered because matching targets dictionary skills.
* English-only embedding models; US job ads; thresholds tuned on job ads may transfer imperfectly to unit text.
