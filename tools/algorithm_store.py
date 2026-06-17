import re


class AlgorithmStore:
    def __init__(self):
        self.algorithms = {
            "dijkstra": {
                "name": "Dijkstra",
                "keywords": ["dijkstra", "shortest path", "weighted graph", "priority queue", "heap"],
                "tags": ["graph", "shortest-path", "heap"],
                "category": "graph",
                "difficulty": "intermediate",
                "time_complexity": "O((V + E) log V)",
                "memory_complexity": "O(V + E)",
            },
            "zero_one_bfs": {
                "name": "0-1 BFS",
                "keywords": ["0-1 bfs", "zero one bfs", "weight 0 1", "deque shortest path"],
                "tags": ["graph", "shortest-path", "deque"],
                "category": "graph",
                "difficulty": "intermediate",
                "time_complexity": "O(V + E)",
                "memory_complexity": "O(V + E)",
            },
            "bfs": {
                "name": "BFS",
                "keywords": ["bfs", "unweighted graph", "minimum edges", "queue"],
                "tags": ["graph", "traversal"],
                "category": "graph",
                "difficulty": "beginner",
                "time_complexity": "O(V + E)",
                "memory_complexity": "O(V)",
            },
            "dfs": {
                "name": "DFS",
                "keywords": ["dfs", "tree traversal", "connected components"],
                "tags": ["graph", "tree", "traversal"],
                "category": "graph",
                "difficulty": "beginner",
                "time_complexity": "O(V + E)",
                "memory_complexity": "O(V)",
            },
            "dynamic_programming": {
                "name": "Dynamic Programming",
                "keywords": ["dp", "dynamic programming", "subsequence", "knapsack", "ways"],
                "tags": ["dp"],
                "category": "dynamic-programming",
                "difficulty": "intermediate",
                "time_complexity": "Depends on state and transition",
                "memory_complexity": "Depends on state",
            },
            "divide_conquer_dp": {
                "name": "Divide and Conquer DP",
                "keywords": ["divide and conquer dp", "dp optimization", "monotonic opt"],
                "tags": ["dp", "optimization"],
                "category": "dynamic-programming",
                "difficulty": "advanced",
                "time_complexity": "Often O(KN log N) or O(KN)",
                "memory_complexity": "Depends on DP state",
            },
            "convex_hull_trick": {
                "name": "Convex Hull Trick",
                "keywords": ["convex hull trick", "cht", "li chao", "dp optimization"],
                "tags": ["dp", "optimization", "data-structures"],
                "category": "dynamic-programming",
                "difficulty": "advanced",
                "time_complexity": "O(log C) per insertion/query with Li Chao Tree",
                "memory_complexity": "O(N)",
            },
            "greedy": {
                "name": "Greedy",
                "keywords": ["greedy", "minimum cost", "maximum profit", "sort"],
                "tags": ["greedy", "sorting"],
                "category": "greedy",
                "difficulty": "beginner",
                "time_complexity": "Usually O(N log N)",
                "memory_complexity": "Usually O(1) or O(N)",
            },
            "binary_search": {
                "name": "Binary Search",
                "keywords": ["binary search", "monotonic", "minimum possible", "maximum possible"],
                "tags": ["binary-search"],
                "category": "search",
                "difficulty": "beginner",
                "time_complexity": "O(log N)",
                "memory_complexity": "O(1)",
            },
            "segment_tree": {
                "name": "Segment Tree",
                "keywords": ["segment tree", "range sum", "range query", "range update", "point update"],
                "tags": ["data-structures", "range-query"],
                "category": "data-structure",
                "difficulty": "intermediate",
                "time_complexity": "O(log N) per query/update",
                "memory_complexity": "O(N)",
            },
            "fenwick_tree": {
                "name": "Fenwick Tree",
                "keywords": ["fenwick", "binary indexed tree", "bit tree", "prefix sum"],
                "tags": ["data-structures", "range-query"],
                "category": "data-structure",
                "difficulty": "intermediate",
                "time_complexity": "O(log N) per query/update",
                "memory_complexity": "O(N)",
            },
            "heavy_light_decomposition": {
                "name": "Heavy Light Decomposition",
                "keywords": ["heavy light decomposition", "heavy-light decomposition", "hld", "path query", "path maximum"],
                "tags": ["trees", "data-structures", "segment-tree"],
                "category": "tree",
                "difficulty": "advanced",
                "time_complexity": "O(log^2 N) per path query/update",
                "memory_complexity": "O(N)",
            },
            "lowest_common_ancestor_binary_lifting": {
                "name": "Lowest Common Ancestor - Binary Lifting",
                "keywords": ["lca", "lowest common ancestor", "binary lifting", "tree ancestor", "kth parent"],
                "tags": ["trees", "binary-lifting"],
                "category": "tree",
                "difficulty": "intermediate",
                "time_complexity": "O(N log N) preprocessing, O(log N) per query",
                "memory_complexity": "O(N log N)",
            },
            "centroid_decomposition": {
                "name": "Centroid Decomposition",
                "keywords": ["centroid decomposition", "tree distance queries", "decompose tree"],
                "tags": ["trees", "decomposition"],
                "category": "tree",
                "difficulty": "advanced",
                "time_complexity": "O(N log N) preprocessing, O(log N) or O(log^2 N) query",
                "memory_complexity": "O(N log N)",
            },
            "dsu_on_tree": {
                "name": "DSU on Tree",
                "keywords": ["dsu on tree", "small to large", "subtree color queries", "sack"],
                "tags": ["trees", "small-to-large"],
                "category": "tree",
                "difficulty": "advanced",
                "time_complexity": "O(N log N) or O(N) depending on implementation",
                "memory_complexity": "O(N)",
            },
        }

    def search(self, query: str):
        return [item["algorithm"] for item in self.search_details(query)] or ["basic_solution"]

    def search_details(self, query: str):
        q = self._normalize(query)
        scored = []
        for algorithm, meta in self.algorithms.items():
            score = self._score_keywords(q, meta["keywords"])
            if score:
                scored.append((score, self._algorithm_result(algorithm, meta, score)))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [item for _, item in scored]

    def get(self, algorithm: str):
        meta = self.algorithms.get(algorithm)
        if not meta:
            return None
        return self._algorithm_result(algorithm, meta, 100)

    def _score_keywords(self, q: str, keywords: list[str]):
        score = 0
        for keyword in keywords:
            normalized = self._normalize(keyword)
            if normalized and normalized in q:
                score += 10 + len(normalized.split())
        return score

    @staticmethod
    def _algorithm_result(algorithm: str, meta: dict, score: int):
        return {
            "type": "algorithm",
            "algorithm": algorithm,
            "name": meta["name"],
            "aliases": meta["keywords"],
            "tags": meta["tags"],
            "difficulty": meta["difficulty"],
            "category": meta["category"],
            "time_complexity": meta["time_complexity"],
            "memory_complexity": meta["memory_complexity"],
            "score": score,
        }

    @staticmethod
    def _normalize(text: str):
        return re.sub(r"\s+", " ", (text or "").lower().replace("-", " ")).strip()
