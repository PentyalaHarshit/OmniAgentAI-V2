"""
tools/similarity_ranker.py
==========================
Similarity Ranker — ranks retrieved documents by relevance to the query,
with answer-type aware boosting AND off-topic rejection.

Algorithm
---------
  base_score    = |query_words ∩ doc_words| / max(|query_words|, 1)
  boost_score   = domain-specific signal boosts
  answer_boost  = does the doc contain the TYPE of answer needed?
                  (dates for duration/when, names for inventor, numbers for population)
  penalty       = doc title matches known off-topic patterns for this query type
  final_score   = base + boost + answer_boost - penalty   (min 0.0, rounded 3 dp)
"""

import re
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain boost rules: (query_signal, doc_signal, boost)
# ---------------------------------------------------------------------------
_BOOST_RULES: list[tuple[str, str, float]] = [
    # Phone / telephone
    ("telephone", "telephone", 0.50),
    ("phone",     "telephone", 0.45),
    ("telephone", "phone",     0.30),
    # Invention
    ("invent",   "invent",   0.40),
    ("invented", "inventor", 0.35),
    ("patent",   "patent",   0.40),
    ("discover", "discover", 0.35),
    ("founded",  "founded",  0.25),
    # History / duration  ← core fix for Chola-type queries
    ("dynasty",  "dynasty",  0.55),
    ("empire",   "empire",   0.45),
    ("ruled",    "ruled",    0.45),
    ("ruled",    "dynasty",  0.40),
    ("ruled",    "empire",   0.35),
    ("reign",    "reign",    0.40),
    ("period",   "period",   0.25),
    ("century",  "century",  0.25),
    ("bce",      "bce",      0.40),
    ("ce",       "ce",       0.20),
    ("years",    "years",    0.20),
    # Named dynasties
    ("chola",    "chola",    0.70),
    ("mughal",   "mughal",   0.70),
    ("ottoman",  "ottoman",  0.70),
    ("roman",    "roman",    0.50),
    ("maurya",   "maurya",   0.70),
    # Geography
    ("capital",  "capital",      0.40),
    ("capital",  "capital city", 0.45),
    # Economics
    ("gdp",      "gdp",                    0.45),
    ("gdp",      "gross domestic product", 0.45),
    ("economy",  "economy",               0.25),
    # Population
    ("population", "population",  0.45),
    ("population", "inhabitants", 0.30),
    # War / history events
    ("world war", "world war", 0.55),
    ("ww2",       "world war", 0.50),
    # Science
    ("gravity",   "gravity",   0.45),
    ("newton",    "newton",    0.40),
    # Superlatives
    ("longest river", "river",   0.40),
    ("longest",       "longest", 0.35),
]

# ---------------------------------------------------------------------------
# Answer-type boosting: if query needs dates and doc has dates → boost
# ---------------------------------------------------------------------------
_DATE_PATTERN   = re.compile(r"\b\d{3,4}\s*(bce?|ce|ad)\b|\b\d{4}\b", re.I)
_NUMBER_PATTERN = re.compile(r"\b\d[\d,\.]+\s*(million|billion|thousand|crore)?\b")
_NAME_PATTERN   = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")

def _needs_dates(q: str) -> bool:
    return bool(re.search(r"\bhow long\b|\bwhen (did|was|were|is)\b|\bduration\b|\bperiod\b", q))

def _needs_inventor_name(q: str) -> bool:
    return bool(re.search(r"\bwho (invented|discovered|created|founded|built)\b", q))

def _needs_number(q: str) -> bool:
    return bool(re.search(r"\bpopulation\b|\bgdp\b|\barea\b|\bsize\b", q))

# ---------------------------------------------------------------------------
# Off-topic rejection patterns per query type
# These title patterns indicate the doc does NOT answer the question.
# ---------------------------------------------------------------------------
_REJECTION_RULES: list[tuple[callable, list[str], float]] = [
    # If asking about dynasty duration, penalise pages about specific sub-topics
    (
        lambda q: bool(re.search(r"\b(dynasty|empire|ruled|rule|kingdom)\b", q)),
        ["navy", "architecture", "temple", "art", "sculpture", "religion",
         "literature", "music", "cuisine", "language", "coins", "trade route",
         "port", "festival", "clothing", "weapon", "war film"],
        0.80,   # heavy penalty
    ),
    # If asking who invented X, penalise pages about the thing itself (not the inventor)
    (
        lambda q: bool(re.search(r"\bwho (invented|discovered|created)\b", q)),
        ["history of", "uses of", "types of", "how to use", "benefits of"],
        0.40,
    ),
]


class SimilarityRanker:
    """
    Ranks documents by relevance with:
    - keyword overlap (base)
    - domain signal boosts
    - answer-type awareness (dates / names / numbers)
    - off-topic title rejection penalties
    """

    def rank(self, query: str, docs: list[dict]) -> list[dict]:
        q_lower = query.lower()
        q_words = set(re.findall(r"[a-zA-Z0-9]+", q_lower))

        need_dates    = _needs_dates(q_lower)
        need_inventor = _needs_inventor_name(q_lower)
        need_number   = _needs_number(q_lower)

        ranked: list[dict] = []

        for doc in docs:
            if doc.get("source") == "error":
                doc["similarity_score"] = 0.0
                ranked.append(doc)
                continue

            title   = doc.get("title", "").lower()
            text    = doc.get("text", "").lower()
            full    = f"{title} {text}"
            d_words = set(re.findall(r"[a-zA-Z0-9]+", full))

            # ── Base overlap ──────────────────────────────────────────────
            overlap = len(q_words & d_words)
            score   = overlap / max(len(q_words), 1)

            # ── Domain boosts ─────────────────────────────────────────────
            for q_sig, d_sig, boost in _BOOST_RULES:
                if q_sig in q_lower and d_sig in full:
                    score += boost

            # ── Answer-type awareness ─────────────────────────────────────
            if need_dates and _DATE_PATTERN.search(full):
                score += 0.50   # doc has dates/years → very likely answers "how long"
            if need_inventor and _NAME_PATTERN.search(doc.get("text", "")):
                score += 0.30
            if need_number and _NUMBER_PATTERN.search(full):
                score += 0.30

            # ── Off-topic title penalties ─────────────────────────────────
            for condition, reject_terms, penalty in _REJECTION_RULES:
                if condition(q_lower):
                    for term in reject_terms:
                        if term in title:
                            score -= penalty
                            logger.debug(
                                "[Ranker] Penalty -%.2f for off-topic '%s' in '%s'",
                                penalty, term, title[:60]
                            )
                            break

            doc["similarity_score"] = round(max(score, 0.0), 3)
            ranked.append(doc)

        ranked.sort(key=lambda x: x["similarity_score"], reverse=True)

        for i, doc in enumerate(ranked[:5]):
            logger.debug(
                "[SimilarityRanker] Rank %d | %.3f | %s",
                i + 1, doc["similarity_score"], doc.get("title", "?")[:80],
            )

        return ranked
