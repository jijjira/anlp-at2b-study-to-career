"""Final Streamlit interface for the Study-to-Career project (Student 6).

Run from the repository root with:
    streamlit run step6_app/app.py

The app does not reimplement the NLP or matching logic. It calls the Step 5
frontend API, which in turn runs the Step 3 exact extractor and (optionally)
the Step 4 semantic extractor before calculating Step 5 career matches.
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


# ---------------------------------------------------------------------------
# Page configuration and helpers
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Study-to-Career Matcher",
    page_icon="🎓",
    layout="wide",
)


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

    This is a presentation-layer consistency check only. It does not modify
    the upstream Step 5 output or the downloaded raw JSON results.
    """
    matched_keys = {
        normalise_skill_key(skill)
        for skill in item.get("matched_skills", [])
        if str(skill).strip()
    }

    clean_gaps = []
    seen = set()
    for skill in item.get("priority_gaps", []):
        key = normalise_skill_key(skill)
        if not key or key in matched_keys or key in seen:
            continue
        seen.add(key)
        clean_gaps.append(skill)
    return clean_gaps


def covered_skill_rows(item: dict) -> pd.DataFrame:
    rows = []
    for detail in item.get("skill_details", []):
        if detail.get("status") != "covered":
            continue
        rows.append(
            {
                "Skill": detail.get("skill", ""),
                "Coverage": detail.get("coverage_level") or "covered",
                "Source": detail.get("evidence_source") or "—",
                "Page(s)": format_pages(detail.get("pages")),
                "Evidence": detail.get("evidence") or "—",
            }
        )
    return pd.DataFrame(rows)


def learning_rows(item: dict) -> pd.DataFrame:
    """Prepare learning recommendations for user-facing display."""
    matched_keys = {
        normalise_skill_key(skill)
        for skill in item.get("matched_skills", [])
        if str(skill).strip()
    }

    rows = []
    for rec in item.get("learning_recommendations", []):
        skill = rec.get("skill", "")
        if normalise_skill_key(skill) in matched_keys:
            continue

        demand_weight = float(rec.get("demand_weight", 0.0))
        rows.append(
            {
                "Priority": rec.get("priority"),
                "Skill to develop": skill,
                "Career demand": f"{demand_weight * 100:.1f}%",
                "Suggested action": rec.get("suggested_action", ""),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🎓 Study-to-Career Matcher")
st.markdown(
    "Upload a university study-material PDF to compare the **skills covered by "
    "the document** with skill demand in Data/AI job advertisements."
)
st.info(
    "**Interpretation:** detected skills indicate coverage in the uploaded material, "
    "not proof that the student has personally mastered those skills. Career results "
    "are skill-based matches, not definitive career decisions.",
    icon="ℹ️",
)

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Analysis settings")
    method = st.radio(
        "Skill extraction method",
        options=[
            "Exact keyword matching (Baseline)",
            "Hybrid semantic matching",
        ],
        index=0,
        help=(
            "Exact keyword matching uses the dictionary/phrase-matching baseline. "
            "Hybrid semantic matching also uses the Step 4 sentence-transformer model "
            "to capture semantically related skill expressions, and may take longer "
            "on the first run."
        ),
    )
    use_semantic = method == "Hybrid semantic matching"
    top_k = st.slider("Number of career results", min_value=3, max_value=5, value=5)

    st.divider()
    st.caption(
        "Career demand profiles are derived from the project's job-ad dataset. "
        "The interface only visualises results produced by the existing NLP and matching pipeline."
    )

# ---------------------------------------------------------------------------
# Upload and analysis
# ---------------------------------------------------------------------------
uploaded = st.file_uploader(
    "Upload one course or unit PDF",
    type=["pdf"],
    help="Examples include a subject outline, unit guide, handbook or learning-material PDF.",
)

analyse_clicked = st.button(
    "Generate career matches",
    type="primary",
    disabled=uploaded is None,
    use_container_width=False,
)

if analyse_clicked and uploaded is not None:
    with st.spinner(
        "Extracting study skills and calculating career matches..."
        if not use_semantic
        else "Loading semantic model, extracting study skills and calculating career matches..."
    ):
        try:
            uploaded.seek(0)
            results = get_api().recommend_from_pdf(
                uploaded,
                use_semantic=use_semantic,
                top_k=top_k,
            )
            st.session_state["results"] = results
            st.session_state["source_name"] = uploaded.name
            st.session_state["method"] = method
        except Exception as exc:  # user-facing app: report error without crashing page
            st.session_state.pop("results", None)
            st.error(f"Could not generate recommendations: {exc}")

results = st.session_state.get("results")

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if results:
    st.divider()
    source_name = st.session_state.get("source_name", "uploaded PDF")
    used_method = st.session_state.get("method", "Exact keyword matching (Baseline)")
    st.subheader("Career match overview")
    st.caption(f"Document: **{source_name}** · Method: **{used_method}**")

    # Top metrics
    metric_cols = st.columns(len(results))
    for col, item in zip(metric_cols, results):
        with col:
            st.metric(
                label=f"#{item['rank']} {item['career']}",
                value=f"{float(item['match_percent']):.1f}%",
            )

    # Comparison chart: explicitly sorted by match percentage, highest first.
    chart_df = pd.DataFrame(
        {
            "Career": [item["career"] for item in results],
            "Match (%)": [float(item["match_percent"]) for item in results],
        }
    )

    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "Match (%):Q",
                title="Match (%)",
                scale=alt.Scale(domain=[0, max(100, float(chart_df["Match (%)"].max()) + 5)]),
            ),
            y=alt.Y(
                "Career:N",
                title=None,
                sort=alt.SortField(field="Match (%)", order="descending"),
            ),
            tooltip=[
                alt.Tooltip("Career:N", title="Career"),
                alt.Tooltip("Match (%):Q", title="Match", format=".1f"),
            ],
        )
        .properties(height=max(180, 42 * len(chart_df)))
    )
    st.altair_chart(chart, use_container_width=True)

    st.subheader("Detailed recommendations")
    for item in results:
        label = f"#{item['rank']} {item['career']} — {float(item['match_percent']):.1f}% match"
        with st.expander(label, expanded=item.get("rank") == 1):
            matched = item.get("matched_skills", [])
            gaps = display_priority_gaps(item)

            left, right = st.columns(2)
            with left:
                st.markdown("#### Skills covered")
                if matched:
                    st.write(" · ".join(f"✅ {skill}" for skill in matched))
                else:
                    st.write("No matched skills were detected among this career's highest-demand skills.")

            with right:
                st.markdown("#### Priority gaps")
                if gaps:
                    st.write(" · ".join(f"△ {skill}" for skill in gaps[:5]))
                else:
                    st.write("No priority gaps were identified.")

            st.markdown("#### Why this career matched")
            st.write(item.get("explanation", "No explanation available."))

            covered = covered_skill_rows(item)
            if not covered.empty:
                with st.expander("View evidence from the uploaded PDF"):
                    st.caption(
                        "Evidence is reported by the upstream study-material extraction pipeline."
                    )
                    st.dataframe(covered, use_container_width=True, hide_index=True)

            learning = learning_rows(item)
            if not learning.empty:
                st.markdown("#### Suggested skills to develop")
                st.dataframe(learning, use_container_width=True, hide_index=True)

    # Keep the raw upstream results available for transparency/reproducibility.
    payload_bytes = json.dumps(results, indent=2, ensure_ascii=False).encode("utf-8")
    st.download_button(
        "Download results as JSON",
        data=payload_bytes,
        file_name="study_to_career_results.json",
        mime="application/json",
    )

else:
    st.caption("Upload a PDF and select **Generate career matches** to see results.")

# ---------------------------------------------------------------------------
# Footer / responsible-use note
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "UTS 36118 Applied NLP · AT2 Part B · Group 6. "
    "The app presents explainable skill-overlap results from the team's existing NLP pipeline."
)
