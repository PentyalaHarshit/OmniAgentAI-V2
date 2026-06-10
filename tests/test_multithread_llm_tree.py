from llm_tree.free_llm_tree import FreeLLMTree


def test_multithread_llm_tree_runs():
    tree = FreeLLMTree()
    result = tree.run("I need trip")
    assert result["parallel"] is True
    assert "total_latency_seconds" in result
    assert "best_model" in result
