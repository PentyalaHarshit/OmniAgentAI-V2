from llm_tree.free_llm_tree import FreeLLMTree


def test_vllm_parallel_tree_structure():
    tree = FreeLLMTree()
    result = tree.run("generate c++ code for dijkstra")
    assert result["parallel"] is True
    assert "backend" in result
    assert "best_model" in result
