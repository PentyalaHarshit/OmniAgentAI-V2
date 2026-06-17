from tools.algorithm_rag import AlgorithmRAG


def test_algorithm_rag_finds_lca_block():
    rag = AlgorithmRAG()

    results = rag.search("Create LCA with binary lifting", top_k=1)

    assert results[0].startswith("Algorithm: lowest_common_ancestor_binary_lifting")
    assert "binary lifting" in results[0].lower()
    assert "Time Complexity: O(N log N) preprocessing, O(log N) per query" in results[0]


def test_algorithm_rag_finds_advanced_algorithm_block():
    rag = AlgorithmRAG()

    results = rag.search("Use Li Chao Tree for DP optimization", top_k=1)

    assert results[0].startswith("Algorithm: convex_hull_trick")
    assert "li chao tree" in results[0].lower()


def test_algorithm_rag_returns_no_match_message():
    rag = AlgorithmRAG()

    assert rag.search("zzzz yyyyy xxxxx", top_k=1) == ["No matching algorithm found."]
