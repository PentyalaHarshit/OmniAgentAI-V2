import re
from typing import Dict, List, Any


class AlgorithmCrew:
    def __init__(self):
        self.algorithm_database = self.build_algorithm_database()

    def run(self, query: str):
        # Detect problem patterns
        problem_type = self.detect_problem_type(query)
        constraints = self.extract_constraints(query)
        
        # Rank algorithms
        ranked_algorithms = self.rank_algorithms(problem_type, constraints, query)
        
        # Select best algorithm
        best_algorithm = ranked_algorithms[0] if ranked_algorithms else {"name": "Brute Force", "score": 50}
        
        crew_steps = [
            {"thought": "Pattern Detector: analyzing problem structure", "output": f"Detected {problem_type}"},
            {"thought": "Constraint Analyzer: extracting input constraints", "output": f"Constraints: {constraints}"},
            {"thought": "Algorithm Ranker: scoring candidate algorithms", "output": f"Ranked {len(ranked_algorithms)} algorithms"},
            {"thought": "Best Match Selector: choosing optimal algorithm", "output": f"Selected: {best_algorithm['name']}"},
        ]
        
        return {
            "problem_type": problem_type,
            "constraints": constraints,
            "ranked_algorithms": ranked_algorithms,
            "best_algorithm": best_algorithm,
            "crew_steps": crew_steps,
        }

    @staticmethod
    def detect_problem_type(query: str) -> str:
        """Detect the type of problem from query."""
        query_lower = query.lower()
        
        problem_patterns = {
            "range_query": ["range query", "range sum", "range update", "segment", "fenwick", "sparse table"],
            "shortest_path": ["shortest path", "dijkstra", "bellman", "floyd", "graph path", "minimum distance"],
            "tree": ["tree", "lca", "lowest common ancestor", "binary tree", "tree traversal", "hld", "centroid"],
            "graph": ["graph", "bfs", "dfs", "topological", "connected component", "bipartite"],
            "string": ["string", "substring", "pattern", "kmp", "trie", "suffix", "palindrome"],
            "dp": ["dynamic programming", "dp", "memoization", "tabulation", "subsequence", "knapsack"],
            "greedy": ["greedy", "minimum", "maximum", "optimal", "schedule", "interval"],
            "binary_search": ["binary search", "search", "sorted", "monotonic", "lower bound", "upper bound"],
            "sorting": ["sort", "sorting", "order", "arrange", "merge", "quick", "heap"],
            "number_theory": ["prime", "gcd", "lcm", "modular", "factor", "divisor"],
            "geometry": ["geometry", "point", "line", "circle", "polygon", "convex hull"],
            "flow": ["flow", "max flow", "min cut", "bipartite matching", "network"],
        }
        
        for problem_type, patterns in problem_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return problem_type
        
        return "general"

    @staticmethod
    def extract_constraints(query: str) -> Dict[str, Any]:
        """Extract constraints from query."""
        constraints = {
            "n": None,
            "m": None,
            "time_limit": None,
            "memory_limit": None,
            "special": []
        }
        
        query_lower = query.lower()
        
        # Extract N constraint
        n_match = re.search(r'n\s*[<=]\s*(\d+)', query_lower)
        if n_match:
            constraints["n"] = int(n_match.group(1))
        
        # Extract M constraint
        m_match = re.search(r'm\s*[<=]\s*(\d+)', query_lower)
        if m_match:
            constraints["m"] = int(m_match.group(1))
        
        # Extract time limit
        time_match = re.search(r'time\s*limit\s*:?\s*(\d+)', query_lower)
        if time_match:
            constraints["time_limit"] = int(time_match.group(1))
        
        # Extract memory limit
        memory_match = re.search(r'memory\s*limit\s*:?\s*(\d+)', query_lower)
        if memory_match:
            constraints["memory_limit"] = int(memory_match.group(1))
        
        # Detect special constraints
        if "online" in query_lower:
            constraints["special"].append("online_queries")
        if "update" in query_lower:
            constraints["special"].append("dynamic")
        if "offline" in query_lower:
            constraints["special"].append("offline")
        if "modulo" in query_lower:
            constraints["special"].append("modulo_arithmetic")
        
        return constraints

    def build_algorithm_database(self) -> Dict[str, List[Dict]]:
        """Build database of algorithms with their characteristics."""
        return {
            "range_query": [
                {
                    "name": "Segment Tree",
                    "time_complexity": "O(log n) per query",
                    "space_complexity": "O(n)",
                    "best_for": ["point updates", "range queries", "dynamic"],
                    "score": 95
                },
                {
                    "name": "Fenwick Tree (BIT)",
                    "time_complexity": "O(log n) per query",
                    "space_complexity": "O(n)",
                    "best_for": ["prefix sums", "point updates", "simple operations"],
                    "score": 90
                },
                {
                    "name": "Sparse Table",
                    "time_complexity": "O(1) query, O(n log n) build",
                    "space_complexity": "O(n log n)",
                    "best_for": ["static arrays", "range min/max queries"],
                    "score": 85
                },
                {
                    "name": "Square Root Decomposition",
                    "time_complexity": "O(√n) per query",
                    "space_complexity": "O(n)",
                    "best_for": ["general range queries", "when log is too slow"],
                    "score": 75
                },
            ],
            "shortest_path": [
                {
                    "name": "Dijkstra (Heap Optimized)",
                    "time_complexity": "O((V + E) log V)",
                    "space_complexity": "O(V + E)",
                    "best_for": ["non-negative weights", "single source"],
                    "score": 95
                },
                {
                    "name": "Bellman-Ford",
                    "time_complexity": "O(VE)",
                    "space_complexity": "O(V)",
                    "best_for": ["negative weights", "detect negative cycles"],
                    "score": 70
                },
                {
                    "name": "Floyd-Warshall",
                    "time_complexity": "O(V³)",
                    "space_complexity": "O(V²)",
                    "best_for": ["all pairs shortest path", "dense graphs"],
                    "score": 75
                },
                {
                    "name": "0-1 BFS",
                    "time_complexity": "O(V + E)",
                    "space_complexity": "O(V + E)",
                    "best_for": ["weights 0 or 1", "unweighted graphs"],
                    "score": 85
                },
            ],
            "tree": [
                {
                    "name": "Binary Lifting (LCA)",
                    "time_complexity": "O(n log n) preprocessing, O(log n) query",
                    "space_complexity": "O(n log n)",
                    "best_for": ["LCA queries", "k-th ancestor"],
                    "score": 95
                },
                {
                    "name": "Heavy Light Decomposition",
                    "time_complexity": "O(log² n) per query",
                    "space_complexity": "O(n)",
                    "best_for": ["path queries", "path updates", "tree DP"],
                    "score": 90
                },
                {
                    "name": "Centroid Decomposition",
                    "time_complexity": "O(n log n)",
                    "space_complexity": "O(n)",
                    "best_for": ["tree queries", "distance problems"],
                    "score": 85
                },
                {
                    "name": "Euler Tour + Segment Tree",
                    "time_complexity": "O(log n) per query",
                    "space_complexity": "O(n)",
                    "best_for": ["subtree queries", "path to root"],
                    "score": 88
                },
            ],
            "graph": [
                {
                    "name": "BFS",
                    "time_complexity": "O(V + E)",
                    "space_complexity": "O(V)",
                    "best_for": ["unweighted shortest path", "connected components"],
                    "score": 90
                },
                {
                    "name": "DFS",
                    "time_complexity": "O(V + E)",
                    "space_complexity": "O(V)",
                    "best_for": ["traversal", "cycle detection", "topological sort"],
                    "score": 90
                },
                {
                    "name": "Union-Find (DSU)",
                    "time_complexity": "O(α(n)) per operation",
                    "space_complexity": "O(V)",
                    "best_for": ["connected components", "dynamic connectivity"],
                    "score": 92
                },
                {
                    "name": "Topological Sort",
                    "time_complexity": "O(V + E)",
                    "space_complexity": "O(V)",
                    "best_for": ["DAG problems", "dependency ordering"],
                    "score": 85
                },
            ],
            "string": [
                {
                    "name": "KMP",
                    "time_complexity": "O(n + m)",
                    "space_complexity": "O(m)",
                    "best_for": ["pattern matching", "single pattern"],
                    "score": 90
                },
                {
                    "name": "Trie",
                    "time_complexity": "O(m) per query",
                    "space_complexity": "O(alphabet_size * n)",
                    "best_for": ["prefix queries", "dictionary", "autocomplete"],
                    "score": 88
                },
                {
                    "name": "Suffix Array",
                    "time_complexity": "O(n log n)",
                    "space_complexity": "O(n)",
                    "best_for": ["substring queries", "pattern matching"],
                    "score": 85
                },
                {
                    "name": "Manacher's Algorithm",
                    "time_complexity": "O(n)",
                    "space_complexity": "O(n)",
                    "best_for": ["palindromes", "longest palindromic substring"],
                    "score": 92
                },
            ],
            "dp": [
                {
                    "name": "1D DP",
                    "time_complexity": "O(n)",
                    "space_complexity": "O(n)",
                    "best_for": ["linear problems", "simple states"],
                    "score": 85
                },
                {
                    "name": "2D DP",
                    "time_complexity": "O(n²)",
                    "space_complexity": "O(n²)",
                    "best_for": ["grid problems", "two-dimensional states"],
                    "score": 80
                },
                {
                    "name": "DP with Bitmask",
                    "time_complexity": "O(n * 2ⁿ)",
                    "space_complexity": "O(n * 2ⁿ)",
                    "best_for": ["small n", "subset problems"],
                    "score": 75
                },
                {
                    "name": "DP with Divide and Conquer",
                    "time_complexity": "O(n log n)",
                    "space_complexity": "O(n)",
                    "best_for": ["convex DP", "optimal partitioning"],
                    "score": 82
                },
            ],
            "general": [
                {
                    "name": "Brute Force",
                    "time_complexity": "O(n!) or O(2ⁿ)",
                    "space_complexity": "O(n)",
                    "best_for": ["small constraints", "verification"],
                    "score": 40
                },
                {
                    "name": "Two Pointers",
                    "time_complexity": "O(n)",
                    "space_complexity": "O(1)",
                    "best_for": ["sorted arrays", "subarray problems"],
                    "score": 85
                },
                {
                    "name": "Sliding Window",
                    "time_complexity": "O(n)",
                    "space_complexity": "O(k)",
                    "best_for": ["fixed window", "subarray constraints"],
                    "score": 88
                },
            ],
        }

    def rank_algorithms(self, problem_type: str, constraints: Dict, query: str) -> List[Dict]:
        """Rank algorithms based on problem type and constraints."""
        algorithms = self.algorithm_database.get(problem_type, self.algorithm_database["general"])
        
        # Score adjustment based on constraints
        n = constraints.get("n", 10**5)
        has_updates = "dynamic" in constraints.get("special", [])
        
        ranked = []
        for algo in algorithms:
            score = algo["score"]
            
            # Adjust score based on constraints
            if n > 10**5 and "O(n log n)" not in algo["time_complexity"]:
                score -= 20
            if n > 10**6 and "O(n)" not in algo["time_complexity"]:
                score -= 30
            if has_updates and "static" in str(algo["best_for"]):
                score -= 25
            
            ranked.append({
                "name": algo["name"],
                "time_complexity": algo["time_complexity"],
                "space_complexity": algo["space_complexity"],
                "best_for": algo["best_for"],
                "score": max(0, min(100, score))
            })
        
        # Sort by score
        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked
