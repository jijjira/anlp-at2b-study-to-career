"""Step 4 - Semantic skill extraction (Sentence Transformers) layered on the Step 3 "Baseline++".

Idea
----
The exact matcher (Step 3) finds a skill only when the ad/unit uses a dictionary alias. Many demanded skills are
*implied* ("measure how well the model generalises" -> Model Evaluation; "build dashboards" -> Data Visualization).
We embed (a) every ad *unit* (line, clause or window, never company boilerplate) and (b) a short text prototype for
every dictionary skill, and add a skill when a unit is similar enough to one of its prototypes.

Design choices (each is an ablation in experiments.py):
  * Hybrid: exact matches are kept, semantic evidence only ADDS skills the exact matcher did not find.
  * Units come from the Step 3 section segmenter, so company/benefit text never produces semantic hits and
    every semantic hit inherits a requirement strength (required / duty / preferred) like exact hits.
  * Optional per-skill z-normalisation against unlabelled ad units removes "hub" skills that are close to
    everything (a hubness correction).
  * The decision rule (threshold, optional margin below the unit's best skill) is separate from the scores, so one
    set of similarity matrices serves a whole threshold sweep.

Public API (drop-in compatible with RequirementAwareExtractor):
    HybridExtractor.extract_skills(text)     -> list[str]
    HybridExtractor.extract_weighted(text)   -> {skill: demand weight}
    HybridExtractor.skill_strengths(text)    -> {skill: strength class}   (what alignment.job_strengths calls)
    HybridExtractor.analyse(text)            -> list[Evidence]            (explainable: unit, similarity, source)
"""
from __future__ import annotations

import pickle
import re
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

import config

REQUIRED, DUTY, PREFERRED, UNLABELLED, COMPANY = "required", "duty", "preferred", "unlabelled", "company"
FALLBACK_WEIGHTS = {REQUIRED: 1.0, DUTY: 0.75, PREFERRED: 0.5, UNLABELLED: 0.5, COMPANY: 0.0}

_URL = re.compile(r"https?://\S+|www\.\S+|\b[\w.+-]+@[\w-]+\.[\w.-]+\b", re.I)
_BULLET = re.compile(r"^\s*[-•*·–▪●◦■□►]\s*")
_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
_CLAUSE = re.compile(r"[;:,()\[\]•|]|\s[-–—]\s")


# =========================================================================== #
# 1. Encoders
# =========================================================================== #
class HashingEncoder:
    """Lexical control: hashed character 3-5-gram bag, L2-normalised. NOT a semantic model.

    Used (a) as the 'fuzzy string matching' control in the model comparison and (b) so the test-suite and a
    smoke test run offline. If a Sentence Transformer does not beat this, its gain is only surface similarity.
    """
    name = "hashing"

    def __init__(self, dim: int = 1024, **_):
        self.dim = dim

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            s = f" {re.sub(r'[^a-z0-9+#/.]+', ' ', str(t).lower()).strip()} "
            for n in (3, 4, 5):
                for j in range(len(s) - n + 1):
                    out[i, zlib.crc32(s[j:j + n].encode()) % self.dim] += 1.0
        norm = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.maximum(norm, 1e-9)

    def save(self):  # parity with Encoder
        pass


class Encoder:
    """Sentence-Transformers wrapper with lazy loading and a persistent text->vector cache.

    Vectors are L2-normalised, so cosine similarity is a dot product. The cache (cache/<key>.pkl) makes repeat runs
    and ablations cheap: each distinct text is embedded once per model.
    """

    def __init__(self, key: str = config.MAIN_MODEL, device: str | None = None, batch_size: int = 64,
                 cache_dir: Path | None = config.CACHE, show_progress: bool = False):
        if key not in config.MODELS or config.MODELS[key]["hf"] is None:
            raise ValueError(f"unknown neural model key {key!r}; choose from "
                             f"{[k for k, v in config.MODELS.items() if v['hf']]}")
        self.name = key
        self.hf = config.MODELS[key]["hf"]
        self.prefix = config.MODELS[key]["prefix"]
        self.device, self.batch_size, self.show_progress = device, batch_size, show_progress
        self._model = None
        self._cache: dict[str, np.ndarray] = {}
        self._path = Path(cache_dir) / f"{key}.pkl" if cache_dir else None
        self._dirty = False
        if self._path and self._path.exists():
            try:
                self._cache = pickle.loads(self._path.read_bytes())
            except Exception:           # corrupt cache: start again
                self._cache = {}

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer     # imported lazily (heavy)
            self._model = SentenceTransformer(self.hf, device=self.device)
        return self._model

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        texts = [str(t) for t in texts]
        missing = list(dict.fromkeys(t for t in texts if t not in self._cache))
        if missing:
            vecs = self.model.encode([self.prefix + t for t in missing], batch_size=self.batch_size,
                                     normalize_embeddings=True, show_progress_bar=self.show_progress,
                                     convert_to_numpy=True)
            for t, v in zip(missing, vecs):
                self._cache[t] = np.asarray(v, dtype=np.float32)
            self._dirty = True
        if not texts:
            return np.zeros((0, 1), dtype=np.float32)
        return np.vstack([self._cache[t] for t in texts])

    def save(self):
        if self._path and self._dirty:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_bytes(pickle.dumps(self._cache))
            self._dirty = False


def get_encoder(key: str, **kw):
    return HashingEncoder() if key == "hashing" else Encoder(key, **kw)


# =========================================================================== #
# 2. Units: what is embedded
# =========================================================================== #
@dataclass(frozen=True)
class Unit:
    text: str
    line_no: int
    strength: str
    kind: str          # line | clause | window


def _clean(line: str) -> str:
    return re.sub(r"\s+", " ", _URL.sub(" ", _BULLET.sub("", line))).strip()


def _nwords(s: str) -> int:
    return len(s.split())


def make_units(segments: Iterable[tuple], granularity: str = "line+clause", min_words: int = 3,
               max_words: int = 60, include_company: bool = False) -> list[Unit]:
    """segments: iterable of (line_no, line, strength) as produced by RequirementAwareExtractor.segment().

    granularity:
      line         one unit per line (long lines are split into sentences)
      clause       the line split at , ; : ( ) | and dashes (phrase level; pieces under 3 words dropped)
      line+clause  both (default): sentence context and phrase precision
      line+window  lines plus every pair of consecutive lines (context across bullets), same strength only
    """
    if granularity not in {"line", "clause", "line+clause", "line+window"}:
        raise ValueError(f"unknown granularity {granularity!r}")
    segs = [(i, _clean(line), s) for i, line, s in segments]
    segs = [(i, l, s) for i, l, s in segs if l and (include_company or s != COMPANY)]
    units: list[Unit] = []

    def sentences(line):
        return [x for x in (_SENT.split(line) if _nwords(line) > max_words else [line]) if x.strip()]

    for i, line, s in segs:
        if granularity in ("line", "line+clause", "line+window"):
            units += [Unit(x.strip(), i, s, "line") for x in sentences(line) if _nwords(x) >= min_words]
        if granularity in ("clause", "line+clause"):
            for sent in sentences(line):
                for c in _CLAUSE.split(sent):
                    c = c.strip()
                    if _nwords(c) >= min_words and c != line:
                        units.append(Unit(c, i, s, "clause"))
    if granularity == "line+window":
        for (i, a, sa), (j, b, sb) in zip(segs, segs[1:]):
            if sa == sb and _nwords(a) + _nwords(b) <= max_words * 2:
                units.append(Unit(f"{a} {b}", i, sa, "window"))
    seen, out = set(), []
    for u in units:                              # drop exact duplicates, keep the first (strongest position)
        k = (u.text.lower(), u.strength)
        if k not in seen:
            seen.add(k)
            out.append(u)
    return out


# =========================================================================== #
# 3. Skill space: dictionary -> prototype embeddings
# =========================================================================== #
def load_skill_table(step3_dir: Path, with_extra: bool = True) -> pd.DataFrame:
    """canonical_skill, alias, category (base dictionary + reviewed extra aliases, as in Baseline++)."""
    base = pd.read_csv(Path(step3_dir) / "skills_dictionary.csv", encoding="utf-8-sig")
    cols = ["canonical_skill", "alias", "category"]
    table = base[cols]
    extra_path = Path(step3_dir) / "extra_aliases_reviewed.csv"
    if with_extra and extra_path.exists():
        extra = pd.read_csv(extra_path, encoding="utf-8-sig")[cols]
        table = pd.concat([table, extra], ignore_index=True)
    table = table.drop_duplicates(["canonical_skill", "alias"]).reset_index(drop=True)
    table["alias"] = table["alias"].astype(str).str.strip()
    return table


class SkillSpace:
    """Prototype embeddings for the candidate skills.

    proto_mode: canonical    one prototype per skill (its name)
                aliases      name + every alias with >= min_alias_len characters (default)
                aliases_ctx  as aliases, each written "<phrase> (<category>)" to disambiguate short phrases
    pool:       max          skill score = max cosine over its prototypes (default in the first run)
                centroid     skill score = cosine to the mean prototype (current default, see config.py)
    categories: concept (config.CONCEPT_CATEGORIES) | all
    """

    def __init__(self, table: pd.DataFrame, encoder, proto_mode: str = "aliases", pool: str = "max",
                 categories: str | Iterable[str] = "concept", min_alias_len: int = 4):
        if proto_mode not in {"canonical", "aliases", "aliases_ctx"} or pool not in {"max", "centroid"}:
            raise ValueError("bad proto_mode / pool")
        self.proto_mode, self.pool, self.encoder = proto_mode, pool, encoder
        cat_of = table.drop_duplicates("canonical_skill").set_index("canonical_skill")["category"].to_dict()
        if categories == "all":
            keep = set(cat_of)
        elif categories == "concept":
            keep = {s for s, c in cat_of.items() if c in config.CONCEPT_CATEGORIES}
        else:
            keep = {s for s, c in cat_of.items() if c in set(categories)}
        self.skills = sorted(keep)
        self.category = {s: cat_of[s] for s in self.skills}
        texts, owner = [], []
        for si, s in enumerate(self.skills):
            phrases = [s]
            if proto_mode != "canonical":
                aliases = table.loc[table.canonical_skill == s, "alias"].tolist()
                phrases += [a for a in aliases if len(a) >= min_alias_len or " " in a]
            seen = set()
            for p in phrases:
                key = p.lower()
                if key in seen:
                    continue
                seen.add(key)
                texts.append(f"{p} ({cat_of[s]})" if proto_mode == "aliases_ctx" else p)
                owner.append(si)
        self.proto_texts, self.owner = texts, np.asarray(owner)
        E = encoder.encode(texts)
        if pool == "centroid":
            C = np.zeros((len(self.skills), E.shape[1]), dtype=np.float32)
            np.add.at(C, self.owner, E)
            C /= np.maximum(np.linalg.norm(C, axis=1, keepdims=True), 1e-9)
            self.matrix, self._starts = C, None
        else:
            self.matrix = E                                   # owner is sorted ascending by construction
            self._starts = np.flatnonzero(np.r_[True, np.diff(self.owner) != 0])
        self.mu = self.sd = None                              # set by fit_reference()

    # ------------------------------------------------------------------ #
    def similarity(self, unit_emb: np.ndarray) -> np.ndarray:
        """U x S cosine similarity (each skill = pooled over its prototypes)."""
        if unit_emb.shape[0] == 0:
            return np.zeros((0, len(self.skills)), dtype=np.float32)
        sim = unit_emb @ self.matrix.T
        if self.pool == "max":
            sim = np.maximum.reduceat(sim, self._starts, axis=1)
        return sim

    def fit_reference(self, ref_unit_emb: np.ndarray):
        """Per-skill mean/std of similarity over unlabelled reference units (for z-normalisation)."""
        if ref_unit_emb.shape[0] < 2:
            raise ValueError("z-normalisation needs at least 2 reference units (unlabelled non-gold ads)")
        sim = self.similarity(ref_unit_emb)
        self.mu, self.sd = sim.mean(axis=0), np.maximum(sim.std(axis=0), 1e-6)
        return self

    def normalise(self, sim: np.ndarray, norm: str) -> np.ndarray:
        if norm == "raw":
            return sim
        if norm == "z":
            if self.mu is None:
                raise RuntimeError("call fit_reference() before using norm='z'")
            return (sim - self.mu) / self.sd
        raise ValueError(norm)


# =========================================================================== #
# 4. Decision rule
# =========================================================================== #
@dataclass(frozen=True)
class Decision:
    tau: float                        # threshold on the (raw or z) score
    delta: float | None = None        # keep only skills within `delta` of the unit's best skill
    topk: int | None = None           # keep at most k skills per unit
    norm: str = "raw"

    def label(self) -> str:
        return f"tau={self.tau}" + (f",delta={self.delta}" if self.delta is not None else "") + \
               (f",top{self.topk}" if self.topk else "") + f",{self.norm}"


def detect(S: np.ndarray, d: Decision) -> dict[int, tuple[float, int]]:
    """S: U x K score matrix (already normalised). -> {skill column: (best score, best unit row)}."""
    if S.shape[0] == 0 or S.shape[1] == 0:
        return {}
    keep = S >= d.tau
    if d.delta is not None:
        keep &= S >= (S.max(axis=1, keepdims=True) - d.delta)
    if d.topk:
        rank = np.argsort(np.argsort(-S, axis=1), axis=1)
        keep &= rank < d.topk
    masked = np.where(keep, S, -np.inf)
    best, row = masked.max(axis=0), masked.argmax(axis=0)
    return {int(k): (float(best[k]), int(row[k])) for k in np.flatnonzero(np.isfinite(best))}


# =========================================================================== #
# 5. Per-text scores (cached once, reused for every decision)
# =========================================================================== #
@dataclass
class TextScores:
    units: list[Unit]
    S: np.ndarray                     # U x K raw cosine
    skills: list[str]                 # K names (column order)

    def additions(self, space: SkillSpace, d: Decision, exclude: set[str] = frozenset()) -> dict[str, "SemHit"]:
        hits = detect(space.normalise(self.S, d.norm), d)
        out = {}
        for k, (score, row) in hits.items():
            sk = self.skills[k]
            if sk in exclude:
                continue
            u = self.units[row]
            out[sk] = SemHit(sk, score, float(self.S[row, k]), u.text, u.line_no, u.strength)
        return out


@dataclass(frozen=True)
class SemHit:
    skill: str
    score: float          # decision score (cosine, or z when norm='z')
    cosine: float
    unit: str
    line_no: int
    strength: str


def score_text(text: str, base, space: SkillSpace, encoder, granularity: str = "line+clause",
               min_words: int = 3, max_words: int = 60, include_company: bool = False) -> TextScores:
    units = make_units(base.segment(text), granularity, min_words, max_words, include_company)
    emb = encoder.encode([u.text for u in units]) if units else np.zeros((0, space.matrix.shape[1]), np.float32)
    return TextScores(units, space.similarity(emb), space.skills)


# =========================================================================== #
# 6. Hybrid extractor (public API)
# =========================================================================== #
@dataclass(frozen=True)
class Evidence:
    skill: str
    source: str            # exact | semantic
    strength: str
    weight: float
    score: float | None    # None for exact
    unit: str | None
    line_no: int | None


class HybridExtractor:
    """Baseline++ (exact) plus semantic additions. Same call signatures as RequirementAwareExtractor."""

    def __init__(self, base, space: SkillSpace, encoder, decision: Decision, granularity: str = "line+clause",
                 sem_weight: float = 1.0, min_words: int = 3, max_words: int = 60, include_company: bool = False):
        self.base, self.space, self.encoder, self.decision = base, space, encoder, decision
        self.granularity, self.sem_weight = granularity, sem_weight
        self.min_words, self.max_words, self.include_company = min_words, max_words, include_company
        self.weights = dict(getattr(base, "weights", FALLBACK_WEIGHTS))

    def _semantic(self, text: str, exact: set[str]) -> dict[str, SemHit]:
        ts = score_text(text, self.base, self.space, self.encoder, self.granularity,
                        self.min_words, self.max_words, self.include_company)
        return ts.additions(self.space, self.decision, exclude=exact)

    def _exact_lines(self, text: str, exact: dict[str, str]) -> dict[str, tuple[str, int]]:
        """skill -> (line, line_no) of the exact match that gave its strength (needs base.analyse, as in Step 3's
        RequirementAwareExtractor; returns {} for bases without it). Gives exact hits an evidence sentence too, which
        the explainable output and the blinded audit sheet need."""
        if not hasattr(self.base, "analyse"):
            return {}
        out = {}
        for m in self.base.analyse(text):
            if m.canonical in exact and m.canonical not in out and m.strength == exact[m.canonical]:
                out[m.canonical] = (_clean(m.line), m.line_no)
        return out

    def analyse(self, text: str) -> list[Evidence]:
        exact = self.base.skill_strengths(text)
        lines = self._exact_lines(text, exact)
        out = [Evidence(s, "exact", st, self.weights.get(st, 0.0), None, *lines.get(s, (None, None)))
               for s, st in exact.items()]
        out = [e for e in out if e.strength != COMPANY]
        found = {s for s, st in exact.items() if st != COMPANY}     # same rule as the evaluation: a skill named only in
                                                                    # company text may still be added from role text
        for sk, h in self._semantic(text, found).items():
            out.append(Evidence(sk, "semantic", h.strength, self.weights.get(h.strength, 0.0) * self.sem_weight,
                                h.score, h.unit, h.line_no))
        return out

    def skill_strengths(self, text: str) -> dict[str, str]:
        """skill -> strength class (exact hits first, then semantic); company-only skills are dropped."""
        return {e.skill: e.strength for e in self.analyse(text) if e.strength != COMPANY}

    def extract_skills(self, text: str, mode: str = "demand") -> list[str]:
        return list(self.skill_strengths(text))

    def extract_weighted(self, text: str) -> dict[str, float]:
        return {e.skill: e.weight for e in self.analyse(text) if e.weight > 0}

    def explain(self, text: str) -> pd.DataFrame:
        return pd.DataFrame([e.__dict__ for e in self.analyse(text)])
