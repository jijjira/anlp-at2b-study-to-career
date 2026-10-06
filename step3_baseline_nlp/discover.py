"""Dictionary discovery by list-context mining (semi-automatic, human-in-the-loop).

Idea: skills are usually enumerated ("Python, SQL, Spark, X, Y"). An unknown item that sits in the same
list as >=2 known skills is a skill candidate. Candidates are ranked by document frequency and by
'list purity' (share of its occurrences that are inside skill lists) and then reviewed by a human.
"""
import re, json, collections
import pandas as pd
from skill_extractor import SkillExtractor, preprocess

SPLIT = re.compile(r"\s[,;/|]\s|\s(?:and|or|and/or)\s|[()\[\]:•]|\be\.g\.|\bi\.e\.|\bsuch as\b|\bincluding\b|\blike\b|\bsuch\b|\betc\b", re.I)
LEAD = re.compile(r"^(?:experience|experienced|proficien\w+|knowledge|familiar\w*|expertise|working|hands-on|exposure|skills?|strong|solid|deep|"
                  r"with|in|of|using|on|the|a|an|to|for|within|across|including|especially|preferably|particularly|as|our|your|any|other|"
                  r"modern|major|popular|related|similar|equivalent|frameworks?|tools?|languages?|technologies|platforms?|libraries|stack)\s+", re.I)
STOP = set("""etc more others other please data team teams work working role roles experience years year skills skill
 ability business product products customer customers engineering engineer science scientist research development
 strong good great excellent plus similar equivalent related relevant new best global companies company all each""".split())

def segments(line):
    pos, out = 0, []
    for m in SPLIT.finditer(line):
        out.append((pos, m.start())); pos = m.end()
    out.append((pos, len(line)))
    return [(a, b, line[a:b].strip()) for a, b in out if line[a:b].strip()]

def clean(seg):
    prev = None
    while prev != seg:
        prev, seg = seg, LEAD.sub("", seg).strip(" .-–—*•'\"")
    return seg

def mine(texts, ext, min_known=2):
    cand = collections.defaultdict(lambda: {"jobs": set(), "forms": collections.Counter(), "n": 0})
    for k, t in texts:
        lines = [preprocess(l) for l in str(t).split("\n") if l.strip()]
        for line, ms in zip(lines, ext.extract_many(lines)):
            if len({m.canonical for m in ms}) < min_known: continue
            spans = [(m.start, m.end) for m in ms]
            for a, b, seg in segments(line):
                if any(s < b and e > a for s, e in spans): continue          # segment already holds a known skill
                c = clean(seg)
                toks = c.split()
                if not (1 <= len(toks) <= 3) or len(c) < 2 or len(c) > 30: continue
                if not re.search(r"[A-Za-z]", c) or c.lower() in STOP or all(w.lower() in STOP for w in toks): continue
                d = cand[c.lower()]; d["jobs"].add(k); d["forms"][c] += 1; d["n"] += 1
    return cand

if __name__ == "__main__":
    j = pd.read_csv("job_cleaned.csv", encoding="utf-8-sig")
    gold = set(json.load(open("gold_split.json"))["gold_row_index"])
    dev = [(k, t) for k, t in j.job_description.items() if k not in gold]      # discovery never sees the held-out sample
    ext = SkillExtractor()
    cand = mine(dev, ext)
    alltext = {k: preprocess(t).lower() for k, t in dev}
    rows = []
    for key, d in cand.items():
        if len(d["jobs"]) < 3: continue
        total = sum(len(re.findall(rf"(?<![a-z0-9]){re.escape(key)}(?![a-z0-9])", t)) for t in alltext.values())
        rows.append({"candidate": d["forms"].most_common(1)[0][0], "list_jobs": len(d["jobs"]),
                     "list_mentions": d["n"], "all_mentions": total, "purity": round(min(1, d["n"] / max(total, 1)), 2)})
    df = pd.DataFrame(rows).sort_values(["list_jobs", "purity"], ascending=False)
    df.to_csv("discovery_candidates_raw.csv", index=False)
    print(len(df), "candidates"); print(df.head(150).to_string(index=False))
