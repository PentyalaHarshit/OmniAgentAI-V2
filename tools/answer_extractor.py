"""
tools/answer_extractor.py
==========================
Answer Extraction Agent.

Converts retrieved multi-source context into a direct, concise answer.

Supported question types
------------------------
  duration    – how long / from when to when / ruling period
  yes_no      – did / does / is / are / was / were
  inventor    – who invented / who discovered / who created / who built
  capital     – what is the capital of …
  population  – population of …
  gdp         – GDP of …
  area        – area / size of …
  date        – when was / when did / when is …
  location    – where is / where was …
  definition  – what is / what are …
  fallback    – compress to first 2 sentences
"""

import re


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DATE_PATTERN = re.compile(
    r"\b(\d{1,2}\s+[A-Z][a-z]+\s+\d{4}"
    r"|[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}"
    r"|\d{4}\s*(BCE?|CE|AD)"
    r"|\d{4})\b",
    re.I,
)

_DURATION_KEYWORDS = [
    "ruled", "reigned", "existed", "lasted", "founded", "established",
    "from", "until", "to", "century", "bce", "ce", "ad", "period",
    "years", "year", "dynasty", "empire", "kingdom",
]

_INVENTOR_KEYWORDS = [
    "credited", "invented", "invented by", "invention", "inventor",
    "developed", "created", "discovered", "pioneered", "patented",
    "bell", "newton", "first", "registered",
]

_AFFIRMATIVE_SIGNALS = [
    "is credited", "was credited", "widely credited", "generally credited",
    "did invent", "did create", "did discover", "patented",
    "received the patent", "is considered", "was considered",
    "successfully", "confirmed", "proved", "demonstrated",
]

_CONTROVERSY_SIGNALS = [
    "controversy", "dispute", "disputed", "debate", "contested",
    "also claimed", "simultaneously", "competing", "rival",
    "however", "although",
]


def _sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text.strip())
    parts   = re.split(r"(?<=[.!?])\s+", cleaned)
    return [s.strip() for s in parts if len(s.strip()) > 15]


def _compress(context: str, n: int = 2) -> str:
    return " ".join(_sentences(context)[:n]).strip()


# ---------------------------------------------------------------------------
# AnswerExtractor
# ---------------------------------------------------------------------------

class AnswerExtractor:

    def extract(self, query: str, context: str) -> str:
        q       = query.lower().strip().rstrip("?")
        context = re.sub(r"\s+", " ", context).strip()
        if not context:
            return ""

        # ── Duration: "how long", "from when", "period of rule" ──────────
        if self._is_duration(q):
            return self._duration(query, context)

        # ── Yes/No ────────────────────────────────────────────────────────
        if self._is_yes_no(q):
            return self._yes_no(query, context)

        # ── Inventor ──────────────────────────────────────────────────────
        if self._starts_with(q, (
            "who invented", "who discovered", "who created",
            "who built", "who designed", "who founded",
        )):
            return self._inventor(query, context)

        # ── Capital ───────────────────────────────────────────────────────
        if "capital of" in q:
            return self._capital(query, context)

        # ── Population ───────────────────────────────────────────────────
        if "population" in q:
            return self._attribute(context, ["population", "inhabitants", "people"])

        # ── GDP ───────────────────────────────────────────────────────────
        if "gdp" in q or "gross domestic product" in q:
            return self._attribute(context, ["gdp", "gross domestic product", "economy"])

        # ── Area / size ───────────────────────────────────────────────────
        if "area" in q or "size of" in q:
            return self._attribute(context, ["area", "km", "square"])

        # ── Date ──────────────────────────────────────────────────────────
        if self._starts_with(q, ("when was", "when did", "when is", "when were")):
            return self._date(context)

        # ── Location ─────────────────────────────────────────────────────
        if self._starts_with(q, ("where is", "where was", "where are", "where did")):
            return self._location(context)

        # ── Definition ───────────────────────────────────────────────────
        if self._starts_with(q, ("what is", "what are", "what was", "define", "explain")):
            return self._definition(context)

        return _compress(context)

    # ── Question type detectors ──────────────────────────────────────────

    @staticmethod
    def _is_duration(q: str) -> bool:
        return bool(re.search(
            r"\bhow long\b|\bfor how long\b|\bfrom when\b"
            r"|\bhow many years\b|\bwhen.*?to when\b"
            r"|\bduration\b|\bruled for\b",
            q
        ))

    @staticmethod
    def _is_yes_no(q: str) -> bool:
        return q.startswith((
            "did ", "does ", "do ", "is ", "are ",
            "was ", "were ", "can ", "could ", "has ", "have ",
        ))

    @staticmethod
    def _starts_with(q: str, prefixes: tuple) -> bool:
        return any(q.startswith(p) for p in prefixes)

    # ── Extractors ───────────────────────────────────────────────────────

    def _duration(self, query: str, context: str) -> str:
        """
        Extract ruling/existence period sentences.

        Strategy:
          1. Find sentences with year patterns (BCE/CE/AD or 4-digit years)
             AND at least one duration keyword → these directly answer "how long"
          2. Score and rank by number of duration signals
          3. Return top 1-2 sentences
          4. If dates found, try to compute/state the span
        """
        sents = _sentences(context)

        # Score each sentence
        scored: list[tuple[float, str]] = []
        for s in sents:
            s_lo = s.lower()
            has_date = bool(_DATE_PATTERN.search(s))
            kw_hits  = sum(1 for kw in _DURATION_KEYWORDS if kw in s_lo)
            score    = (2.0 if has_date else 0.0) + kw_hits * 0.5
            if score > 0:
                scored.append((score, s))

        scored.sort(reverse=True)

        if not scored:
            return _compress(context)

        # Return top 2 most informative sentences
        top = [s for _, s in scored[:2]]
        result = " ".join(top).strip()

        # If we found date ranges, try to present them cleanly
        # Look for patterns like "300 BCE to 1279 CE" or "848 CE – 1279 CE"
        span_m = re.search(
            r"(\d{1,4}\s*(?:BCE?|CE|AD))\s*(?:to|–|-|until|and)\s*(\d{1,4}\s*(?:BCE?|CE|AD))",
            result, re.I
        )
        if span_m and len(result) > 300:
            # Trim to the most relevant sentence containing the date span
            for _, s in scored:
                if span_m.group(0) in s:
                    result = s
                    break

        return result

    def _yes_no(self, query: str, context: str) -> str:
        lower = context.lower()
        sents = _sentences(context)

        aff = sum(1 for sig in _AFFIRMATIVE_SIGNALS if sig in lower)
        con = sum(1 for sig in _CONTROVERSY_SIGNALS if sig in lower)

        name_m = re.search(
            r"(?:did|does|is|are|was|were|can|could)\s+"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4})",
            query, re.I
        )
        subj_words = name_m.group(1).lower().split() if name_m else []

        primary = next(
            (s for s in sents if subj_words and any(w in s.lower() for w in subj_words)),
            sents[0] if sents else "",
        )
        primary = ". ".join(primary.split(". ")[:2]).strip()
        if primary and not primary.endswith("."):
            primary += "."

        con_sent = next(
            (s for s in sents if any(sig in s.lower() for sig in
             ["controversy", "dispute", "however", "although"])),
            ""
        )

        if aff > 0 and con == 0:
            return f"Yes. {primary}" if primary else "Yes."
        if aff > 0 and con > 0:
            parts = ["Generally yes, but with historical debate.", primary]
            if con_sent and con_sent != primary:
                cs = ". ".join(con_sent.split(". ")[:2]).strip()
                parts.append(cs if cs.endswith(".") else cs + ".")
            return " ".join(p for p in parts if p)
        if con > 0:
            return f"This is historically debated. {primary}"
        return _compress(context)

    def _inventor(self, query: str, context: str) -> str:
        sents = _sentences(context)

        subj_m = re.search(
            r"(?:who invented|who discovered|who created|who built"
            r"|who designed|who founded)\s+(?:the\s+)?(.+)",
            query, re.I,
        )
        subject = subj_m.group(1).strip().rstrip("?") if subj_m else ""

        # Layer 1: passive voice
        m = re.search(
            r"(?:invented|created|patented|developed|designed|discovered|founded)"
            r"\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
            context, re.I,
        )
        if m:
            obj = f" the {subject}" if subject else " it"
            return f"{m.group(1)} invented{obj}."

        # Layer 2: active voice
        m = re.search(
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\s+"
            r"(?:invented|created|patented|developed|designed|discovered|founded)",
            context,
        )
        if m:
            obj = f" the {subject}" if subject else " it"
            return f"{m.group(1)} invented{obj}."

        # Layer 3: "credited with"
        m = re.search(
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\s+is\s+"
            r"(?:widely\s+|generally\s+)?credited\s+with",
            context,
        )
        if m:
            return f"{m.group(1)} is credited with inventing it."

        # Layer 4: highest inventor-keyword scored sentence
        scored = [(sum(1 for kw in _INVENTOR_KEYWORDS if kw in s.lower()), s)
                  for s in sents]
        scored.sort(reverse=True)
        if scored and scored[0][0] > 0:
            best = ". ".join(scored[0][1].split(". ")[:2]).strip()
            return best if best.endswith(".") else best + "."

        return _compress(context)

    def _capital(self, query: str, context: str) -> str:
        sents = _sentences(context)
        for s in sents:
            if "capital" in s.lower():
                return s
        m = re.search(
            r"capital(?:\s+city)?\s+(?:is|of\s+\w+\s+is)\s+"
            r"([A-Z][a-z]+(?:[\s-][A-Z][a-z]+)*)",
            context, re.I,
        )
        return f"The capital is {m.group(1)}." if m else _compress(context)

    def _attribute(self, context: str, keywords: list[str]) -> str:
        sents = _sentences(context)
        # Prefer sentence that has keyword AND a number
        for s in sents:
            s_lo = s.lower()
            if any(kw in s_lo for kw in keywords) and re.search(r"\d", s):
                return s
        for s in sents:
            if any(kw in s.lower() for kw in keywords):
                return s
        return _compress(context)

    def _date(self, context: str) -> str:
        for s in _sentences(context):
            if _DATE_PATTERN.search(s):
                return s
        return _compress(context)

    def _location(self, context: str) -> str:
        loc_kw = ["located", "situated", "lies in", "is in", "based in", "part of"]
        for s in _sentences(context):
            if any(kw in s.lower() for kw in loc_kw):
                return s
        return _compress(context)

    def _definition(self, context: str) -> str:
        sents = _sentences(context)
        return " ".join(sents[:2]) if sents else _compress(context)
