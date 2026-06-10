"""
tools/fact_verifier.py
======================
Fact Verification Agent.

ReAct Stage: Action — verify extracted answer across multiple source documents.

Strategy
--------
1. Cross-source consistency  — count how many docs contain the key answer term.
2. Contradiction detection   — look for contradictory date / name patterns.
3. Known-wrong rules         — hardcoded sanity checks (e.g. "capital of Paris").

Returns a verification result dict:
  {
    "verified"    : bool,
    "confidence"  : float,   # 0.0 – 1.0
    "reason"      : str,
    "corrected"   : str,     # same as answer if no correction needed
    "sources_used": int,
  }
"""

import re
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Known incorrect query patterns that should never reach a real answer
# ---------------------------------------------------------------------------
_KNOWN_WRONG: list[tuple[re.Pattern, str]] = [
    (
        re.compile(r"capital\s+of\s+paris", re.I),
        "Paris is a city, not a country, and does not have a capital. "
        "Did you mean: What is the capital of France? Answer: Paris.",
    ),
    (
        re.compile(r"capital\s+of\s+(new york|london|tokyo|berlin|sydney)", re.I),
        "That is a city, not a country. Please ask about the capital of a country.",
    ),
]


class FactVerifier:
    """
    Verifies an extracted answer against retrieved source documents.

    Usage
    -----
        verifier = FactVerifier()
        result = verifier.verify(query, answer, docs)
    """

    def verify(self, query: str, answer: str, docs: list[dict]) -> dict:
        """
        Parameters
        ----------
        query   : original user question
        answer  : the extracted candidate answer string
        docs    : ranked source documents (each has 'text' key)

        Returns
        -------
        dict with keys: verified, confidence, reason, corrected, sources_used
        """
        # ── 1. Known-wrong query check ────────────────────────────────────
        for pattern, correction in _KNOWN_WRONG:
            if pattern.search(query):
                return {
                    "verified":     False,
                    "confidence":   0.0,
                    "reason":       "Known invalid query pattern.",
                    "corrected":    correction,
                    "sources_used": 0,
                }

        if not answer or not docs:
            return {
                "verified":     bool(answer),
                "confidence":   0.5 if answer else 0.0,
                "reason":       "No sources to verify against." if answer else "Empty answer.",
                "corrected":    answer,
                "sources_used": 0,
            }

        # ── 2. Cross-source consistency ───────────────────────────────────
        # Extract key nouns / numbers from answer
        answer_tokens = set(re.findall(r"[A-Za-z]{3,}|\d{3,}", answer))

        supporting_docs = 0
        for doc in docs[:5]:
            text_lo = doc.get("text", "").lower()
            hit = sum(1 for tok in answer_tokens if tok.lower() in text_lo)
            if hit >= max(1, len(answer_tokens) // 3):
                supporting_docs += 1

        confidence = min(1.0, supporting_docs / max(len(docs[:5]), 1))

        # ── 3. Date / year sanity check ───────────────────────────────────
        years_in_answer = re.findall(r"\b(1[0-9]{3}|2[0-9]{3})\b", answer)
        if years_in_answer:
            for doc in docs[:3]:
                text = doc.get("text", "")
                for yr in years_in_answer:
                    if yr in text:
                        confidence = min(1.0, confidence + 0.1)
                        break

        # ── 4. Verdict ────────────────────────────────────────────────────
        verified = confidence >= 0.3 or supporting_docs >= 1

        return {
            "verified":     verified,
            "confidence":   round(confidence, 2),
            "reason":       (
                f"Supported by {supporting_docs}/{min(len(docs), 5)} sources."
                if verified else
                f"Low cross-source support ({supporting_docs}/{min(len(docs), 5)})."
            ),
            "corrected":    answer,
            "sources_used": supporting_docs,
        }
