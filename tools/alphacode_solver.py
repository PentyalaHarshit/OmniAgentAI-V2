import re


class AlphaCodeStyleSolver:
    HARD_KEYWORDS = {
        "hard",
        "advanced",
        "dsu on tree",
        "centroid decomposition",
        "heavy light",
        "hld",
        "segment tree graph",
        "binary lifting",
        "tree queries",
        "mo on tree",
        "dijkstra",
    }

    def build_search_report(
        self,
        query: str,
        algorithm_rag_blocks: list[str],
        candidates: list[dict],
        selected_candidate: dict,
        supported: bool,
    ):
        strategy_candidates = self._strategy_candidates(query, algorithm_rag_blocks, candidates)
        validation_gates = [
            "problem_statement_or_task_resolved",
            "algorithm_selected_from_rag_or_supported_bank",
            "code_generated",
            "compiled_successfully",
            "expected_tests_passed",
            "template_output_absent",
            "statement_tests_available",
        ]

        return {
            "mode": "AlphaCode-style hard problem search",
            "enabled": self.is_hard_query(query, algorithm_rag_blocks),
            "supported_solution": supported,
            "strategy_candidates": strategy_candidates,
            "selected_strategy": strategy_candidates[0] if strategy_candidates else selected_candidate,
            "validation_gates": validation_gates,
            "policy": (
                "Return success only after generation, compilation, expected tests, "
                "template detection, and statement/test validation all pass."
            ),
            "status": "ready_to_validate" if supported else "needs_problem_statement_or_verified_solution",
        }

    def is_hard_query(self, query: str, algorithm_rag_blocks: list[str]):
        text = f"{query}\n" + "\n".join(algorithm_rag_blocks or [])
        lower = text.lower()
        rating = self._extract_rating(lower)
        return bool(
            (rating and rating >= 1800)
            or any(keyword in lower for keyword in self.HARD_KEYWORDS)
        )

    def _strategy_candidates(self, query: str, algorithm_rag_blocks: list[str], candidates: list[dict]):
        strategies = []
        for candidate in candidates:
            strategies.append({
                "name": candidate.get("name", candidate.get("algorithm", "unknown")),
                "algorithm": candidate.get("algorithm", "unknown"),
                "score": candidate.get("score", 0),
                "source": "candidate_generator",
                "reason": candidate.get("reason", ""),
            })

        for block in algorithm_rag_blocks or []:
            parsed = self._parse_algorithm_block(block)
            if not parsed:
                continue
            strategies.append({
                "name": parsed.get("algorithm", "RAG Strategy"),
                "algorithm": parsed.get("generator_key", parsed.get("algorithm", "unknown")),
                "score": self._score_rag_strategy(query, parsed),
                "source": "algorithm_rag",
                "reason": parsed.get("use_when", parsed.get("approach", "")),
                "time_complexity": parsed.get("time_complexity", "Unknown"),
                "memory_complexity": parsed.get("memory_complexity", "Unknown"),
            })

        deduped = {}
        for strategy in strategies:
            key = strategy.get("algorithm") or strategy.get("name")
            if key not in deduped or strategy.get("score", 0) > deduped[key].get("score", 0):
                deduped[key] = strategy

        return sorted(deduped.values(), key=lambda item: item.get("score", 0), reverse=True)[:8]

    @staticmethod
    def _parse_algorithm_block(block: str):
        if not block or "No matching algorithm found." in block:
            return {}
        parsed = {}
        for line in block.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            parsed[key.strip().lower().replace(" ", "_")] = value.strip()
        if "algorithm" not in parsed and "problem" in parsed:
            parsed["algorithm"] = parsed["problem"]
        return parsed

    @staticmethod
    def _score_rag_strategy(query: str, parsed: dict):
        q = query.lower()
        score = 60
        for field in ("algorithm", "problem", "keywords", "category", "generator_key"):
            value = parsed.get(field, "").lower()
            if value and value in q:
                score += 20
        for token in re.findall(r"[a-zA-Z0-9]+", parsed.get("keywords", "").lower()):
            if len(token) > 2 and token in q:
                score += 3
        return min(score, 99)

    @staticmethod
    def _extract_rating(text: str):
        match = re.search(r"\b(1[8-9]\d{2}|2[0-9]\d{2}|3[0-5]\d{2})\b", text)
        return int(match.group(1)) if match else None
