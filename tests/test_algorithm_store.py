from tools.algorithm_store import AlgorithmStore


def test_algorithm_store_matches_algorithm_metadata():
    store = AlgorithmStore()

    results = store.search_details("Create Lowest Common Ancestor using Binary Lifting in C++")

    assert results[0]["algorithm"] == "lowest_common_ancestor_binary_lifting"
    assert results[0]["type"] == "algorithm"
    assert "trees" in results[0]["tags"]
    assert results[0]["difficulty"] == "intermediate"
    assert "O(N log N)" in results[0]["time_complexity"]


def test_algorithm_store_search_remains_backward_compatible():
    store = AlgorithmStore()

    assert store.search("Create Heavy Light Decomposition")[0] == "heavy_light_decomposition"
    assert store.search("Create optimized Dijkstra algorithm")[0] == "dijkstra"
    assert store.search("unknown prompt") == ["basic_solution"]


def test_algorithm_store_matches_advanced_generic_algorithms():
    store = AlgorithmStore()

    cases = {
        "Use centroid decomposition for dynamic tree distance queries": "centroid_decomposition",
        "Use DSU on tree for subtree color queries": "dsu_on_tree",
        "Use Li Chao Tree for DP optimization": "convex_hull_trick",
        "Use zero one bfs for 0 1 weighted graph": "zero_one_bfs",
    }

    for query, algorithm in cases.items():
        assert store.search_details(query)[0]["algorithm"] == algorithm
