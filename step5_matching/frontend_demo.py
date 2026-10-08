"""Minimal dynamic frontend demo for the Step 3 -> Step 4 -> Step 5 pipeline."""
from __future__ import annotations

import json

import streamlit as st

from frontend_api import CareerMatchingAPI


@st.cache_resource
def get_api() -> CareerMatchingAPI:
    return CareerMatchingAPI()


st.set_page_config(page_title="Study-to-Career Matcher", page_icon="🎓", layout="wide")
st.title("Study-to-Career Matcher")
st.caption("Upload one course PDF to calculate a new result. PDF coverage is not proof of personal mastery.")

uploaded = st.file_uploader("Upload a course PDF", type=["pdf"])
use_semantic = st.checkbox(
    "Use Step 4 semantic matching",
    value=False,
    help="The first run downloads and loads the sentence-transformer model, so it may take longer.",
)

if uploaded is not None and st.button("Generate career matches", type="primary"):
    with st.spinner("Extracting skills and calculating career matches..."):
        try:
            st.session_state.results = get_api().recommend_from_pdf(
                uploaded, use_semantic=use_semantic, top_k=5
            )
        except Exception as exc:
            st.error(f"Could not generate recommendations: {exc}")

results = st.session_state.get("results")
if results:
    for item in results:
        with st.container(border=True):
            left, right = st.columns([3, 1])
            left.subheader(f"#{item['rank']} {item['career']}")
            right.metric("Match", f"{item['match_percent']:.1f}%")
            st.write("**Matched skills:** " + (", ".join(item["matched_skills"]) or "None detected"))
            learning = [x["skill"] for x in item["learning_recommendations"]]
            st.write("**Priority learning skills:** " + (", ".join(learning) or "No priority gaps"))

    payload_bytes = json.dumps(results, indent=2, ensure_ascii=False).encode("utf-8")
    st.download_button(
        "Download this result as JSON",
        data=payload_bytes,
        file_name="latest_app_payload.json",
        mime="application/json",
    )
