import re
import os
import json
import urllib.parse
from pathlib import Path

import requests
from agents.base_agent import BaseAgent


class QuizAgent(BaseAgent):
    name = "QuizAgent"
    agent_type = "Quiz"
    base_tasks = [
        "Detect multiple-choice question",
        "Parse answer options",
        "Find correct answer",
        "Generate explanation",
        "Score confidence",
    ]

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        thoughts = self.tot.create_thoughts(self.agent_type, query, self.base_tasks)
        options = self.parse_options(query)
        local_match = self.lookup_local_knowledge(query, options)
        evidence: list[dict] = []
        if local_match["confidence"] > 0.9:
            answer = self.answer_from_knowledge_record(local_match["record"], options)
            source_stage = "quiz_local_knowledge"
            confidence = local_match["confidence"]
            thoughts.append("QuizKnowledgeDB: high-confidence local match; answered directly.")
        elif local_match["confidence"] > 0.6:
            evidence = self.retrieve_evidence(query)
            answer = self.answer_mcq(query, options, evidence, local_match)
            source_stage = "quiz_knowledge_web_verified"
            confidence = local_match["confidence"]
            thoughts.append("QuizKnowledgeDB: medium-confidence local match; verified with web evidence.")
        else:
            evidence = self.retrieve_evidence(query)
            answer = self.answer_mcq(query, options, evidence, {"record": None, "confidence": local_match["confidence"]})
            source_stage = "quiz_reasoning"
            confidence = local_match["confidence"]
            thoughts.append("QuizKnowledgeDB: no strong local match; searched web evidence.")
        return self.response(query, thoughts + [
            f"QuizAgent: detected {len(options)} option(s).",
            f"WebSearchAgent: retrieved {len(evidence)} evidence snippet(s).",
            "QuizAgent: generated answer, explanation, and distractor analysis.",
        ], answer, {
            "slot_filling": False,
            "source_stage": source_stage,
            "pipeline": [
                "detect_mcq",
                "local_knowledge_check",
                "confidence_gate",
                "api_web_search_if_needed",
                "detect_answer_from_sources",
                "generate_explanation",
                "score",
            ],
            "options": options,
            "evidence": evidence[:3],
            "local_match": {
                "confidence": local_match["confidence"],
                "id": local_match["record"].get("id") if local_match["record"] else None,
                "category": local_match["record"].get("category") if local_match["record"] else "",
            },
            "score": 1.0 if "Correct Answer:" in answer else confidence,
        })

    def __init__(self, quiz_db_path: str = "knowledge/quiz/quiz_db.json"):
        super().__init__()
        self.quiz_db_path = Path(quiz_db_path)
        self.quiz_knowledge = self.load_quiz_knowledge(self.quiz_db_path)

    def answer_mcq(
        self,
        query: str,
        options: dict[str, str],
        evidence: list[dict] | None = None,
        local_match: dict | None = None,
    ) -> str:
        detected = self.detect_answer_from_evidence(query, options, evidence or [])
        if detected:
            letter, value = detected
            explanation = self.explanation_for_detected_answer(query, options, letter, value)
            return (
                f"Correct Answer: {letter}) {value}\n\n"
                "Explanation:\n"
                f"{explanation}\n\n"
                "Why others are wrong:\n"
                f"{self.why_others_are_wrong(query, options, letter)}"
            )

        record = (local_match or {}).get("record")
        if record:
            return self.answer_from_knowledge_record(record, options)

        if options:
            return (
                "I detected this as a multiple-choice quiz, but I could not confidently determine the correct option "
                "from web evidence or local quiz knowledge. Please provide source material."
            )

        return (
            "I detected a quiz-style question, but I could not parse the answer choices. "
            "Please provide options like A), B), C), and D)."
        )

    @staticmethod
    def load_quiz_knowledge(path: Path) -> list[dict]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def lookup_local_knowledge(self, query: str, options: dict[str, str]) -> dict:
        question = self.question_without_options(query).lower()
        question_tokens = self.content_tokens(question)
        best = {"record": None, "confidence": 0.0}
        for record in self.quiz_knowledge:
            keywords = [kw.lower() for kw in record.get("keywords", [])]
            keyword_hit = any(keyword in question for keyword in keywords)
            record_tokens = self.content_tokens(" ".join([record.get("question", ""), *keywords]))
            overlap = len(question_tokens & record_tokens)
            token_score = overlap / max(1, min(len(question_tokens), len(record_tokens)))
            answer_present = self.record_answer_in_options(record, options)
            option_score = 0.2 if answer_present else 0.0
            confidence = min(1.0, (0.8 if keyword_hit else 0.0) + token_score * 0.25 + option_score)
            if confidence > best["confidence"]:
                best = {"record": record, "confidence": round(confidence, 3)}
        return best

    @staticmethod
    def content_tokens(text: str) -> set[str]:
        stopwords = {
            "a", "an", "and", "are", "for", "in", "is", "of", "on", "the",
            "to", "used", "which", "what", "who", "with", "internally",
        }
        return {
            token
            for token in re.findall(r"[a-z0-9]+", text.lower())
            if token not in stopwords
        }

    @staticmethod
    def record_answer_in_options(record: dict, options: dict[str, str]) -> bool:
        answer_text = (record.get("answer_text") or "").lower()
        answer_letter = (record.get("answer") or "").upper()
        return any(
            answer_text == value.lower()
            or answer_text in value.lower()
            or (letter == answer_letter and answer_text in value.lower())
            for letter, value in options.items()
        )

    def answer_from_knowledge_record(self, record: dict, options: dict[str, str]) -> str:
        answer_letter = self.resolve_answer_letter(record, options)
        answer_text = options.get(answer_letter) or record.get("answer_text", "")
        return (
            f"Correct Answer: {answer_letter}) {answer_text}\n\n"
            "Explanation:\n"
            f"{record.get('explanation', '').strip()}\n\n"
            "Why others are wrong:\n"
            f"{self.wrong_options_from_record(record, options, answer_letter)}"
        )

    def resolve_answer_letter(self, record: dict, options: dict[str, str]) -> str:
        answer_letter = (record.get("answer") or "").upper()
        answer_text = record.get("answer_text", "")
        if answer_letter in options and self.option_matches_answer(options[answer_letter], answer_text):
            return answer_letter
        matched = self.find_option_letter(options, answer_text)
        if matched:
            return matched
        matched = self.find_option_containing(options, [answer_text.lower()])
        if matched:
            return matched
        return answer_letter or "?"

    @staticmethod
    def option_matches_answer(option: str, answer_text: str) -> bool:
        option = option.lower()
        answer_text = answer_text.lower()
        return option == answer_text or answer_text in option or option in answer_text

    @staticmethod
    def wrong_options_from_record(record: dict, options: dict[str, str], answer_letter: str) -> str:
        wrong = record.get("wrong", {})
        lines = []
        for letter, value in sorted(options.items()):
            if letter == answer_letter:
                continue
            reason = wrong.get(value) or wrong.get(value.lower()) or "Not the best answer for this question."
            lines.append(f"{letter}) {value} -> {reason}")
        return "\n".join(lines)

    def retrieve_evidence(self, query: str) -> list[dict]:
        search_query = self.build_search_query(query, self.parse_options(query))
        if not search_query:
            return []

        for provider in (
            self.search_tavily,
            self.search_serpapi,
            self.search_bing,
            self.search_google_custom_search,
        ):
            docs = provider(search_query)
            if docs:
                return docs[:5]
        return []

    @staticmethod
    def build_search_query(query: str, options: dict[str, str]) -> str:
        question = QuizAgent.question_without_options(query)
        option_text = " ".join(options.values())
        return re.sub(r"\s+", " ", f"{question} {option_text}").strip()

    @staticmethod
    def search_tavily(query: str) -> list[dict]:
        api_key = os.getenv("TAVILY_API_KEY", "").strip()
        if not api_key:
            return []
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={"api_key": api_key, "query": query, "max_results": 5},
                timeout=8,
            )
            response.raise_for_status()
            items = response.json().get("results", [])
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                    "source": "Tavily",
                }
                for item in items
            ]
        except Exception:
            return []

    @staticmethod
    def search_serpapi(query: str) -> list[dict]:
        api_key = os.getenv("SERPAPI_API_KEY", "").strip()
        if not api_key:
            return []
        try:
            response = requests.get(
                "https://serpapi.com/search.json",
                params={"engine": "google", "q": query, "num": 5, "api_key": api_key},
                timeout=8,
            )
            response.raise_for_status()
            items = response.json().get("organic_results", [])
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "SerpAPI",
                }
                for item in items
            ]
        except Exception:
            return []

    @staticmethod
    def search_bing(query: str) -> list[dict]:
        api_key = os.getenv("BING_SEARCH_API_KEY", "").strip()
        endpoint = os.getenv("BING_SEARCH_ENDPOINT", "https://api.bing.microsoft.com/v7.0/search").strip()
        if not api_key:
            return []
        try:
            response = requests.get(
                endpoint,
                params={"q": query, "count": 5, "textDecorations": False, "textFormat": "Raw"},
                headers={"Ocp-Apim-Subscription-Key": api_key},
                timeout=8,
            )
            response.raise_for_status()
            items = response.json().get("webPages", {}).get("value", [])
            return [
                {
                    "title": item.get("name", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "Bing Search API",
                }
                for item in items
            ]
        except Exception:
            return []

    @staticmethod
    def search_google_custom_search(query: str) -> list[dict]:
        api_key = os.getenv("GOOGLE_CSE_API_KEY", "").strip()
        cx = os.getenv("GOOGLE_CSE_ID", "").strip()
        if not api_key or not cx:
            return []
        try:
            url = "https://www.googleapis.com/customsearch/v1?" + urllib.parse.urlencode({
                "key": api_key,
                "cx": cx,
                "q": query,
                "num": 5,
            })
            response = requests.get(url, timeout=8)
            response.raise_for_status()
            items = response.json().get("items", [])
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "Google Custom Search API",
                }
                for item in items
            ]
        except Exception:
            return []

    @staticmethod
    def detect_answer_from_evidence(
        query: str,
        options: dict[str, str],
        evidence: list[dict],
    ) -> tuple[str, str] | None:
        if not options or not evidence:
            return None

        question_text = QuizAgent.question_without_options(query).lower()
        question_terms = set(re.findall(r"[a-z0-9]+", question_text))
        scores: dict[str, int] = {letter: 0 for letter in options}
        for doc in evidence:
            text = f"{doc.get('title', '')} {doc.get('snippet', '')} {doc.get('text', '')}".lower()
            for letter, option in options.items():
                option_terms = set(re.findall(r"[a-z0-9]+", option.lower()))
                if not option_terms:
                    continue
                option_hits = sum(1 for term in option_terms if re.search(rf"\b{re.escape(term)}\b", text))
                phrase_hit = 4 if option.lower() in text else 0
                question_hits = len(question_terms & set(re.findall(r"[a-z0-9]+", text)))
                scores[letter] += option_hits * 3 + phrase_hit + min(question_hits, 5)

        best_letter = max(scores, key=scores.get)
        if scores[best_letter] <= 0:
            return None
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[0] == sorted_scores[1]:
            return None
        return best_letter, options[best_letter]

    @staticmethod
    def explanation_for_detected_answer(
        query: str,
        options: dict[str, str],
        letter: str,
        value: str,
    ) -> str:
        q = query.lower()
        value_lower = value.lower()
        if "dijkstra" in q and ("priority queue" in value_lower or "min heap" in value_lower):
            return (
                "Dijkstra's algorithm repeatedly selects the unvisited node with the smallest current distance. "
                "A priority queue implemented with a min heap helps retrieve that node efficiently."
            )
        if "bfs" in q and value_lower == "queue":
            return (
                "BFS uses a queue because it processes nodes in first-in, first-out order and explores the graph level by level."
            )
        if "object storage" in q and value_lower == "s3":
            return (
                "Amazon S3 is AWS's object storage service for files, backups, images, videos, and other unstructured data."
            )
        return "The selected option has the strongest support in the retrieved quiz/explanation context."

    @staticmethod
    def why_others_are_wrong(query: str, options: dict[str, str], correct_letter: str) -> str:
        q = query.lower()
        if "dijkstra" in q:
            wrong = {
                "queue": "used in BFS",
                "stack": "used in DFS",
                "linked list": "inefficient for repeatedly finding the minimum distance node",
                "tree": "a data structure, not the usual priority worklist for Dijkstra's algorithm",
            }
            return QuizAgent.format_wrong_options(options, correct_letter, wrong)
        if "bfs" in q:
            wrong = {
                "stack": "used by DFS-style traversal, not standard BFS",
                "heap": "used for priority-based algorithms such as Dijkstra's algorithm",
                "tree": "a hierarchical data structure, not the worklist used by BFS",
            }
            return QuizAgent.format_wrong_options(options, correct_letter, wrong)
        return "The other options were less supported by the retrieved evidence."

    @staticmethod
    def format_wrong_options(options: dict[str, str], correct_letter: str, reasons: dict[str, str]) -> str:
        lines = []
        for letter, value in sorted(options.items()):
            if letter == correct_letter:
                continue
            reason = reasons.get(value.lower(), "not the best answer for this question")
            lines.append(f"{letter}) {value} -> {reason}")
        return "\n".join(lines)

    @staticmethod
    def question_without_options(query: str) -> str:
        lines = [
            line.strip()
            for line in query.splitlines()
            if not re.match(r"(?i)^\s*[a-d]\)\s+", line)
        ]
        return " ".join(line for line in lines if line).strip()

    @staticmethod
    def parse_options(query: str) -> dict[str, str]:
        options: dict[str, str] = {}
        pattern = re.compile(r"(?im)^\s*([A-D])\)\s*(.+?)\s*$")
        for match in pattern.finditer(query):
            options[match.group(1).upper()] = match.group(2).strip()
        return options

    @staticmethod
    def find_option_letter(options: dict[str, str], expected: str) -> str:
        expected = expected.lower()
        for letter, value in options.items():
            if value.strip().lower() == expected:
                return letter
        return ""

    @staticmethod
    def find_option_containing(options: dict[str, str], expected_terms: list[str]) -> str:
        for letter, value in options.items():
            lower = value.strip().lower()
            if any(term in lower for term in expected_terms):
                return letter
        return ""
