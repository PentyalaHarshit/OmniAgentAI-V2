from tools.rag_tool import RAGTool


def test_healthcare_rag():
    rag = RAGTool()
    result = rag.search("chest pain diabetes", "healthcare")
    assert "context" in result
