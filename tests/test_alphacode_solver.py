from tools.alphacode_solver import AlphaCodeStyleSolver


def test_alphacode_solver_enables_for_hard_rag_query():
    solver = AlphaCodeStyleSolver()
    report = solver.build_search_report(
        query="Create DSU on Tree for subtree color frequency queries",
        algorithm_rag_blocks=[
            """Algorithm: dsu_on_tree
Keywords: dsu on tree, small to large, subtree queries
Category: tree
Use When: Need aggregate statistics for every subtree.
Time Complexity: O(N log N)
Memory Complexity: O(N)"""
        ],
        candidates=[{"name": "DSU on Tree", "algorithm": "dsu_on_tree", "score": 96}],
        selected_candidate={"name": "DSU on Tree", "algorithm": "dsu_on_tree", "score": 96},
        supported=True,
    )

    assert report["enabled"] is True
    assert report["status"] == "ready_to_validate"
    assert report["strategy_candidates"][0]["source"] == "candidate_generator"
    assert "statement/test validation" in report["policy"]


def test_alphacode_solver_ready_for_supported_hard_problem():
    solver = AlphaCodeStyleSolver()
    report = solver.build_search_report(
        query="Create Heavy Light Decomposition with segment tree path maximum",
        algorithm_rag_blocks=["Algorithm: heavy_light_decomposition\nKeywords: hld, path maximum"],
        candidates=[{"name": "Heavy Light Decomposition", "algorithm": "heavy_light_decomposition", "score": 96}],
        selected_candidate={"name": "Heavy Light Decomposition", "algorithm": "heavy_light_decomposition", "score": 96},
        supported=True,
    )

    assert report["enabled"] is True
    assert report["status"] == "ready_to_validate"
    assert report["supported_solution"] is True
