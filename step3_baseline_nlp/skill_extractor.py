"""Step 3 - Baseline skill extraction with spaCy PhraseMatcher.

Pipeline
--------
raw text -> light preprocessing -> spaCy tokenisation -> PhraseMatcher (aliases from
skills_dictionary.csv) -> matched alias -> canonical skill via normalisation.py
-> de-duplicate per document (order of first appearance preserved).

The same ``extract_skills(text)`` function is meant to be reused on job advertisements
and on student study material, so both sides share identical logic.

Usage
-----
>>> from skill_extractor import extract_skills
>>> extract_skills("Strong Python, SQL and ML models on AWS.")
['Python', 'SQL', 'Machine Learning', 'AWS']
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

import pandas as pd
import spacy
from spacy.matcher import PhraseMatcher
from spacy.util import filter_spans

from normalisation import ALIAS_TO_CANONICAL, normalise_skill

HERE = Path(__file__).resolve().parent
DEFAULT_DICTIONARY = HERE / "skills_dictionary.csv"

# --------------------------------------------------------------------------- #
# Preprocessing
# --------------------------------------------------------------------------- #
_DASHES = dict.fromkeys(map(ord, "‐‑‒–—−"), "-")
_QUOTES = {ord("‘"): "'", ord("’"): "'", ord("“"): '"', ord("”"): '"'}
# sentence-final period glued to a token ("... and R.") would otherwise stay inside the token
_FINAL_DOT = re.compile(r"(?<=[A-Za-z0-9+#])\.(?=\s|$)")
# "/" glued to words ("Node.js/TypeScript", "R/Python") must be its own token
_SLASH = re.compile(r"\s*/\s*")
# commas/brackets glued to the next word ("C++,Go") hide the second skill from the tokenizer
_PUNCT = re.compile(r"\s*([,;:()\[\]{}\"|])\s*")
# trademark signs would otherwise be turned into letters by NFKC ("Spark\u2122" -> "SparkTM")
_MARKS = dict.fromkeys(map(ord, "\u2122\u00ae\u00a9"), " ")


def preprocess(text: str) -> str:
    """Normalise unicode/punctuation so aliases and text tokenise the same way.

    Applied identically to job text and to dictionary aliases. It never changes letter
    case (needed for the case-sensitive alias ``R``) and never removes words.
    """
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    text = str(text).translate(_MARKS)
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_DASHES).translate(_QUOTES)
    text = text.replace(" ", " ")
    text = _SLASH.sub(" / ", text)
    text = _PUNCT.sub(r" \1 ", text)
    text = _FINAL_DOT.sub(" .", text)
    return text


@dataclass(frozen=True)
class SkillMatch:
    canonical: str   # normalised skill, e.g. "Machine Learning"
    alias: str       # dictionary alias that fired, e.g. "ml models"
    text: str        # exact surface text in the document
    start: int       # char offsets in the *preprocessed* text
    end: int


class SkillExtractor:
    """Dictionary-driven, explainable skill extractor (baseline NLP method)."""

    def __init__(self, dictionary_path: "str | Path | pd.DataFrame" = DEFAULT_DICTIONARY,
                 resolve_overlaps: bool = False):
        """
        resolve_overlaps=False keeps every alias hit (e.g. "AWS Lambda" -> AWS Lambda *and*
        AWS), which is how Step 2's frequency tables were computed.
        resolve_overlaps=True keeps only the longest span at each position.
        """
        self.resolve_overlaps = resolve_overlaps
        self.nlp = spacy.blank("en")  # tokenizer only: no statistical model is needed
        if isinstance(dictionary_path, pd.DataFrame):   # e.g. dictionary + reviewed extra aliases
            dictionary = dictionary_path.copy()
        else:
            dictionary = pd.read_csv(dictionary_path, encoding="utf-8-sig")
        aliases = dictionary["alias"].astype(str).str.strip().unique()

        # Case-insensitive matcher for ordinary aliases; case-sensitive (ORTH) matcher for
        # aliases written with capitals (only the language "R"), so "r" in free text never fires.
        self._lower = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self._exact = PhraseMatcher(self.nlp.vocab, attr="ORTH")
        for alias in aliases:
            matcher = self._exact if alias != alias.lower() else self._lower
            matcher.add(alias, [self.nlp.make_doc(preprocess(alias))])

        # Guard: the CSV and normalisation.py must agree, otherwise Step 2 outputs are inconsistent.
        csv_map = dict(zip(dictionary["alias"].astype(str), dictionary["canonical_skill"].astype(str)))
        # (aliases added after Step 2 are absent from normalisation.py and are resolved via the CSV)
        bad = {a: (c, ALIAS_TO_CANONICAL.get(a)) for a, c in csv_map.items()
               if a in ALIAS_TO_CANONICAL and ALIAS_TO_CANONICAL[a] != c}
        if bad:
            raise ValueError(f"skills_dictionary.csv and normalisation.py disagree: {bad}")
        self._csv_map = csv_map
        self.alias_to_category = dict(zip(dictionary["canonical_skill"], dictionary["category"]))

    # ------------------------------------------------------------------ #
    def _find(self, doc) -> list[SkillMatch]:
        spans = []
        for matcher in (self._lower, self._exact):
            for match_id, start, end in matcher(doc):
                spans.append((doc[start:end], self.nlp.vocab.strings[match_id]))
        if self.resolve_overlaps and spans:
            keep = set(map(lambda s: (s.start, s.end), filter_spans([s for s, _ in spans])))
            spans = [(s, a) for s, a in spans if (s.start, s.end) in keep]
        spans.sort(key=lambda sa: (sa[0].start_char, -(sa[0].end_char - sa[0].start_char)))
        return [SkillMatch(self._canonical(alias), alias, span.text, span.start_char, span.end_char)
                for span, alias in spans]

    def _canonical(self, alias: str) -> str:
        """normalisation.py is the source of truth; reviewed extra aliases fall back to the CSV."""
        return normalise_skill(alias) if alias in ALIAS_TO_CANONICAL else self._csv_map[alias]

    @staticmethod
    def _dedupe(matches: Iterable[SkillMatch]) -> list[str]:
        seen, out = set(), []
        for m in matches:
            if m.canonical not in seen:
                seen.add(m.canonical)
                out.append(m.canonical)
        return out

    # ------------------------------------------------------------------ #
    def extract_with_evidence(self, text: str) -> list[SkillMatch]:
        """All matches (with alias and position) - for debugging and explainability."""
        return self._find(self.nlp(preprocess(text)))

    def extract_skills(self, text: str) -> list[str]:
        """Canonical skills in order of first appearance, de-duplicated."""
        return self._dedupe(self.extract_with_evidence(text))

    def extract_many(self, texts: Iterable[str], batch_size: int = 64) -> Iterator[list[SkillMatch]]:
        docs = self.nlp.pipe((preprocess(t) for t in texts), batch_size=batch_size)
        for doc in docs:
            yield self._find(doc)


# Module-level convenience API ------------------------------------------------
_default: SkillExtractor | None = None


def get_extractor() -> SkillExtractor:
    global _default
    if _default is None:
        _default = SkillExtractor()
    return _default


def extract_skills(text: str) -> list[str]:
    """Return canonical skills found in ``text`` (shared by job-side and student-side code)."""
    return get_extractor().extract_skills(text)
