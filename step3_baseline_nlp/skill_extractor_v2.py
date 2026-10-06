"""Step 3+ - Requirement-aware skill extraction ("Baseline++").

Extends the PhraseMatcher baseline (skill_extractor.py) with three ideas:

1. Requirement-strength tagging. A job ad is segmented into sections (requirements, preferred,
   responsibilities, company blurb ...). Every skill mention is tagged with the section it appears
   in, so we can tell *must-have* from *nice-to-have* from *company boilerplate* ("founded by the
   creators of Apache Spark" is not a demand for Spark).
2. Context disambiguation. URLs/e-mails are removed and ambiguous lowercase aliases ("spark",
   "hive", ...) only count when the line also contains another known skill.
3. Optional reviewed extra aliases (from the dictionary-discovery step) merged at load time.

Everything is rule-based and explainable: each decision can be traced to a line and a cue.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from skill_extractor import DEFAULT_DICTIONARY, SkillExtractor

# --------------------------------------------------------------------------- #
# Section / strength lexicon
# --------------------------------------------------------------------------- #
REQUIRED, DUTY, PREFERRED, UNLABELLED, COMPANY = "required", "duty", "preferred", "unlabelled", "company"
PRIORITY = [REQUIRED, DUTY, PREFERRED, UNLABELLED, COMPANY]          # strongest evidence first

# default weights (hyper-parameters; see the sensitivity analysis in the notebook)
DEFAULT_WEIGHTS = {REQUIRED: 1.0, DUTY: 0.75, PREFERRED: 0.5, UNLABELLED: 0.5, COMPANY: 0.0}

_H = lambda s: re.compile(rf"^\s*(?:{s})\b", re.I)
HEADER_PATTERNS = [
    # order matters: first match wins
    (PREFERRED, _H(r"preferred|nice[- ]to[- ]have|bonus|extra credit|desirable|good to have|"
                   r"it'?s a plus|a plus|ideal(ly)?|strong candidates (may|might) also|even better")),
    (REQUIRED,  _H(r"required|requirements?|(minimum|basic|key|essential|must[- ]have) (qualifications?|requirements?|skills?)|"
                   r"qualifications?|must[- ]have|what you('|’)?ll need|what you need|what you bring|what you have|"
                   r"you have|you('|’)?ll have|you are|about you|who you are|who you('|’)?re|"
                   r"what we('|’)?re looking for|what we look for|you might thrive|skills? (and|&) experience|"
                   r"experience|your background|ideal candidate|the ideal|minimum education|"
                   r"required field|minimum years")),
    (DUTY,      _H(r"responsibilit(y|ies)|key responsibilit|what you('|’)?ll do|what you will do|in this role|"
                   r"you will|you('|’)?ll|about the (role|team|position|job|internship)|the role|the opportunity|"
                   r"your (impact|role|mission)|day[- ]to[- ]day|what (the )?(job|role) involves|duties|"
                   r"the team|team overview|job description|position summary|overview")),
    (COMPANY,   _H(r"about (?!the (role|team|position|job|internship)\b|you\b)|who we are|our (mission|story|values|culture|company|"
                   r"commitment|approach|benefits)|why (join|work|us)|benefits|perks|compensation|salary|pay (range|transparency)|"
                   r"annual salary|what we offer|we offer|equal (employment )?opportunit|diversity|privacy|accommodations?|"
                   r"how we('|’)?re different|logistics|visa|location|work (location|arrangement)|legal|disclaimer|eeo|"
                   r"applicant|recruitment|life at|culture|company (overview|description)|compliance|please note|"
                   r"for additional information|for more information|protecting yourself|"
                   r"us salary|salary range|total rewards|what makes us|our team and culture|notice (for|to)|automated employment|"
                   r"ai (use|policy|usage)|use of ai|how we use ai")),
]
# sentence-level cue that downgrades a line to "preferred" even inside a requirements section
PREFERRED_CUE = re.compile(
    r"\b(preferred|nice[- ]to[- ]have|nice to have|a plus|is a plus|are a plus|bonus|desirable|ideally|good to have|"
    r"would be (a )?(plus|great|nice|beneficial|an advantage)|an advantage|beneficial|not required|but not required|"
    r"familiarity with|exposure to)\b", re.I)
# Line-level cues used when no header has been seen (or the last header was a company one) -- many ads
# put requirement bullets under headers we do not know ("Technical expertise", "Skills", ...).
REQUIRED_CUE = re.compile(r"\b(experience (with|in|using|building|developing|designing|working)|proficien\w+|expertise|"
                          r"familiar(ity)? with|knowledge of|hands[- ]on|years of|skilled in|strong (understanding|background)|"
                          r"possess|solid understanding|working knowledge|track record)\b", re.I)
DUTY_CUE = re.compile(r"^(?:as an? [^,]{0,60},\s*)?(you('|’)?ll|you will|we are looking for|we('|’)?re looking for|"
                      r"design|build|develop|define|implement|lead|own|drive|collaborate|partner|create|deliver|maintain|"
                      r"architect|shape|represent|help|work with|work closely|contribute|ship|deploy|optimi[sz]e|analy[sz]e|"
                      r"conduct|support|manage|mentor|research)\b", re.I)
_BULLET = re.compile(r"^\s*[-•*·–▪●◦]\s*")
_URL = re.compile(r"https?://\S+|www\.\S+|\b[\w.+-]+@[\w-]+\.[\w.-]+\b", re.I)

# ambiguous lowercase aliases: only count when the *same line* has another known skill, or the
# surface form is capitalised / part of a longer unambiguous phrase
LIST_ONLY_ALIASES = {"Go", "Ray"}   # common words/names: count only when another skill is in the same line
AMBIGUOUS_ALIASES = {"spark", "hive", "presto", "jax", "ner", "eda", "elt", "flink", "git", "trino", "airflow"}


def classify_header(line: str):
    """Return (strength, remainder) if the line opens a section, else None.

    A header is a short line (<= 80 chars) that starts with a cue phrase and is not a sentence.
    The remainder is any text after "Cue:" so inline headers such as "Requirements: Python, SQL" work.
    """
    raw = _BULLET.sub("", line).strip()
    if not raw or len(raw) > 80 and ":" not in raw[:60]:
        return None
    head, sep, rest = raw.partition(":")
    head_clean = head.strip()
    short = len(head_clean) <= 80 and len(head_clean.split()) <= 10
    if not short:
        return None
    for label, pat in HEADER_PATTERNS:
        if pat.match(head_clean):
            # a full sentence that merely *starts* with a cue word ("You will build ...") is not a header
            if not sep and (head_clean.endswith(".") or len(head_clean.split()) > 4):
                return None   # a bare header is short ("Requirements"); "Experience with Spark, SQL ..." is a sentence
            if sep and len(head_clean.split()) > 7:
                return None
            return label, rest.strip()
    return None


@dataclass(frozen=True)
class ContextMatch:
    canonical: str
    alias: str
    text: str
    line_no: int
    strength: str       # required | duty | preferred | unlabelled | company
    line: str


class RequirementAwareExtractor:
    def __init__(self, dictionary_path=DEFAULT_DICTIONARY, extra_aliases_path=None,
                 weights=None, guard_ambiguous: bool = True, tag_context: bool = True,
                 expand_morphology: bool = False):
        """tag_context=False disables section tagging (everything = 'unlabelled'); used for ablations."""
        dictionary = pd.read_csv(dictionary_path, encoding="utf-8-sig")
        if extra_aliases_path is not None and Path(extra_aliases_path).exists():
            extra = pd.read_csv(extra_aliases_path, encoding="utf-8-sig")
            dictionary = pd.concat([dictionary, extra[dictionary.columns.intersection(extra.columns)]],
                                   ignore_index=True).drop_duplicates(["canonical_skill", "alias"])
        if expand_morphology:
            dictionary = self._with_plural_variants(dictionary)
        self.base = SkillExtractor(dictionary)
        self.weights = dict(DEFAULT_WEIGHTS if weights is None else weights)
        self.guard_ambiguous = guard_ambiguous
        self.tag_context = tag_context
        self.alias_to_category = self.base.alias_to_category

    @staticmethod
    def _with_plural_variants(dictionary: pd.DataFrame) -> pd.DataFrame:
        """Add singular/plural variants of the LAST word of each lowercase alias ("a/b test" -> "a/b tests").

        Job ads inflect skill names ("A/B tests", "feature store"/"feature stores"); a lemma-free matcher
        misses them. This keeps matching transparent (no statistical model) and maps to the same canonical.
        """
        have = set(dictionary["alias"])
        rows = []
        for _, r in dictionary.iterrows():
            a = str(r["alias"])
            if a != a.lower() or len(a) < 5:
                continue
            v = a[:-1] if a.endswith("s") and not a.endswith("ss") else a + "s"
            if v not in have:
                have.add(v)
                rows.append({**r.to_dict(), "alias": v})
        return pd.concat([dictionary, pd.DataFrame(rows)], ignore_index=True) if rows else dictionary

    # ------------------------------------------------------------------ #
    def segment(self, text: str):
        """Yield (line_no, line, strength) for every non-empty line of the ad."""
        state = UNLABELLED
        for i, raw in enumerate(str(text).split("\n")):
            line = raw.strip()
            if not line:
                continue
            if not self.tag_context:
                yield i, line, UNLABELLED
                continue
            hdr = classify_header(line)
            if hdr:
                state, rest = hdr
                line = rest            # inline header: keep the text after the colon, if any
                if not line:
                    continue
            strength = state
            if state in (UNLABELLED, COMPANY) and not hdr:
                body = _BULLET.sub("", line)
                if REQUIRED_CUE.search(body):
                    strength = REQUIRED
                elif DUTY_CUE.match(body):
                    strength = DUTY
            if strength in (REQUIRED, DUTY, UNLABELLED) and PREFERRED_CUE.search(line):
                strength = PREFERRED   # "... is a plus" even inside a requirements list
            yield i, line, strength

    def analyse(self, text: str) -> list[ContextMatch]:
        segs = [(i, _URL.sub(" ", line), s) for i, line, s in self.segment(text)]
        out: list[ContextMatch] = []
        for (i, line, strength), matches in zip(segs, self.base.extract_many([l for _, l, _ in segs])):
            if self.guard_ambiguous and matches:
                n_known = len({m.canonical for m in matches})
                matches = [m for m in matches
                           if not (n_known < 2 and (m.alias in LIST_ONLY_ALIASES or
                                   (m.alias in AMBIGUOUS_ALIASES and m.text == m.text.lower())))]
            out += [ContextMatch(m.canonical, m.alias, m.text, i, strength, line) for m in matches]
        return out

    # ------------------------------------------------------------------ #
    def skill_strengths(self, text: str) -> dict[str, str]:
        """canonical skill -> strongest evidence class (required > duty > preferred > unlabelled > company)."""
        best: dict[str, str] = {}
        order: list[str] = []
        for m in self.analyse(text):
            if m.canonical not in best:
                best[m.canonical] = m.strength
                order.append(m.canonical)
            elif PRIORITY.index(m.strength) < PRIORITY.index(best[m.canonical]):
                best[m.canonical] = m.strength
        return {k: best[k] for k in order}

    def extract_skills(self, text: str, mode: str = "demand") -> list[str]:
        """mode='demand' drops skills that only occur in company/benefit boilerplate; 'all' keeps them."""
        s = self.skill_strengths(text)
        return [k for k, v in s.items() if mode == "all" or v != COMPANY]

    def extract_weighted(self, text: str) -> dict[str, float]:
        return {k: self.weights[v] for k, v in self.skill_strengths(text).items() if self.weights[v] > 0}
