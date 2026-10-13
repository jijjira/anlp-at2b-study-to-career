"""Streamlit interface for the Study-to-Career project (version 2).

Run from the repository root with:
    streamlit run step6_app/app.py

The app does not reimplement the NLP or matching logic. It calls the Step 5
frontend API, which in turn runs the Step 3 exact extractor and (optionally)
the Step 4 semantic extractor before calculating Step 5 career matches.

Changes in version 2 (made after the formative user test, n = 3):
  * Plain-language method names with a one-line "when to use it" (P1 found the
    two modes unclear).
  * A built-in sample outline so a first-time user can see a result in one click.
  * Skills found only by the semantic layer are marked "possibly covered" and
    counted separately, because the blinded audit found about one in three of
    them wrong.
  * A "how to read this" panel and a warning when career scores are too close
    to rank (the middle careers sit within about two points of each other).
  * Per-career coverage bar, demand shown as a bar, and a
    CSV download of the skill gaps next to the JSON.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Repository imports
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
STEP5_DIR = REPO_ROOT / "step5_matching"
if str(STEP5_DIR) not in sys.path:
    sys.path.insert(0, str(STEP5_DIR))

from frontend_api import CareerMatchingAPI  # noqa: E402

SAMPLE_PDF = REPO_ROOT / "step3_baseline_nlp" / "sample_unit_outline.pdf"

EXACT_LABEL = "Fast: exact skill names"
HYBRID_LABEL = "Deeper: also finds skills described in other words"
METHOD_HELP = {
    EXACT_LABEL: (
        "Looks for skill names from our dictionary (for example SQL or machine "
        "learning). Takes a few seconds and almost never adds a wrong skill."
    ),
    HYBRID_LABEL: (
        "Does the same, then also reads sentences to find skills that are "
        "described but not named. Finds more, but about one in three of these "
        "extra skills is wrong, so they are marked as possibly covered. The "
        "first run loads a language model and can take a few minutes."
    ),
}

# Colour is never the only signal: every state also has a symbol and a word.
BADGE = {
    "assessed": "Assessed (strongest)",
    "taught": "Taught",
    "mentioned": "Mentioned (weakest)",
}

st.set_page_config(
    page_title="Study-to-Career Matcher",
    page_icon="🎓",
    layout="wide",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 2rem; max-width: 1200px;}
      .hero {padding: 1.1rem 1.4rem; border-radius: 14px;
             background: linear-gradient(135deg, #0f3d5e 0%, #1b6ca8 100%);
             color: #fff; margin-bottom: 1rem;}
      .hero h1 {margin: 0 0 .25rem 0; font-size: 2rem; color: #fff;}
      .hero p {margin: 0; font-size: 1.02rem; color: #e8f1f8;}
      .step {display:inline-block; padding:.15rem .6rem; margin-right:.4rem;
             border-radius: 999px; background:#e8f1f8; color:#0f3d5e;
             font-weight:600; font-size:.85rem;}
      .pill {display:inline-block; padding:.1rem .55rem; margin:.15rem .25rem .15rem 0;
             border-radius: 999px; font-size:.86rem; border:1px solid #c7d3de;}
      .pill-ok {background:#e7f5ec; border-color:#9bd3ae; color:#14532d;}
      .pill-maybe {background:#fff6e0; border-color:#e7c46a; color:#6b4a00;}
      .pill-gap {background:#fdecec; border-color:#e6a1a1; color:#7a1f1f;}
      .headline {padding: .9rem 1.1rem; border-left: 6px solid #1b6ca8;
                 background: rgba(27,108,168,.08); border-radius: 8px;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_api() -> CareerMatchingAPI:
    """Load the Step 5 API once per Streamlit session."""
    return CareerMatchingAPI(root=REPO_ROOT)


def format_pages(pages: list[int] | None) -> str:
    if not pages:
        return "—"
    return ", ".join(str(p) for p in pages)


def normalise_skill_key(skill: str) -> str:
    """Normalise a skill name for safe display-layer comparisons."""
    return " ".join(str(skill).strip().lower().split())


def display_priority_gaps(item: dict) -> list[str]:
    """Hide any gap that is already reported as a matched skill.

    Presentation-layer consistency check only; the raw JSON is unchanged.
    """
    matched_keys = {
        normalise_skill_key(s) for s in item.get("matched_skills", []) if str(s).strip()
    }
    clean, seen = [], set()
    for skill in item.get("priority_gaps", []):
        key = normalise_skill_key(skill)
        if not key or key in matched_keys or key in seen:
            continue
        seen.add(key)
        clean.append(skill)
    return clean


def covered_details(item: dict) -> list[dict]:
    return [d for d in item.get("skill_details", []) if d.get("status") == "covered"]


def split_confident_and_possible(item: dict) -> tuple[list[dict], list[dict]]:
    """Exact hits are confident; semantic-only hits are 'possibly covered'."""
    sure, maybe = [], []
    for d in covered_details(item):
        (maybe if d.get("evidence_source") == "semantic" else sure).append(d)
    return sure, maybe


def evidence_rows(details: list[dict]) -> pd.DataFrame:
    rows = []
    for d in details:
        level = d.get("coverage_level") or "covered"
        rows.append(
            {
                "Skill": d.get("skill", ""),
                "How it appears": BADGE.get(level, level.title()),
                "Found by": "Exact name" if d.get("evidence_source") == "exact" else "Meaning (semantic)",
                "Page(s)": format_pages(d.get("pages")),
                "Evidence sentence": d.get("evidence") or "—",
            }
        )
    return pd.DataFrame(rows)


def learning_rows(item: dict) -> pd.DataFrame:
    matched_keys = {
        normalise_skill_key(s) for s in item.get("matched_skills", []) if str(s).strip()
    }
    rows = []
    for rec in item.get("learning_recommendations", []):
        skill = rec.get("skill", "")
        if normalise_skill_key(skill) in matched_keys:
            continue
        rows.append(
            {
                "Priority": rec.get("priority"),
                "Skill to develop": skill,
                "Career demand": float(rec.get("demand_weight", 0.0)) * 100,
                "What to do": rec.get("suggested_action", ""),
            }
        )
    return pd.DataFrame(rows)


def gaps_csv(results: list[dict]) -> bytes:
    frames = []
    for item in results:
        df = learning_rows(item)
        if not df.empty:
            df.insert(0, "Career", item["career"])
            frames.append(df)
    out = pd.concat(frames) if frames else pd.DataFrame()
    return out.to_csv(index=False).encode("utf-8")


def pills(skills: list[str], css: str, symbol: str) -> str:
    return "".join(f'<span class="pill {css}">{symbol} {s}</span>' for s in skills)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
      <h1>🎓 Study-to-Career Matcher</h1>
      <p>Upload a unit outline and see which Data/AI careers its content lines up
      with, what is covered, and what to learn next.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    '<span class="step">1 Choose a PDF</span><span class="step">2 Pick a method</span>'
    '<span class="step">3 Read the results</span>',
    unsafe_allow_html=True,
)
st.info(
    "**Please read as:** a score shows how much of what employers ask for appears "
    "in this document. It is **not** proof you have the skills, and **not** the "
    "chance of getting a job. Experience and education also matter and are not measured here.",
    icon="ℹ️",
)

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Analysis settings")
    method = st.radio(
        "How should skills be found?",
        options=[EXACT_LABEL, HYBRID_LABEL],
        index=0,
        help="Choose the fast option first. You can run the deeper one afterwards to compare.",
    )
    st.caption(METHOD_HELP[method])
    use_semantic = method == HYBRID_LABEL
    top_k = st.slider("Careers to show", min_value=3, max_value=5, value=5)

    with st.expander("How to read the results"):
        st.markdown(
            "- **Match %** = share of the career's 30 most requested skills that "
            "this document covers, weighted by how often employers ask for each.\n"
            "- **Assessed / Taught / Mentioned** show how strongly the "
            "document covers a skill.\n"
            "- **? Possibly covered** skills come from the semantic method and "
            "need a quick check against the evidence sentence.\n"
            "- Scores within about 2 points of each other are effectively tied."
        )

    st.divider()
    st.caption(
        "Career demand comes from 688 U.S. job advertisements (five careers). "
        "The interface only displays results from the project's NLP pipeline."
    )

# ---------------------------------------------------------------------------
# Upload and analysis
# ---------------------------------------------------------------------------
col_up, col_sample = st.columns([3, 1])
with col_up:
    uploaded = st.file_uploader(
        "Upload one course or unit PDF",
        type=["pdf"],
        help="A subject outline, unit guide, handbook entry or learning-material PDF.",
    )
with col_sample:
    st.write("")
    st.write("")
    sample_clicked = st.button(
        "Try the sample outline",
        disabled=not SAMPLE_PDF.exists(),
        help="Runs the example unit outline used in the project report.",
    )

analyse_clicked = st.button(
    "Generate career matches",
    type="primary",
    disabled=uploaded is None and not sample_clicked,
)

if (analyse_clicked and uploaded is not None) or sample_clicked:
    source = uploaded if (analyse_clicked and uploaded is not None) else SAMPLE_PDF
    name = uploaded.name if source is uploaded else SAMPLE_PDF.name
    message = (
        "Reading the PDF and calculating career matches…"
        if not use_semantic
        else "Loading the language model (first run only), reading the PDF and "
        "calculating career matches…"
    )
    with st.spinner(message):
        try:
            if hasattr(source, "seek"):
                source.seek(0)
            results = get_api().recommend_from_pdf(
                source, use_semantic=use_semantic, top_k=top_k
            )
            st.session_state["results"] = results
            st.session_state["source_name"] = name
            st.session_state["method"] = method
        except ModuleNotFoundError as exc:
            st.session_state.pop("results", None)
            if use_semantic:
                st.error(
                    "The deeper method needs an extra install that is not on this "
                    "computer yet. Run `pip install sentence-transformers torch` "
                    "(about 2 GB), or choose the fast method. "
                    f"Missing module: {exc.name}"
                )
            else:
                st.error(f"A required library is missing: {exc.name}. Run `pip install -r step6_app/requirements.txt`.")
        except Exception as exc:  # user-facing app: report error without crashing page
            st.session_state.pop("results", None)
            st.error(
                "Could not read this file. Please check it is a text-based PDF "
                f"(not a scan) and try again. Details: {exc}"
            )

results = st.session_state.get("results")

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if results:
    st.divider()
    source_name = st.session_state.get("source_name", "uploaded PDF")
    used_method = st.session_state.get("method", EXACT_LABEL)
    st.subheader("Career match overview")
    st.caption(f"Document: **{source_name}** · Method: **{used_method}**")

    best = results[0]
    top_two_gap = (
        float(results[0]["match_percent"]) - float(results[1]["match_percent"])
        if len(results) > 1
        else 99.0
    )
    tie_note = (
        " The next career is within 2 points, so treat these as a tie."
        if top_two_gap < 2.0
        else ""
    )
    st.markdown(
        f'<div class="headline"><b>Closest fit: {best["career"]} '
        f'({float(best["match_percent"]):.1f}%).</b> This document covers '
        f'{best["n_covered_top_skills"]} of the {best["n_top_skills"]} skills '
        f"employers ask for most in this role.{tie_note}</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    n_semantic = sum(len(split_confident_and_possible(i)[1]) for i in results)
    if n_semantic:
        st.warning(
            "Some skills were found by meaning rather than by name and are marked "
            "**? possibly covered**. In our audit about 64% of such additions were "
            "correct, so check the evidence sentence before relying on them.",
            icon="⚠️",
        )

    metric_cols = st.columns(len(results))
    for col, item in zip(metric_cols, results):
        with col:
            st.metric(
                label=f"#{item['rank']} {item['career']}",
                value=f"{float(item['match_percent']):.1f}%",
                help=f"{item['n_covered_top_skills']} of {item['n_top_skills']} top skills covered; "
                f"based on {item['n_ads']} job ads.",
            )

    chart_df = pd.DataFrame(
        {
            "Career": [i["career"] for i in results],
            "Match (%)": [float(i["match_percent"]) for i in results],
            "Skills covered": [
                f"{i['n_covered_top_skills']} of {i['n_top_skills']}" for i in results
            ],
        }
    )
    base = alt.Chart(chart_df).encode(
        y=alt.Y("Career:N", title=None, sort=alt.SortField("Match (%)", order="descending")),
        x=alt.X("Match (%):Q", title="Match (%)", scale=alt.Scale(domain=[0, 100])),
    )
    bars = base.mark_bar(color="#1b6ca8").encode(
        tooltip=["Career:N", alt.Tooltip("Match (%):Q", format=".1f"), "Skills covered:N"]
    )
    labels = base.mark_text(align="left", dx=4).encode(text=alt.Text("Match (%):Q", format=".1f"))
    st.altair_chart(
        (bars + labels).properties(height=max(180, 42 * len(chart_df))),
        use_container_width=True,
    )

    st.subheader("Detailed recommendations")
    st.caption("Open a career to see what is covered, what is missing and the evidence.")
    for item in results:
        label = f"#{item['rank']} {item['career']} — {float(item['match_percent']):.1f}% match"
        with st.expander(label, expanded=item.get("rank") == 1):
            sure, maybe = split_confident_and_possible(item)
            gaps = display_priority_gaps(item)

            covered_n = int(item["n_covered_top_skills"])
            total_n = int(item["n_top_skills"])
            st.progress(
                covered_n / max(total_n, 1),
                text=f"{covered_n} of {total_n} of this career's most requested skills are covered",
            )

            left, right = st.columns(2)
            with left:
                st.markdown("#### Skills covered")
                if sure or maybe:
                    html = pills([d["skill"] for d in sure], "pill-ok", "✓")
                    html += pills([d["skill"] for d in maybe], "pill-maybe", "?")
                    st.markdown(html, unsafe_allow_html=True)
                    st.caption("✓ found by exact name  |  ? possibly covered (semantic)")
                else:
                    st.write("No covered skills were detected among this career's top skills.")
            with right:
                st.markdown("#### Biggest gaps")
                if gaps:
                    st.markdown(pills(gaps[:6], "pill-gap", "△"), unsafe_allow_html=True)
                    st.caption("△ requested by employers, not found in this document")
                else:
                    st.write("No priority gaps were identified.")

            st.markdown("#### Why this career matched")
            st.write(item.get("explanation", "No explanation available."))

            details = sure + maybe
            if details:
                with st.expander("Show the evidence from your PDF"):
                    st.caption(
                        "Each skill is traced to a page and sentence so you can check it."
                    )
                    st.dataframe(
                        evidence_rows(details),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Page(s)": st.column_config.TextColumn(width="small"),
                            "Evidence sentence": st.column_config.TextColumn(width="large"),
                        },
                    )

            learning = learning_rows(item)
            if not learning.empty:
                st.markdown("#### What to learn next")
                st.dataframe(
                    learning,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Priority": st.column_config.NumberColumn(width="small"),
                        "Career demand": st.column_config.ProgressColumn(
                            "Career demand (weighted)", min_value=0, max_value=100, format="%.0f%%"
                        ),
                    },
                )

    dl1, dl2, _ = st.columns([1, 1, 3])
    with dl1:
        st.download_button(
            "Download full results (JSON)",
            data=json.dumps(results, indent=2, ensure_ascii=False).encode("utf-8"),
            file_name="study_to_career_results.json",
            mime="application/json",
        )
    with dl2:
        st.download_button(
            "Download skill gaps (CSV)",
            data=gaps_csv(results),
            file_name="study_to_career_gaps.csv",
            mime="text/csv",
        )
else:
    st.caption("Choose a PDF (or try the sample outline), then select **Generate career matches**.")

# ---------------------------------------------------------------------------
# Footer / responsible-use note
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "UTS 36118 Applied NLP · AT2 Part B · Group 6. "
    "Explainable skill-overlap results from the team's NLP pipeline."
)
