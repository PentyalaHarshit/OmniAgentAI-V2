"""
ReActGeneralCrew
=================
Proper ReAct + Crew AI pipeline with named agents.

Crew agents
-----------
  1. QueryUnderstandingAgent   – classify question type, extract subject
  2. SearchAgent               – retrieve content (CountryAPI / Wikipedia / WebRAG)
  3. AnalyzerAgent             – extract the specific fact (years, name, number, etc.)
  4. ValidatorAgent            – verify the extracted fact for correctness
  5. FinalAnswerAgent          – compose clean natural-language response

Flow example — "How long did the Chola dynasty rule?"
-----------------------------------------------------
  Thought (QueryUnderstanding): This is a 'duration' question. Subject = 'Chola dynasty'.
  Action  (Search):             Fetch Wikipedia for 'Chola dynasty'.
  Observation:                  Wikipedia returned 2,400 chars about Chola dynasty.
  Thought (Analyzer):           Need ruling period years from text.
  Action  (Analyzer):           Scan for date patterns — found '3rd century BCE', '1279 CE'.
  Observation:                  Start = ~300 BCE, End = 1279 CE, Duration ≈ 1,500+ years.
  Thought (Validator):          Cross-check: do multiple sentences confirm these dates?
  Action  (Validator):          Confirmed in 2 sentences. Confidence = high.
  Final:                        "The Chola dynasty ruled from approximately 300 BCE to
                                 1279 CE — a span of roughly 1,500 years."
"""

import re
import json
import logging
import urllib.parse
import urllib.request

import requests
from bs4 import BeautifulSoup

from tools.general_query_tools import (
    BuiltInFacts, CountryInfoTool, classify_question,
    extract_entity_after_of, normalize_query,
)

logger = logging.getLogger(__name__)

_TIMEOUT = 8
_UA      = "OmniAgentAI/1.0"


# ── Wikipedia helpers ────────────────────────────────────────────────────────

def _wiki_get(url: str) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception as e:
        logger.debug("wiki_get %s: %s", url, e)
        return None


def _wiki_search(query: str, prefer: str = "") -> tuple[str, str]:
    """
    Search Wikipedia, return (page_extract, page_url).
    prefer: if set, prefer a title containing this word.
    """
    data = _wiki_get(
        "https://en.wikipedia.org/w/api.php?"
        + urllib.parse.urlencode({
            "action": "query", "list": "search",
            "srsearch": query, "format": "json", "srlimit": 5,
        })
    )
    if not data:
        return "", ""

    results = data.get("query", {}).get("search", [])
    if not results:
        return "", ""

    # Pick best title
    title = results[0]["title"]
    if prefer:
        # Escape special regex chars so subjects like "c++" match correctly
        prefer_escaped = re.escape(prefer.lower())
        for r in results:
            t = r["title"].lower()
            if re.search(prefer_escaped, t) and "navy" not in t and "art" not in t \
                    and "temple" not in t and "architecture" not in t:
                title = r["title"]
                break

    summary = _wiki_get(
        "https://en.wikipedia.org/api/rest_v1/page/summary/"
        + urllib.parse.quote(title.replace(" ", "_"))
    )
    if not summary:
        return "", ""

    extract  = re.sub(r"\s+", " ", summary.get("extract", "")).strip()
    page_url = summary.get("content_urls", {}).get("desktop", {}).get("page", "")
    return extract, page_url


def _clean_web_text(html: str, max_chars: int = 1800) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    parts = []
    for tag in soup.find_all(["p", "li"], limit=80):
        text = re.sub(r"\s+", " ", tag.get_text(" ", strip=True)).strip()
        if len(text) >= 40:
            parts.append(text)
        if sum(len(p) for p in parts) >= max_chars:
            break
    return " ".join(parts)[:max_chars].strip()


def _web_search_duckduckgo(query: str, max_results: int = 3) -> list[dict]:
    """
    Google-like web fallback using DuckDuckGo HTML.
    Returns readable page snippets from top result pages.
    """
    headers = {"User-Agent": _UA}
    docs: list[dict] = []
    try:
        resp = requests.get(
            "https://duckduckgo.com/html/",
            params={"q": query},
            headers=headers,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.debug("duckduckgo search failed for %s: %s", query, exc)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    for result in soup.select(".result")[: max_results * 2]:
        title_tag = result.select_one(".result__title a")
        snippet_tag = result.select_one(".result__snippet")
        if not title_tag:
            continue

        raw_url = title_tag.get("href", "")
        parsed = urllib.parse.urlparse(raw_url)
        query_params = urllib.parse.parse_qs(parsed.query)
        url = query_params.get("uddg", [raw_url])[0]
        if not url.startswith("http"):
            continue

        title = title_tag.get_text(" ", strip=True)
        snippet = snippet_tag.get_text(" ", strip=True) if snippet_tag else ""
        page_text = ""
        try:
            page_resp = requests.get(url, headers=headers, timeout=_TIMEOUT)
            content_type = page_resp.headers.get("content-type", "")
            if page_resp.ok and "text/html" in content_type:
                page_text = _clean_web_text(page_resp.text)
        except requests.RequestException as exc:
            logger.debug("web page read failed for %s: %s", url, exc)

        text = page_text or snippet
        if not text:
            continue
        docs.append({
            "title": title,
            "url": url,
            "text": text,
            "source": "DuckDuckGo Web",
        })
        if len(docs) >= max_results:
            break
    return docs


# ── Date / year extraction helpers ───────────────────────────────────────────

# Match patterns like "300 BCE", "1279 CE", "3rd century BCE", "13th century CE", "1876"
_YEAR_FULL   = re.compile(r"(\d{1,4})\s*(BCE?|CE|AD)\b", re.I)
_CENTURY     = re.compile(r"(\d+)(?:st|nd|rd|th)\s+century\s*(BCE?|CE|AD)?", re.I)
_PLAIN_YEAR  = re.compile(r"\b(1[0-9]{3}|2[0-9]{3})\b")   # 1000–2999


def _century_to_year(n: int, era: str) -> int:
    """Convert '3rd century BCE' → -300, '13th century CE' → 1200."""
    approx = (n - 1) * 100
    if era and re.search(r"bce?", era, re.I):
        return -approx
    return approx


def _extract_years(text: str) -> list[tuple[int, str]]:
    """
    Return list of (year_as_int, label) pairs from text, sorted chronologically.
    year_as_int: negative = BCE, positive = CE.
    label: original string like "300 BCE", "1279 CE".
    """
    found: list[tuple[int, str]] = []

    for m in _YEAR_FULL.finditer(text):
        n    = int(m.group(1))
        era  = m.group(2).upper()
        val  = -n if "B" in era else n
        found.append((val, m.group(0)))

    for m in _CENTURY.finditer(text):
        n   = int(m.group(1))
        era = (m.group(2) or "CE").upper()
        val = _century_to_year(n, era)
        label = m.group(0).strip()
        found.append((val, label))

    # Avoid duplicating years already captured
    captured_vals = {v for v, _ in found}
    for m in _PLAIN_YEAR.finditer(text):
        v = int(m.group(1))
        if v not in captured_vals:
            found.append((v, m.group(1)))

    found.sort(key=lambda x: x[0])
    return found


def _format_year(val: int, label: str) -> str:
    """Return clean display string for a year."""
    # If we extracted from century pattern, make it more readable
    if "century" in label.lower():
        return label.strip()
    return label.strip()


# ── Crew Agents ──────────────────────────────────────────────────────────────

class QueryUnderstandingAgent:
    """Classifies question and extracts the subject entity."""

    DURATION_RE = re.compile(
        r"\bhow long\b|\bfor how long\b|\bhow many years\b",
        re.I
    )
    INVENTOR_RE = re.compile(
        r"\bwho\s+(invented|discovered|created|built|designed|founded)\b", re.I
    )
    WINNER_RE = re.compile(
        r"\bwho\s+(won|defeated|won the|conquered|beat|lost|won in|"
        r"was victorious|emerged victorious|triumphed)\b",
        re.I
    )
    # "when did X rule/start/begin/end" — a specific date question, NOT duration
    DATE_RE = re.compile(r"\bwhen\s+(did|was|were|is|has)\b", re.I)

    def run(self, query: str) -> dict:
        q = query.strip()

        # ── Winner of battle / war ────────────────────────────────────────
        if self.WINNER_RE.search(q):
            q_type = "winner"
            # Extract the event: "who won the opium war" → "opium war"
            m = re.search(
                r"(?:won|defeated|conquered|beat|won in|lost|triumphed|victorious)"
                r"(?:\s+(?:the|in|at))?\s+(.+)",
                q, re.I
            )
            subject = m.group(1).strip().rstrip("?").strip() if m else re.sub(
                r"^who\s+\w+\s+(?:the\s+)?", "", q, flags=re.I
            ).strip("?").strip()

        # ── Inventor ──────────────────────────────────────────────────────
        elif self.INVENTOR_RE.search(q):
            q_type = "inventor"
            m = re.search(
                r"(?:invented|discovered|created|built|designed|founded)"
                r"\s+(?:the\s+)?(.+)",
                q, re.I
            )
            subject = m.group(1).strip().rstrip("?") if m else q

        # ── Duration: "how long" only (NOT "when did ... rule") ──────────
        elif self.DURATION_RE.search(q):
            q_type = "duration"
            m = re.search(
                r"how long\s+(?:did|was|has|have|were|are)?\s*(?:the\s+)?(.+?)"
                r"\s*(?:rule|ruled|last|lasted|exist|existed|reign|reigned|stand|stood)?[\?\.]?$",
                q, re.I
            )
            if m:
                subject = m.group(1).strip()
            else:
                subject = re.sub(
                    r"^how long\s+(?:did|was|has)?\s*(?:the\s+)?", "", q, flags=re.I
                ).strip()

        # ── Date: "when did X" ─────────────────────────────────────────────
        elif self.DATE_RE.search(q):
            q_type = "date"
            # Extract the meaningful subject: "when did british rule India" → "British rule India"
            # Keep what comes after "when did/was/were" — that IS the search subject
            subject = re.sub(
                r"^when\s+(?:did|was|were|is|has)\s+(?:the\s+)?", "", q, flags=re.I
            ).strip().rstrip("?").strip()
            # For "when did british rule/ruled India" → search subject = "British rule India"
            # Normalise verb forms
            subject = re.sub(r"\bruled\b", "rule", subject, flags=re.I)

        else:
            q_type  = "general"
            subject = q

        return {
            "question_type": q_type,
            "subject":       subject,
            "original":      query,
        }


class SearchAgent:
    """Retrieves content from Wikipedia for the subject."""

    # Common query cruft that should be stripped before Wikipedia search
    _STRIP_RE = re.compile(
        r"\b(got|get|gain|gained|did|was|were|has|have|is|are|when|how long|"
        r"the|a|an|please|tell me|explain)\b",
        re.I
    )

    # Map common informal phrasings to proper Wikipedia search terms
    _REMAP = [
        (re.compile(r"\b(usa|u\.s\.a|united states|america)\b.*\bindepend", re.I),
         "United States Declaration of Independence 1776"),
        (re.compile(r"\bindia\b.*\bindepend", re.I),
         "Indian independence 1947"),
        (re.compile(r"\bpakistan\b.*\bindepend", re.I),
         "Pakistan independence 1947"),
        (re.compile(r"\bfrench revolution\b", re.I),
         "French Revolution history"),
        (re.compile(r"\bberlin wall\b", re.I),
         "Berlin Wall fall 1989"),
        (re.compile(r"\bsoviet union\b.*(collaps|end|dissolv)", re.I),
         "Dissolution of the Soviet Union"),
        (re.compile(r"\btitanic\b.*(sink|sank)", re.I),
         "RMS Titanic sinking 1912"),
        (re.compile(r"\bmoon landing\b|\bapollo 11\b", re.I),
         "Apollo 11 Moon landing 1969"),
        (re.compile(r"\bchola\b.*(dynasty|empire|kingdom|rule)", re.I),
         "Chola dynasty history period"),
        (re.compile(r"\bbritish\b.*\bindia\b", re.I),
         "British Raj India 1858 1947"),
        (re.compile(r"\bopium war\b", re.I),
         "First Opium War 1839 1842"),
        (re.compile(r"\b1971\b.*\b(india|pakistan)\b|\b(india|pakistan)\b.*\b1971\b", re.I),
         "Indo-Pakistani War 1971"),
        # Programming languages & tech inventions
        (re.compile(r"\bc\+\+", re.I),
         "C++ programming language Bjarne Stroustrup"),
        (re.compile(r"\bc#|csharp", re.I),
         "C sharp programming language Anders Hejlsberg Microsoft"),
        (re.compile(r"\bpython\b.*(language|programming|invent|creat)", re.I),
         "Python programming language Guido van Rossum"),
        (re.compile(r"\bjava\b.*(language|programming|invent|creat)", re.I),
         "Java programming language James Gosling"),
        (re.compile(r"\bjavascript\b", re.I),
         "JavaScript programming language Brendan Eich"),
        (re.compile(r"\blua\b.*(language|programming|invent|creat)", re.I),
         "Lua programming language Roberto Ierusalimschy"),
        (re.compile(r"\bruby\b.*(language|programming|invent|creat)", re.I),
         "Ruby programming language Yukihiro Matsumoto"),
        (re.compile(r"\brust\b.*(language|programming|invent|creat)", re.I),
         "Rust programming language Graydon Hoare Mozilla"),
        (re.compile(r"\bgolang\b|\bgo\b.*(language|programming|invent|creat)", re.I),
         "Go programming language Google Rob Pike Ken Thompson"),
        (re.compile(r"\bswift\b.*(language|programming|invent|creat)", re.I),
         "Swift programming language Apple Chris Lattner"),
        (re.compile(r"\bkotlin\b.*(language|programming|invent|creat)", re.I),
         "Kotlin programming language JetBrains"),
        (re.compile(r"\btypescript\b", re.I),
         "TypeScript programming language Microsoft Anders Hejlsberg"),
        (re.compile(r"\bphp\b.*(language|programming|invent|creat)", re.I),
         "PHP programming language Rasmus Lerdorf"),
        (re.compile(r"\bperl\b.*(language|programming|invent|creat)", re.I),
         "Perl programming language Larry Wall"),
        (re.compile(r"\bscala\b.*(language|programming|invent|creat)", re.I),
         "Scala programming language Martin Odersky"),
        (re.compile(r"\bhaskell\b.*(language|programming|invent|creat)", re.I),
         "Haskell programming language history"),
        (re.compile(r"\binternet\b.*(invent|creat|found)", re.I),
         "History of the Internet"),
        (re.compile(r"\bworld wide web\b|\bwww\b.*(invent|creat)", re.I),
         "World Wide Web Tim Berners-Lee invention"),
        (re.compile(r"\btelephone\b.*(invent|creat)", re.I),
         "Telephone invention Alexander Graham Bell"),
        (re.compile(r"\belectricity\b.*(invent|discov)", re.I),
         "Electricity discovery history"),
    ]

    def _clean_subject(self, subject: str, question_type: str) -> str:
        """
        Map informal subject strings to proper Wikipedia search queries.
        e.g. "usa got independence day" → "United States Declaration of Independence 1776"
        """
        for pattern, replacement in self._REMAP:
            if pattern.search(subject):
                return replacement

        # Generic clean: strip filler words, keep nouns
        cleaned = self._STRIP_RE.sub(" ", subject).strip()
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()

        if question_type == "duration":
            return f"{cleaned} history ruled period"
        if question_type == "inventor":
            return f"{cleaned} invention history"
        return cleaned or subject

    def run(self, subject: str, question_type: str) -> dict:
        search_q = self._clean_subject(subject, question_type)
        # For inventor questions use the full subject as the prefer hint (e.g. "c++")
        # For others use first word only
        if question_type == "inventor":
            prefer = subject.strip().rstrip("?")
        else:
            prefer = subject.split()[0] if subject else ""
        extract, page_url = _wiki_search(search_q, prefer=prefer)
        if extract:
            return {
                "text":    extract,
                "url":     page_url,
                "source":  "Wikipedia",
                "subject": subject,
                "chars":   len(extract),
                "docs":    [],
            }

        web_docs = _web_search_duckduckgo(search_q, max_results=3)
        web_text = "\n\n".join(
            f"{doc.get('title', '')}: {doc.get('text', '')}"
            for doc in web_docs
        ).strip()
        first_url = web_docs[0].get("url", "") if web_docs else ""
        return {
            "text":    web_text,
            "url":     first_url,
            "source":  "DuckDuckGo Web",
            "subject": subject,
            "chars":   len(web_text),
            "docs":    web_docs,
        }


class AnalyzerAgent:
    """Extracts the specific factual answer from retrieved text."""

    def run(self, query: str, question_type: str, subject: str, text: str) -> dict:
        if not text:
            return {"answer": "", "years": [], "confidence": 0.0}

        if question_type == "winner":
            return self._analyze_winner(query, subject, text)
        if question_type == "duration":
            return self._analyze_duration(subject, text)
        if question_type == "inventor":
            return self._analyze_inventor(query, text)
        if question_type == "date":
            return self._analyze_date(text)
        # General: return first 2 relevant sentences
        return self._analyze_general(query, text)

    # ── Duration analysis ────────────────────────────────────────────────

    def _analyze_duration(self, subject: str, text: str) -> dict:
        years = _extract_years(text)

        if len(years) < 2:
            # Try to get at least start or end from sentences
            sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
            for s in sents:
                y = _extract_years(s)
                if y:
                    years = y
                    break

        if not years:
            return {"answer": _compress(text, 2), "years": [], "confidence": 0.2}

        start_val, start_lbl = years[0]
        end_val,   end_lbl   = years[-1]

        # Duration in years (absolute difference)
        span = abs(end_val - start_val)

        start_str = _format_year(start_val, start_lbl)
        end_str   = _format_year(end_val,   end_lbl)

        # Convert numeric year to readable label if needed
        if re.fullmatch(r"\d+", start_str):
            start_str = f"{start_str} CE"
        if re.fullmatch(r"\d+", end_str):
            end_str   = f"{end_str} CE"

        answer = (
            f"The {subject} ruled from approximately **{start_str}** to **{end_str}** — "
            f"a span of roughly **{span:,} years**."
        )

        return {
            "answer":     answer,
            "start":      start_str,
            "end":        end_str,
            "span_years": span,
            "years":      [(v, l) for v, l in years],
            "confidence": 0.9 if len(years) >= 2 else 0.5,
        }

    # ── Inventor analysis ────────────────────────────────────────────────

    # Matches full names including lowercase particles: "Guido van Rossum", "Bjarne Stroustrup"
    # Format: Capital word, optionally followed by lowercase particles (van/de/von/el/bin/al)
    # and/or more Capital words, up to 5 parts total.
    _NAME_RE = (
        r"([A-Z][a-zA-Z\-]+"                        # First name (must start with capital)
        r"(?:\s+(?:van|de|von|el|bin|al|le|du)\b)?" # optional lowercase particle
        r"(?:\s+[A-Z][a-zA-Z\-]+){0,3})"            # up to 3 more capitalized words
    )

    def _analyze_inventor(self, query: str, text: str) -> dict:
        # Extract subject from query for use in the answer (e.g. "c++" from "who invented c++")
        m_subj = re.search(
            r"(?:invented|discovered|created|built|designed|founded)"
            r"\s+(?:the\s+)?(.+)",
            query, re.I
        )
        subject_label = m_subj.group(1).strip().rstrip("?") if m_subj else "it"

        # Build a set of words from the subject to exclude — e.g. "lua", "python", "c++"
        # so the language name itself isn't mistaken for the inventor's name.
        subject_words = set(re.findall(r"[a-z]+", subject_label.lower()))

        def _is_not_subject(name: str) -> bool:
            """Return True if the captured name is NOT just the subject/language name."""
            name_words = set(re.findall(r"[a-z]+", name.lower()))
            # Reject single-word names that exactly match a subject word (e.g. "Lua", "Python")
            if len(name_words) == 1 and name_words & subject_words:
                return False
            return True

        # Pattern 1: passive "invented/created/developed by <Name>"
        for m in re.finditer(
            r"(?:invented|created|patented|developed|discovered|founded|designed)"
            r"\s+by\s+" + self._NAME_RE,
            text
        ):
            if _is_not_subject(m.group(1)):
                return {"answer": f"**{m.group(1)}** invented {subject_label}.", "confidence": 0.9, "years": []}

        # Pattern 2: active "<Name> invented/created/developed"
        for m in re.finditer(
            self._NAME_RE
            + r"\s+(?:invented|created|patented|developed|discovered|founded|designed)\b",
            text
        ):
            if _is_not_subject(m.group(1)):
                return {"answer": f"**{m.group(1)}** invented {subject_label}.", "confidence": 0.9, "years": []}

        # Pattern 3: "<Name> began working on / started / introduced"
        for m in re.finditer(
            self._NAME_RE
            + r"\s+(?:began|started|introduced|proposed|conceived|initiated)\b",
            text
        ):
            if _is_not_subject(m.group(1)):
                return {"answer": f"**{m.group(1)}** invented {subject_label}.", "confidence": 0.85, "years": []}

        # Pattern 4: "credited with"
        for m in re.finditer(
            self._NAME_RE
            + r"\s+is\s+(?:widely\s+|generally\s+)?credited\s+with",
            text
        ):
            if _is_not_subject(m.group(1)):
                return {"answer": f"**{m.group(1)}** is credited with inventing {subject_label}.", "confidence": 0.8, "years": []}

        # Pattern 5: "<Name> is a ... programmer/scientist who created/developed"
        for m in re.finditer(
            self._NAME_RE
            + r"[^.]{0,80}(?:who\s+)?(?:created|developed|invented|designed|built)\b",
            text
        ):
            if _is_not_subject(m.group(1)):
                return {"answer": f"**{m.group(1)}** invented {subject_label}.", "confidence": 0.75, "years": []}

        return {"answer": _compress(text, 2), "confidence": 0.4, "years": []}

    def _analyze_date(self, text: str) -> dict:
        """
        For 'when did X rule/happen' — find sentences that describe
        a specific time range (start year → end year) in the text.

        Strategy:
          1. Find sentences containing ruling/period keywords + two years
          2. Return those years as the answer
          3. Fall back to first date-containing sentence
        """
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 15]

        PERIOD_KW = [
            "ruled", "reign", "reigned", "period", "from", "until",
            "established", "founded", "controlled", "governed",
            "colonized", "annexed", "independence", "ended", "began",
        ]

        # Find sentences with period keywords AND at least one year
        candidate_sents = []
        for s in sents:
            s_lo = s.lower()
            has_kw   = any(kw in s_lo for kw in PERIOD_KW)
            has_year = bool(_YEAR_FULL.search(s) or _PLAIN_YEAR.search(s))
            if has_kw and has_year:
                years_in_s = _extract_years(s)
                candidate_sents.append((len(years_in_s), s, years_in_s))

        # Sort by number of years found (prefer sentences with 2+ years = a range)
        candidate_sents.sort(reverse=True)

        if candidate_sents:
            _, best_sent, years = candidate_sents[0]
            if len(years) >= 2:
                start_val, start_lbl = years[0]
                end_val,   end_lbl   = years[-1]
                start_str = _format_year(start_val, start_lbl)
                end_str   = _format_year(end_val, end_lbl)
                if re.fullmatch(r"\d+", start_str):
                    start_str += " CE"
                if re.fullmatch(r"\d+", end_str):
                    end_str += " CE"
                span = abs(end_val - start_val)
                answer = (
                    f"This occurred from **{start_str}** to **{end_str}** "
                    f"(approximately {span} years)."
                )
                return {"answer": answer, "confidence": 0.85, "years": years}
            elif len(years) == 1:
                val, lbl = years[0]
                answer = f"This occurred around **{_format_year(val, lbl)}**."
                return {"answer": answer, "confidence": 0.65, "years": years}
            else:
                return {"answer": best_sent, "confidence": 0.5, "years": []}

        # Final fallback: first sentence with any date
        for s in sents:
            years = _extract_years(s)
            if years:
                val, lbl = years[0]
                return {
                    "answer":     f"This occurred around **{_format_year(val, lbl)}**.",
                    "confidence": 0.4,
                    "years":      years,
                }

        return {"answer": _compress(text, 1), "confidence": 0.3, "years": []}

    # ── Winner analysis ──────────────────────────────────────────────────

    def _analyze_winner(self, query: str, subject: str, text: str) -> dict:
        """
        Find who won a battle/war by scanning for victory/defeat sentences.

        Looks for patterns like:
          "British Empire won the First Opium War"
          "China was defeated by Britain"
          "Treaty of Nanking, signed by China, ended the war"
          "resulted in a British victory"
          "X emerged victorious"
        """
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 15]

        VICTORY_KW = [
            "won", "victory", "victorious", "defeated", "surrendered",
            "triumphed", "emerged victorious", "forced to sign",
            "result", "outcome", "ended with", "concluded with",
            "gave up", "ceded", "forced to", "compelled",
        ]

        # Score sentences by victory keywords
        scored: list[tuple[int, str]] = []
        for s in sents:
            s_lo = s.lower()
            hits = sum(1 for kw in VICTORY_KW if kw in s_lo)
            if hits:
                scored.append((hits, s))

        scored.sort(reverse=True)

        if scored:
            best = scored[0][1]
            # Try to extract the winner name from patterns like:
            # "resulted in a British victory" / "Britain won" / "defeated by Britain"
            patterns = [
                # "X victory" or "victory for X"
                r"([A-Z][a-zA-Z\s]+?)\s+(?:victory|won|triumphed)",
                r"victory\s+(?:for|of)\s+([A-Z][a-zA-Z\s]+)",
                # "defeated <loser>" — winner is subject of sentence
                r"([A-Z][a-zA-Z\s]+?)\s+defeated\b",
                # "<loser> was defeated by <winner>"
                r"defeated\s+by\s+([A-Z][a-zA-Z\s]+)",
                # "X emerged victorious"
                r"([A-Z][a-zA-Z\s]+?)\s+emerged\s+victorious",
                # "forced <loser> to sign" — subject = winner
                r"([A-Z][a-zA-Z\s]+?)\s+forced\b",
            ]
            winner = ""
            for pat in patterns:
                m = re.search(pat, best)
                if m:
                    candidate = m.group(1).strip()
                    # Sanity: must be a proper noun (starts with capital, reasonable length)
                    if re.match(r"[A-Z]", candidate) and 2 < len(candidate) < 50:
                        winner = candidate
                        break

            if winner:
                event = subject.title()
                answer = f"**{winner}** won the {event}.\n\n_{best}_"
            else:
                # Return the best victory sentence directly
                answer = best

            return {"answer": answer, "confidence": 0.85, "years": []}

        # Fallback: return the most relevant sentences
        return {"answer": _compress(text, 2), "confidence": 0.3, "years": []}

    # ── General analysis ─────────────────────────────────────────────────

    def _analyze_general(self, query: str, text: str) -> dict:
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 15]
        q_words = set(re.findall(r"[a-z]+", query.lower()))
        scored = sorted(sents, key=lambda s: len(q_words & set(re.findall(r"[a-z]+", s.lower()))), reverse=True)
        answer = " ".join(scored[:2]) if scored else _compress(text, 2)
        return {"answer": answer, "confidence": 0.5, "years": []}


class ValidatorAgent:
    """Cross-checks the extracted answer and assigns confidence."""

    def run(self, question_type: str, analysis: dict, text: str, query: str) -> dict:
        answer     = analysis.get("answer", "")
        confidence = analysis.get("confidence", 0.5)

        if not answer:
            return {
                "valid":      False,
                "confidence": 0.0,
                "reason":     "No answer extracted.",
                "corrected":  "",
            }

        # For duration questions, verify dates appear in source text
        if question_type == "duration" and analysis.get("years"):
            confirmed = 0
            for val, lbl in analysis["years"]:
                # Check numeric part appears in text
                num_part = re.search(r"\d+", lbl)
                if num_part and num_part.group() in text:
                    confirmed += 1
            if confirmed >= 2:
                confidence = min(confidence + 0.1, 1.0)
                reason = f"Dates confirmed in source text ({confirmed} references)."
            elif confirmed == 1:
                reason = "Partial date confirmation."
            else:
                confidence = max(confidence - 0.2, 0.1)
                reason = "Dates not directly confirmed in source."
        else:
            reason = "Answer extracted. Source content available."

        # Basic sanity: reject answers that are clearly about wrong topic
        wrong_topics = ["navy", "ship", "vessel", "temple", "sculpture", "art of"]
        if question_type not in ("winner", "inventor") and any(t in answer.lower() for t in wrong_topics):
            return {
                "valid":      False,
                "confidence": 0.0,
                "reason":     "Answer appears to be about wrong topic.",
                "corrected":  "",
            }

        return {
            "valid":      True,
            "confidence": round(confidence, 2),
            "reason":     reason,
            "corrected":  answer,
        }


class FinalAnswerAgent:
    """Composes the final user-facing response."""

    def run(
        self,
        question_type: str,
        subject: str,
        analysis: dict,
        validation: dict,
        source_url: str,
        original_query: str,
    ) -> str:
        if not validation.get("valid") or not validation.get("corrected"):
            return (
                f"I couldn't find a verified answer for: **\"{original_query}\"**\n\n"
                "Try rephrasing with more specific terms."
            )

        answer = validation["corrected"]

        # Fix answers that echo the raw query as subject
        # e.g. "The when did british ruled in india? ruled from..." → fix subject
        if answer.lower().startswith("the when") or answer.lower().startswith("the how"):
            # Rebuild a clean answer using the subject
            years = analysis.get("years", [])
            if len(years) >= 2:
                start_str = _format_year(years[0][0], years[0][1])
                end_str   = _format_year(years[-1][0], years[-1][1])
                if re.fullmatch(r"\d+", start_str): start_str += " CE"
                if re.fullmatch(r"\d+", end_str):   end_str   += " CE"
                span = abs(years[-1][0] - years[0][0])
                answer = (
                    f"The **{subject.title()}** lasted from **{start_str}** "
                    f"to **{end_str}** — approximately **{span:,} years**."
                )

        # Add source attribution
        src = ""
        if source_url:
            title = subject.title()
            src = f"\n\n📖 *Source: [{title} — Wikipedia]({source_url})*"

        return answer + src


# ── Helpers ──────────────────────────────────────────────────────────────────

def _compress(text: str, n: int = 2) -> str:
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 15]
    return " ".join(sents[:n]).strip()


# ── ReActGeneralCrew ─────────────────────────────────────────────────────────

class ReActGeneralCrew:
    """
    Orchestrates the 5-agent ReAct crew:
      QueryUnderstandingAgent → SearchAgent → AnalyzerAgent →
      ValidatorAgent → FinalAnswerAgent
    """

    def __init__(self, mcp=None):
        self.mcp          = mcp
        self.country_tool = CountryInfoTool()
        self.facts        = BuiltInFacts()
        # Crew agents
        self.query_agent  = QueryUnderstandingAgent()
        self.search_agent = SearchAgent()
        self.analyzer     = AnalyzerAgent()
        self.validator    = ValidatorAgent()
        self.final_agent  = FinalAnswerAgent()

    def run(self, query: str) -> dict:
        steps: list[dict] = []

        def step(agent: str, thought: str, output=None):
            steps.append({"agent": agent, "thought": thought, "output": output})

        # ── Agent 1: Query Understanding ──────────────────────────────────
        understanding = self.query_agent.run(query)
        q_type  = understanding["question_type"]
        subject = understanding["subject"]

        step("QueryUnderstandingAgent",
             f"Thought: Question type = '{q_type}'. Subject = '{subject}'.",
             understanding)

        # ── Built-in facts shortcut ───────────────────────────────────────
        fact = self.facts.lookup(normalize_query(query))
        if fact:
            step("BuiltInFactAgent", "Thought: Matched built-in verified fact.")
            verification = {
                "verified": True,
                "confidence": 1.0,
                "reason": "Matched curated built-in fact.",
                "corrected": fact,
                "sources_used": 1,
            }
            return self._result(steps, fact, "built_in_facts", verification)

        # ── Country API shortcut for capital / population / currency ──────
        if q_type in ("capital", "population", "currency"):
            country = extract_entity_after_of(normalize_query(query), q_type)
            step("SearchAgent",
                 f"Thought: Calling CountryInfoTool for {q_type} of '{country}'.",
                 None)
            step("SearchAgent",
                 f"Action: GET https://restcountries.com/v3.1/name/{country}")
            info = self.country_tool.get_country(country)
            step("ObservationAgent",
                 f"Observation: CountryInfoTool returned: {info}")
            if info:
                answer = self._format_country(q_type, info)
                step("FinalAnswerAgent", f"Answer: {answer[:160]}")
                verification = {
                    "verified": True,
                    "confidence": 0.9,
                    "reason": "Returned by CountryInfoTool.",
                    "corrected": answer,
                    "sources_used": 1,
                }
                return self._result(steps, answer, "country_info_tool", verification)
            step("SearchAgent",
                 f"Observation: CountryInfoTool returned nothing. Falling back to Wikipedia.")

        # ── Agent 2: Search ───────────────────────────────────────────────
        step("SearchAgent",
             f"Thought: Need to retrieve content about '{subject}' ({q_type} question).")
        step("SearchAgent",
             f"Action: Search Wikipedia for '{subject}'.")

        search_result = self.search_agent.run(subject, q_type)
        text      = search_result["text"]
        page_url  = search_result["url"]
        source    = search_result.get("source", "Wikipedia")
        web_docs  = search_result.get("docs", [])

        step("ObservationAgent",
             f"Observation: {source} returned {search_result['chars']} chars. "
             f"URL: {page_url[:80]}",
             {"chars": search_result["chars"], "url": page_url, "source": source, "docs": web_docs})

        if not text:
            # MCP fallback
            step("SearchAgent",
                 "Observation: Wikipedia empty. Trying MCP chain (DDG → Wikipedia → Wikimedia).")
            if self.mcp:
                mcp_result = self.mcp.run(query)
                text       = mcp_result.get("answer", "")
                step("ObservationAgent",
                     f"Observation: MCP returned {len(text)} chars via "
                     f"'{mcp_result.get('tool_used', '')}'.")

        if not text:
            step("FinalAnswerAgent",
                 "Observation: No content retrieved. Cannot answer.")
            return self._result(steps, "", "")

        # ── Agent 3: Analyzer ─────────────────────────────────────────────
        step("AnalyzerAgent",
             f"Thought: Analyze retrieved content to extract {q_type} answer for '{subject}'.")

        analysis = self.analyzer.run(query, q_type, subject, text)

        step("AnalyzerAgent",
             f"Action: Extracted → \"{analysis.get('answer', '')[:160]}\"",
             {k: v for k, v in analysis.items() if k != "answer"})

        # ── Agent 4: Validator ────────────────────────────────────────────
        step("ValidatorAgent",
             f"Thought: Validate extracted answer. "
             f"Confidence before = {analysis.get('confidence', 0.5)}.")

        validation = self.validator.run(q_type, analysis, text, query)

        step("ValidatorAgent",
             f"Observation: valid={validation['valid']}, "
             f"confidence={validation['confidence']}, "
             f"reason='{validation['reason']}'",
             validation)

        # ── Agent 5: Final Answer ─────────────────────────────────────────
        step("FinalAnswerAgent",
             "Thought: Composing final natural-language response.")

        final = self.final_agent.run(
            q_type, subject, analysis, validation, page_url, query
        )

        step("FinalAnswerAgent", f"Answer: {final[:200]}", final[:200])

        verification = {
            "verified": validation.get("valid", False),
            "confidence": validation.get("confidence", 0.0),
            "reason": validation.get("reason", ""),
            "corrected": validation.get("corrected", final),
            "sources_used": 1 if page_url else 0,
        }
        tool_used = "wikipedia_react_crew" if source == "Wikipedia" else "web_react_crew"
        return self._result(steps, final, tool_used, verification)

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _format_country(q_type: str, info: dict) -> str:
        name = info.get("name", "Unknown")
        src  = "\n\n🌐 Source: RestCountries API"
        if q_type == "capital":
            return f"The capital of {name} is **{info.get('capital', 'Unknown')}**.{src}"
        if q_type == "population":
            pop = info.get("population")
            return (
                f"{name} has a population of approximately **{pop:,}** people.{src}"
                if pop else
                f"I found {name}, but population data was unavailable.{src}"
            )
        if q_type == "currency":
            cur = ", ".join(info.get("currencies") or ["Unknown"])
            return f"The currency of {name} is **{cur}**.{src}"
        return str(info)

    @staticmethod
    def _result(steps: list, answer: str, tool: str, verification: dict | None = None) -> dict:
        return {
            "crew_name":   "ReActGeneralCrew",
            "crew_steps":  steps,
            "answer":      answer,
            "tool_used":   tool,
            "all_results": [{"tool": tool, "result": answer}] if answer else [],
            "verification": verification or {},
        }
