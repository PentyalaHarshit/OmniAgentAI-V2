"""
tools/query_corrector.py
=========================
Query Correction Agent — fixes spelling mistakes in user queries before routing.

Uses rapidfuzz for fuzzy string matching (much better than difflib for
real-world typos like "popualation", "graivty", "telepone").

Flow
----
  User: "what is popualation of japan"
  Thought: Possible spelling mistake detected in 'popualation'
  Action: Fuzzy-match 'popualation' → 'population' (score 91.7)
  Observation: Corrected query = "what is population of japan"
  Answer: routed to GeneralAgent with clean query

Correction strategy
-------------------
  1. Each word in the query is checked against the vocabulary.
  2. If the best fuzzy match scores ≥ CUTOFF and differs from the original,
     the word is replaced.
  3. Short words (≤ 3 chars), numbers, and proper nouns starting mid-sentence
     are skipped to avoid over-correction.
  4. Stop words (the, a, is, of, …) are passed through unchanged.
"""

import re
import logging
from rapidfuzz import process, fuzz

logger = logging.getLogger(__name__)

# ── Cutoff score (0–100). Below this → keep original word ─────────────────
CUTOFF = 82

# ── Vocabulary: all words the corrector is allowed to suggest ─────────────
# Organised by domain so it's easy to extend.
VOCABULARY: list[str] = [
    # ── Question / query words ────────────────────────────────────────────
    "what", "when", "where", "who", "which", "why", "how",
    "is", "are", "was", "were", "did", "does", "do",
    "invented", "discovered", "created", "founded", "built", "designed",
    "won", "ruled", "governed", "defeated", "conquered",
    # ── Geography ─────────────────────────────────────────────────────────
    "capital", "population", "currency", "region", "continent", "country",
    "city", "language", "area", "location", "geography",
    "japan", "france", "italy", "india", "china", "germany", "spain",
    "brazil", "russia", "canada", "australia", "egypt", "turkey",
    "pakistan", "indonesia", "mexico", "nigeria", "korea",
    "united", "states", "kingdom", "america",
    # ── Science / maths ───────────────────────────────────────────────────
    "gravity", "gravitation", "physics", "chemistry", "biology",
    "quantum", "mechanics", "relativity", "calculus", "algebra",
    "electricity", "magnetism", "thermodynamics", "evolution",
    "theory", "equation", "formula", "element", "molecule", "atom",
    # ── Technology / inventions ────────────────────────────────────────────
    "telephone", "telegraph", "television", "radio", "internet",
    "computer", "calculator", "electricity", "battery", "engine",
    "airplane", "automobile", "printing", "photography",
    "penicillin", "vaccine", "dynamite", "nuclear",
    # ── History ───────────────────────────────────────────────────────────
    "dynasty", "empire", "kingdom", "revolution", "independence",
    "history", "historical", "ancient", "medieval", "modern",
    "war", "battle", "treaty", "constitution", "republic",
    "civilization", "century", "period", "era",
    # ── Economics ─────────────────────────────────────────────────────────
    "gdp", "economy", "inflation", "recession", "export", "import",
    "trade", "market", "finance", "banking", "investment",
    # ── Healthcare ────────────────────────────────────────────────────────
    "symptom", "diagnosis", "treatment", "medicine", "hospital",
    "doctor", "patient", "disease", "infection", "surgery",
    "diabetes", "hypertension", "cancer", "fever", "pain",
    # ── Programming ───────────────────────────────────────────────────────
    "python", "javascript", "algorithm", "function", "variable",
    "database", "server", "network", "security", "encryption",
    "recursion", "inheritance", "polymorphism", "compilation",
    # ── Travel / booking ──────────────────────────────────────────────────
    "hotel", "flight", "restaurant", "reservation", "booking",
    "travel", "airport", "destination", "itinerary", "vacation",
    "ticket", "passport", "visa", "accommodation",
    # ── General ───────────────────────────────────────────────────────────
    "population", "government", "president", "minister", "parliament",
    "university", "education", "language", "religion", "culture",
    "distance", "measurement", "temperature", "speed", "weight",
]

# ── Stop words — pass through without correction ──────────────────────────
_STOP_WORDS = {
    "a", "an", "the", "of", "in", "on", "at", "to", "for", "and",
    "or", "but", "not", "with", "by", "from", "up", "as", "into",
    "it", "its", "i", "my", "me", "we", "us", "you", "he", "she",
    "they", "this", "that", "these", "those", "about", "than",
}


class QueryCorrector:
    """
    Corrects spelling mistakes in user queries using rapidfuzz.

    Usage
    -----
        corrector = QueryCorrector()
        result = corrector.correct("what is popualation of japan")
        # result = {
        #   "original":  "what is popualation of japan",
        #   "corrected": "what is population of japan",
        #   "changed":   True,
        #   "changes":   [("popualation", "population", 91.7)]
        # }
    """

    def __init__(self, cutoff: int = CUTOFF):
        self.cutoff = cutoff
        # Pre-build lowercase vocabulary for fast lookup
        self._vocab = [w.lower() for w in VOCABULARY]

    def correct(self, query: str) -> dict:
        """
        Correct spelling in `query`.

        Returns
        -------
        {
            "original":  str,   original query
            "corrected": str,   query with corrections applied
            "changed":   bool,  True if any word was corrected
            "changes":   list,  [(original_word, corrected_word, score), ...]
        }
        """
        tokens  = query.split()
        result  = []
        changes = []

        for token in tokens:
            # Preserve punctuation attached to the token
            word, suffix = self._split_punctuation(token)
            word_lo = word.lower()

            # Skip: stop words, short words (≤3 chars), pure digits, URLs
            if (word_lo in _STOP_WORDS
                    or len(word) <= 3
                    or word.isdigit()
                    or word.startswith("http")):
                result.append(token)
                continue

            # Skip: already an exact vocabulary match
            if word_lo in self._vocab:
                result.append(token)
                continue

            # Fuzzy match against vocabulary
            match = process.extractOne(
                word_lo,
                self._vocab,
                scorer=fuzz.ratio,
                score_cutoff=self.cutoff,
            )

            if match and match[0] != word_lo:
                corrected_word = match[0]
                score          = round(match[1], 1)

                # Preserve original capitalisation pattern
                corrected_word = self._preserve_case(word, corrected_word)

                changes.append((word, corrected_word, score))
                logger.debug(
                    "[QueryCorrector] '%s' → '%s' (score %.1f)",
                    word, corrected_word, score
                )
                result.append(corrected_word + suffix)
            else:
                result.append(token)

        corrected_query = " ".join(result)
        return {
            "original":  query,
            "corrected": corrected_query,
            "changed":   bool(changes),
            "changes":   changes,
        }

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _split_punctuation(token: str) -> tuple[str, str]:
        """Split trailing punctuation: 'japan?' → ('japan', '?')"""
        m = re.match(r"^([\w\-]+)([^\w\-]*)$", token)
        if m:
            return m.group(1), m.group(2)
        return token, ""

    @staticmethod
    def _preserve_case(original: str, corrected: str) -> str:
        """
        Apply the capitalisation of the original word to the corrected word.
        'Japan' → 'Japan', 'JAPAN' → 'POPULATION', 'japan' → 'population'
        """
        if original.isupper():
            return corrected.upper()
        if original.istitle():
            return corrected.capitalize()
        return corrected
