from agents.coding_agent import CodingAgent
from crews.coding_crew import CodingCrew


def test_dijkstra_coding_agent_returns_reasoned_algorithm_pipeline():
    agent = CodingAgent()

    result = agent.run("Create optimized Dijkstra algorithm")
    answer = result["answer"]
    crew = result["extra"]["crew_result"]

    assert crew["selected_algorithm"] == "dijkstra"
    assert crew["selected_algorithm_label"] == "Heap Optimized Dijkstra"
    assert crew["reasoning_score"] >= 90
    assert crew["verification"]["passed"] is True
    assert crew["verification"]["confidence"] == 98
    assert "Selected Algorithm:" in answer
    assert "Dijkstra" in answer
    assert "O((V + E) log V)" in answer
    assert "ReAct Trace:" in answer
    assert "Retrieve algorithms.txt" in answer
    assert "CrewAI Review:" in answer
    assert "Multi-LLM Improvements:" in answer
    assert "Use long long" in answer
    assert "Compilation Passed" in answer
    assert "Unit Tests Passed" in answer
    assert "Confidence:" in answer
    assert "98%" in answer


def test_negative_edge_shortest_path_replans_to_bellman_ford():
    agent = CodingAgent()

    result = agent.run("Find shortest path in a weighted graph with a negative edge.")
    answer = result["answer"]
    crew = result["extra"]["crew_result"]

    assert crew["selected_algorithm"] == "bellman_ford"
    assert crew["selected_algorithm_label"] == "Bellman-Ford"
    assert crew["verification"]["passed"] is True
    assert crew["self_correct"][0]["action"] == "retry_with_alternative_algorithm"
    assert crew["crew_validation_trace"][0]["analyzer"]["failure_type"] == "strategy_mismatch"
    assert crew["crew_validation_trace"][0]["validator"]["decision"] == "reopen_tot"
    assert "CrewAI Failed Observation Validation:" in answer
    assert "Validator=reopen_tot" in answer
    assert "Bellman-Ford" in answer
    assert "O(VE)" in answer


def test_segment_tree_query_returns_coding_pipeline():
    agent = CodingAgent()

    result = agent.run("Create Segment Tree with range sum queries")
    answer = result["answer"]
    crew = result["extra"]["crew_result"]

    assert crew["selected_algorithm"] == "segment_tree"
    assert crew["selected_algorithm_label"] == "Segment Tree"
    assert crew["reasoning_score"] >= 90
    assert crew["verification"]["passed"] is True
    assert "Selected Algorithm:" in answer
    assert "Segment Tree" in answer
    assert "Fenwick Tree" in answer
    assert "O(log N)" in answer
    assert "Generated C++ solution template" not in answer


def test_heavy_light_decomposition_returns_full_cpp_solution():
    agent = CodingAgent()

    result = agent.run(
        "Create Heavy Light Decomposition in C++. "
        "Use segment tree for path maximum query. "
        "Support update node value and query path u-v. "
        "Generate full code with input/output."
    )
    answer = result["answer"]
    crew = result["extra"]["crew_result"]

    assert crew["selected_algorithm"] == "heavy_light_decomposition"
    assert crew["selected_algorithm_label"] == "Heavy Light Decomposition"
    assert crew["status"] == "success"
    assert crew["verification"]["passed"] is True
    assert "Generated C++ solution template" not in answer
    assert "Selected Algorithm:\nHeavy Light Decomposition" in answer
    assert "SegmentTree" in answer
    assert "query_path" in answer
    assert "O(log^2 N)" in answer
    assert "Case 1 passed" in crew["test_result"]["output"]


def test_lca_binary_lifting_returns_full_cpp_solution():
    agent = CodingAgent()

    result = agent.run(
        "Create Lowest Common Ancestor using Binary Lifting in C++. "
        "Use DFS preprocessing, up table, depth array. "
        "Support multiple LCA queries. "
        "Generate complete working code with input/output."
    )
    answer = result["answer"]
    crew = result["extra"]["crew_result"]

    assert crew["selected_algorithm"] == "lowest_common_ancestor_binary_lifting"
    assert crew["selected_algorithm_label"] == "Binary Lifting LCA"
    assert crew["status"] == "success"
    assert crew["verification"]["passed"] is True
    assert crew["verification"]["confidence"] >= 90
    assert "Generated C++ solution template" not in answer
    assert "vector<vector<int>> up" in answer
    assert "vector<int> depth" in answer
    assert "void dfs" in answer
    assert "O(N log N)" in answer
    assert "Case 1 passed" in crew["test_result"]["output"]


def test_template_output_is_marked_failed_and_retry_required():
    crew = CodingCrew()
    selected = {
        "algorithm": "segment_tree",
        "score": 50,
        "time_complexity": "O(log N)",
        "memory_complexity": "O(N)",
    }
    compile_result = {"status": "passed", "output": "Compilation Passed"}
    test_result = {"status": "passed", "output": "Case 1 passed"}

    verification = crew.verify_solution(
        selected,
        compile_result,
        test_result,
        'cout << "Generated C++ solution template\\n";',
    )

    assert verification["passed"] is False
    assert verification["compilation_passed"] is True
    assert verification["problem_solved"] is False
    assert "Template output detected" in verification["reason"]
    assert verification["retry_required"] is True


def test_retry_candidate_prefers_family_alternative():
    selected = {"algorithm": "segment_tree"}
    candidates = [
        {"algorithm": "segment_tree", "score": 95},
        {"algorithm": "fenwick_tree", "score": 88},
    ]

    assert CodingCrew.pick_retry_candidate(candidates, selected)["algorithm"] == "fenwick_tree"


def test_fastapi_crud_mysql_request_returns_project_code_not_deployment():
    agent = CodingAgent()

    result = agent.run(
        "Build a FastAPI CRUD application with MySQL. "
        "Generate full project code with SQLAlchemy models, schemas, routes, "
        "database connection, requirements.txt, and run command. "
        "Do not generate Docker files unless I ask for deployment."
    )
    answer = result["answer"]
    crew = result["extra"]["crew_result"]

    assert result["agent"] == "CodingAgent"
    assert crew["selected_algorithm"] == "fastapi_crud_application"
    assert crew["database"] == "mysql"
    assert "FastAPI CRUD application with MySQL" in answer
    assert "requirements.txt" in answer
    assert "mysql+pymysql" in answer
    assert "class Item" in answer
    assert "class ItemCreate" in answer
    assert "@app.post(\"/items\"" in answer
    assert "@app.delete(\"/items/{item_id}\"" in answer
    assert "uvicorn app.main:app --reload" in answer
    assert "Dockerfile" not in answer
    assert "docker-compose" not in answer
    assert "#include <bits/stdc++.h>" not in answer


def test_multithreaded_web_crawler_uses_software_engineering_mode():
    agent = CodingAgent()

    result = agent.run("Build a multithreaded web crawler in Python using requests and BeautifulSoup.")
    answer = result["answer"]
    crew = result["extra"]["crew_result"]

    assert result["agent"] == "CodingAgent"
    assert crew["mode"] == "software_engineering"
    assert crew["generator_key"] == "web_crawler_python"
    assert crew["selected_pattern"] == "Multithreaded Web Crawler"
    assert crew["language"] == "python"
    assert crew["status"] == "success"
    assert "Selected Pattern: Multithreaded Web Crawler" in answer
    assert "Language: Python" in answer
    assert "Status: success" in answer
    assert "ThreadPoolExecutor" in answer
    assert "queue.Queue" in answer
    assert "requests.Session" in answer
    assert "BeautifulSoup" in answer
    assert "centroid_decomposition" not in answer
    assert "heavy_light_decomposition" not in answer
    assert "lowest_common_ancestor" not in answer
    assert "segment_tree" not in answer
