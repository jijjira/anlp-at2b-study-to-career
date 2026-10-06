"""Student-side pipeline: PDF study material -> clean text -> canonical skills (with page evidence).

Uses the SAME dictionary-matching logic as the job-ad side (skill_extractor / skill_extractor_v2),
so a skill is recognised identically on both sides of the comparison.

>>> from extraction import extract_skills, analyse_study_material
>>> extract_skills("Strong Python and SQL")                      # raw text, baseline matcher
['Python', 'SQL']
>>> profile = analyse_study_material("unit_outline.pdf")        # PDF path, bytes or file object
>>> profile.skills["Python"]["pages"]
[2, 5]

Wording note for the UI: these are "skills covered by your study materials", not skills the
student has mastered.
"""
from __future__ import annotations

import collections
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from skill_extractor import extract_skills            # noqa: F401  (re-exported, baseline API)
from skill_extractor_v2 import RequirementAwareExtractor, UNLABELLED

HERE = Path(__file__).resolve().parent
EXTRA_ALIASES = HERE / "extra_aliases_reviewed.csv"

# --------------------------------------------------------------------------- #
# 1. PDF -> text
# --------------------------------------------------------------------------- #
_HYPHEN_BREAK = re.compile(r"(?<=[A-Za-z])-\n(?=[a-z])")          # "inter-\nnational" -> "international"
_PAGE_NUM = re.compile(r"^\s*(?:page\s*)?\d{1,4}(?:\s*(?:/|of)\s*\d{1,4})?\s*$", re.I)
_BULLET = re.compile(r"^\s*(?:[-•*·–▪●◦■□►]|\d{1,2}[.)])\s+")
_COLUMN_GAP = re.compile(r"\s{8,}")                                 # wide gap = another column or table cell
_SENT = re.compile(r"(?<=[a-z0-9)][.!?])\s+(?=[A-Z])")
_SOFT = re.compile(r"(?<![.:;!?])\n(?=[a-z(])")                   # line wrapped mid-sentence


def read_pdf_pages(source) -> list[str]:
    """Raw text of each page. `source` is a path, bytes, or a file-like object (e.g. Streamlit upload)."""
    import pymupdf                                                  # PyMuPDF
    if isinstance(source, (str, Path)):
        doc = pymupdf.open(str(source))
    else:
        data = source.read() if hasattr(source, "read") else bytes(source)
        doc = pymupdf.open(stream=data, filetype="pdf")
    with doc:
        return [page.get_text("text", sort=True) for page in doc]


def clean_pages(pages: list[str], repeat_share: float = 0.5) -> list[str]:
    """Remove running headers/footers and page numbers, repair hyphenation and soft line wraps.

    Lines (after stripping digits) that appear on >= `repeat_share` of pages (and on >= 3 pages)
    are treated as headers/footers. Soft wraps are joined so that "machine\\nlearning" can match.
    """
    norm = lambda l: re.sub(r"\s+", " ", re.sub(r"\d+", "#", l.strip().lower()))   # browser print headers pad with long runs of spaces
    counts = collections.Counter(norm(l) for p in pages for l in set(p.split("\n")) if l.strip())
    n = len(pages)
    boiler = {k for k, c in counts.items() if n >= 3 and c >= max(3, repeat_share * n) and len(k) < 120}
    out = []
    for p in pages:
        p = unicodedata.normalize("NFKC", p)
        p = _HYPHEN_BREAK.sub("", p)
        lines = [c.strip() for l in p.split("\n") if l.strip() and norm(l) not in boiler and not _PAGE_NUM.match(l)
                 for c in _COLUMN_GAP.split(l) if c.strip()]          # table cells and side columns become separate lines
        text = "\n".join(lines)
        text = _SOFT.sub(" ", text)
        text = _SENT.sub("\n", text)       # one sentence per line, so the ambiguity guard works per sentence
        out.append(text)
    return out


# --------------------------------------------------------------------------- #
# 1b. Coverage strength: is a skill assessed, taught, or only mentioned?
# --------------------------------------------------------------------------- #
ASSESSED, TAUGHT, MENTIONED = "assessed", "taught", "mentioned"
COVERAGE_WEIGHTS = {ASSESSED: 1.0, TAUGHT: 0.75, MENTIONED: 0.5}      # hyper-parameters
_LEVEL_ORDER = [ASSESSED, TAUGHT, MENTIONED]
_H_ASSESS = re.compile(r"^\s*(?:assessments?|assessment (?:tasks?|items?|overview)|assignments?|learning outcomes?|"
                       r"(?:course|subject|unit) (?:learning )?outcomes?|learning objectives?|objectives?|graduate attributes?|"
                       r"capstone|final project|exams?)\b", re.I)
_H_TAUGHT = re.compile(r"^\s*(?:week\s*\d+|weekly (?:schedule|topics?|outline)|schedule|topics?|course content|content|syllabus|"
                       r"lectures?|modules?|tutorials?|labs?|teaching (?:and learning )?(?:plan|schedule))\b", re.I)
_H_OTHER = re.compile(r"^\s*(?:overview|unit overview|prerequisites?|about|introduction|description|resources?|readings?|"
                      r"textbooks?|contact|policies|academic integrity)\b", re.I)
_ASSESS_CUE = re.compile(r"\b(assess\w*|assignments?|exams?|quiz(?:zes)?|graded|marks?|submit\w*|"
                         r"students will (?:be able to|demonstrate)|upon completion|by the end of (?:this|the) (?:unit|subject|course))\b", re.I)


_TAUGHT_CUE = re.compile(r"\b(?:topics? (?:covered|include|to be covered)|(?:this|the) (?:course|subject|unit) (?:covers?|introduces?)|"
                         r"students (?:will )?(?:learn|study|explore)|we (?:cover|study))\b", re.I)


def tag_lines(text: str) -> dict[int, str]:
    """line index -> coverage level for one page of study material (header state machine + line cues).

    Headings are short lines (<= 8 words, no final full stop). Skills under a learning-outcomes or assessment
    heading, or in a sentence about assessment, count as ASSESSED; skills in weekly schedule/topic sections as
    TAUGHT; everything else (overview, prerequisites, unlabelled text) as MENTIONED.
    """
    state, out = MENTIONED, {}
    for i, raw in enumerate(text.split("\n")):
        line = raw.strip()
        if not line:
            continue
        is_heading = len(line.split()) <= 8 and not line.endswith(".")
        if is_heading:
            if _H_ASSESS.match(line):
                state = ASSESSED
            elif _H_TAUGHT.match(line):
                state = TAUGHT
            elif _H_OTHER.match(line):
                state = MENTIONED
        level = state
        if not is_heading and _ASSESS_CUE.search(line):
            level = ASSESSED
        elif not is_heading and level == MENTIONED and _TAUGHT_CUE.search(line):
            level = TAUGHT                                     # "Topics covered include ..." is teaching, not a passing mention
        out[i] = level
    return out


# --------------------------------------------------------------------------- #
# 2. text -> skills
# --------------------------------------------------------------------------- #
@dataclass
class StudyProfile:
    skills: dict = field(default_factory=dict)      # canonical -> {mentions, pages, category, evidence}
    n_pages: int = 0
    n_chars: int = 0
    warnings: list = field(default_factory=list)

    def strengths(self) -> dict:
        """canonical skill -> coverage weight (assessed 1.0, taught 0.75, mentioned 0.5)."""
        return {k: v["weight"] for k, v in self.skills.items()}

    def names(self) -> list[str]:
        """Skills ordered by number of mentions (most covered first)."""
        return sorted(self.skills, key=lambda s: (-self.skills[s]["mentions"], s))


_extractor: RequirementAwareExtractor | None = None


# Lines that name a skill without saying it is taught: later study, requisites, equivalent/excluded courses.
_NOT_COVERED = re.compile(r"\b(?:further (?:learning|study)|advanced topics such as|assumed knowledge|prerequisites?|"
                          r"co-?requisites?|prohibitions?|equivalent courses?|exclusion courses?|prepares? (?:students )?for|"
                          r"leads? (?:on )?to|generative ai|ai (?:allowed|permitted|use|tools?)|(?:use|using) (?:of )?(?:generative )?(?:artificial intelligence|ai)\b|generative artificial intelligence|academic integrity|"
                          r"open assessments?|secure assessments?)\b", re.I)
_AI_POLICY = re.compile(r"prohibit|allowed|permitted|secure|invigilat|supervised|performance task|assessments?|acknowledg|\d\s?%|hours?", re.I)   # assessment-policy tables ("AI allowed")
_COURSE_CODE = re.compile(r"\b[A-Z]{3,4}\s?\d{4}\b|\b\d{6}\b")                       # e.g. MATH5836, WENG3007, COMP2123


def get_student_extractor() -> RequirementAwareExtractor:
    """Same matcher + reviewed aliases + plural variants as the job side; no ad-section tagging."""
    global _extractor
    if _extractor is None:
        _extractor = RequirementAwareExtractor(extra_aliases_path=EXTRA_ALIASES, tag_context=False,
                                               expand_morphology=True)
    return _extractor


def analyse_pages(pages: list[str], extractor: RequirementAwareExtractor | None = None) -> StudyProfile:
    ext = extractor or get_student_extractor()
    prof = StudyProfile(n_pages=len(pages), n_chars=sum(map(len, pages)))
    if prof.n_chars < 200 * max(1, len(pages)) * 0.1:
        prof.warnings.append("Very little text was found; the PDF may be scanned images (OCR is not supported).")
    for pno, text in enumerate(pages, start=1):
        levels = tag_lines(text)
        for m in ext.analyse(text):
            if _NOT_COVERED.search(m.line) or _COURSE_CODE.search(m.line) or \
                    (m.canonical in ("Artificial Intelligence", "Generative AI") and (_AI_POLICY.search(m.line) or len(m.line.strip()) <= 3)):
                continue                                              # a catalogue reference, not coverage
            level = levels.get(m.line_no, MENTIONED)
            d = prof.skills.setdefault(m.canonical, {"mentions": 0, "pages": [], "level": level,
                                                      "category": ext.alias_to_category.get(m.canonical, ""),
                                                      "evidence": m.line.strip()[:200]})
            d["mentions"] += 1
            if pno not in d["pages"]:
                d["pages"].append(pno)
            if _LEVEL_ORDER.index(level) < _LEVEL_ORDER.index(d["level"]):      # keep the strongest evidence
                d["level"], d["evidence"] = level, m.line.strip()[:200]
    for d in prof.skills.values():
        d["weight"] = COVERAGE_WEIGHTS[d["level"]]
    return prof


def analyse_study_material(source, extractor: RequirementAwareExtractor | None = None) -> StudyProfile:
    """PDF (path / bytes / file object) -> StudyProfile of skills covered by the material."""
    return analyse_pages(clean_pages(read_pdf_pages(source)), extractor)


def analyse_text(text: str, extractor: RequirementAwareExtractor | None = None) -> StudyProfile:
    """Same output for pasted text or .txt / .md study notes."""
    return analyse_pages(clean_pages([text]), extractor)
