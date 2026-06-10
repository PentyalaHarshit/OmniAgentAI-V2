class AlgorithmStore:
    def __init__(self):
        self.algorithms = {
            "dijkstra": ["dijkstra", "shortest path", "weighted graph", "priority queue"],
            "bfs": ["bfs", "unweighted graph", "minimum edges", "queue"],
            "dfs": ["dfs", "tree traversal", "connected components"],
            "dynamic_programming": ["dp", "dynamic programming", "subsequence", "knapsack", "ways"],
            "greedy": ["greedy", "minimum cost", "maximum profit", "sort"],
            "binary_search": ["binary search", "monotonic", "minimum possible", "maximum possible"],
        }

    def search(self, query: str):
        q = query.lower()
        scored = []
        for name, keys in self.algorithms.items():
            score = sum(1 for k in keys if k in q)
            if score:
                scored.append((score, name))
        scored.sort(reverse=True)
        return [name for _, name in scored] or ["basic_solution"]
