"""Small integration API for the Streamlit frontend.

Typical use::

    from frontend_api import match_uploaded_pdf

    results = match_uploaded_pdf(uploaded_pdf)

``results`` is a JSON-safe list of five career cards.  Career demand profiles
come from the job advertisements and stay fixed; study coverage is recalculated
for every uploaded PDF.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

try:  # package import (from step5_matching.frontend_api ...)
    from .matching import (
        build_career_profiles,
        recommend_for_frontend,
        study_coverage_from_hits,
        study_coverage_from_profile,
    )
except ImportError:  # direct import after adding step5_matching/ to sys.path
    from matching import (
        build_career_profiles,
        recommend_for_frontend,
        study_coverage_from_hits,
        study_coverage_from_profile,
    )


class CareerMatchingAPI:
    """Convert one new PDF or skill profile into frontend-ready results."""

    def __init__(self, root: str | Path | None = None, device: str | None = None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[1]
        self.device = device
        self._semantic_components = None
        self.career_profiles = self._load_career_profiles()

    def _load_career_profiles(self) -> pd.DataFrame:
        cached = self.root / "step5_matching" / "outputs" / "career_profiles.csv"
        if cached.exists():
            return pd.read_csv(cached)
        jobs = pd.read_csv(self.root / "step1_data" / "job_cleaned.csv")
        hits = pd.read_csv(
            self.root / "step4_semantic" / "results" / "hybrid_job_skills" / "job_skills_hybrid_long.csv"
        )
        return build_career_profiles(hits, jobs)

    def recommend_from_profile(self, profile, top_k: int = 5, top_n: int = 30) -> list[dict]:
        """Use a Step 3/4 ``StudyProfile`` and return new career results."""
        study = study_coverage_from_profile(profile)
        return recommend_for_frontend(study, self.career_profiles, top_k=top_k, top_n=top_n)

    def recommend_from_hits(self, hits: pd.DataFrame | str | Path,
                            top_k: int = 5, top_n: int = 30) -> list[dict]:
        """Use Step 3/4 long-form hits (unit_id, skill, source, page, level, evidence)."""
        frame = pd.read_csv(hits) if isinstance(hits, (str, Path)) else hits
        study = study_coverage_from_hits(frame)
        return recommend_for_frontend(study, self.career_profiles, top_k=top_k, top_n=top_n)

    def _load_exact_extractor(self):
        step3 = self.root / "step3_baseline_nlp"
        if str(step3) not in sys.path:
            sys.path.insert(0, str(step3))
        from extraction import analyse_study_material
        return analyse_study_material

    def _load_semantic_components(self):
        if self._semantic_components is not None:
            return self._semantic_components
        step3 = self.root / "step3_baseline_nlp"
        step4 = self.root / "step4_semantic"
        for folder in (step3, step4):
            if str(folder) not in sys.path:
                sys.path.insert(0, str(folder))
        from data_access import load_context
        from experiments import Runner
        from corpus_extract import build_hybrid, load_final
        from curriculum_semantic import analyse_study_material_semantic

        ctx = load_context(step3)
        runner = Runner(ctx, device=self.device)
        hybrid = build_hybrid(runner, load_final())
        self._semantic_components = (step3, hybrid, analyse_study_material_semantic)
        return self._semantic_components

    @staticmethod
    def _rewind(source) -> None:
        if hasattr(source, "seek"):
            source.seek(0)

    def recommend_from_pdf(self, source, use_semantic: bool = False,
                           top_k: int = 5, top_n: int = 30) -> list[dict]:
        """Run a new PDF through Step 3 (+ optional Step 4), then Step 5.

        ``source`` can be a path, bytes, or a Streamlit ``UploadedFile``.
        The semantic model is loaded lazily on the first hybrid request.
        """
        self._rewind(source)
        if use_semantic:
            step3, hybrid, analyse_semantic = self._load_semantic_components()
            profile = analyse_semantic(
                source,
                step3,
                hybrid.space,
                hybrid.encoder,
                hybrid.decision,
                hybrid.granularity,
            )
        else:
            profile = self._load_exact_extractor()(source)
        return self.recommend_from_profile(profile, top_k=top_k, top_n=top_n)

    @staticmethod
    def save_json(results: list[dict], destination: str | Path) -> Path:
        """Save one request's results when a file is preferred."""
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        return path


def match_uploaded_pdf(uploaded_pdf, use_semantic: bool = False) -> list[dict]:
    """One-call frontend interface: uploaded PDF -> five career results."""
    return CareerMatchingAPI().recommend_from_pdf(uploaded_pdf, use_semantic=use_semantic)

