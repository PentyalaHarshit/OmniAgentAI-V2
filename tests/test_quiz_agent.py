from agents.agent_router import AgentRouter
from agents.quiz_agent import QuizAgent


AWS_OBJECT_STORAGE_QUESTION = """Which AWS service is primarily used for object storage?

A) EC2
B) S3
C) Lambda
D) RDS
"""

BFS_DATA_STRUCTURE_QUESTION = """Which data structure is used in BFS?

A) Stack
B) Queue
C) Heap
D) Tree
"""

DIJKSTRA_DATA_STRUCTURE_QUESTION = """Which data structure is used internally in Dijkstra's Algorithm?

A) Queue
B) Stack
C) Priority Queue (Min Heap)
D) Linked List
"""


def test_router_sends_mcq_to_quiz_agent_not_rag_agent():
    route, agent = AgentRouter().route(AWS_OBJECT_STORAGE_QUESTION)

    assert route == "quiz"
    assert agent.name == "QuizAgent"
    assert agent.name != "RAGAgent"


def test_quiz_agent_answers_aws_object_storage_question():
    result = QuizAgent().run(AWS_OBJECT_STORAGE_QUESTION)

    assert result["agent"] == "QuizAgent"
    assert "Correct Answer: B) S3" in result["answer"]
    assert "Amazon S3 (Simple Storage Service)" in result["answer"]
    assert "A) EC2 -> Virtual servers" in result["answer"]
    assert "C) Lambda -> Serverless functions" in result["answer"]
    assert "D) RDS -> Relational databases" in result["answer"]
    assert result["extra"]["source_stage"] == "quiz_local_knowledge"
    assert result["extra"]["local_match"]["confidence"] > 0.9


def test_quiz_agent_answers_bfs_data_structure_question():
    result = QuizAgent().run(BFS_DATA_STRUCTURE_QUESTION)

    assert result["agent"] == "QuizAgent"
    assert "Correct Answer: B) Queue" in result["answer"]
    assert "BFS (Breadth-First Search) uses a queue" in result["answer"]
    assert "A) Stack -> Used by DFS-style traversal" in result["answer"]
    assert "C) Heap -> Used for priority-based algorithms" in result["answer"]
    assert "D) Tree -> A hierarchical data structure" in result["answer"]
    assert "local_knowledge_check" in result["extra"]["pipeline"]
    assert result["extra"]["source_stage"] == "quiz_local_knowledge"


def test_quiz_agent_uses_web_evidence_before_local_knowledge(monkeypatch):
    agent = QuizAgent(quiz_db_path="missing.json")

    monkeypatch.setattr(agent, "retrieve_evidence", lambda query: [{
        "title": "Dijkstra algorithm priority queue explanation",
        "snippet": "Dijkstra's algorithm uses a priority queue or min heap to repeatedly select the vertex with minimum distance.",
        "url": "https://example.com/dijkstra",
        "source": "SerpAPI",
    }])

    result = agent.run(DIJKSTRA_DATA_STRUCTURE_QUESTION)

    assert "Correct Answer: C) Priority Queue (Min Heap)" in result["answer"]
    assert "smallest current distance" in result["answer"]
    assert result["extra"]["evidence"][0]["source"] == "SerpAPI"


def test_quiz_agent_falls_back_to_local_knowledge_when_web_fails(monkeypatch):
    agent = QuizAgent()
    monkeypatch.setattr(agent, "retrieve_evidence", lambda query: [])

    result = agent.run(DIJKSTRA_DATA_STRUCTURE_QUESTION)

    assert "Correct Answer: C) Priority Queue (Min Heap)" in result["answer"]
    assert "A) Queue -> Used in BFS" in result["answer"]
    assert "B) Stack -> Used in DFS" in result["answer"]
    assert "D) Linked List -> Inefficient" in result["answer"]
    assert result["extra"]["source_stage"] == "quiz_local_knowledge"


def test_quiz_agent_does_not_guess_without_evidence_or_local_knowledge(monkeypatch):
    agent = QuizAgent()
    monkeypatch.setattr(agent, "retrieve_evidence", lambda query: [])
    query = """Which widget mode is correct?

A) Alpha
B) Beta
C) Gamma
D) Delta
"""

    result = agent.run(query)

    assert "Correct Answer:" not in result["answer"]
    assert "could not confidently determine" in result["answer"]


def test_quiz_agent_loads_json_quiz_database():
    agent = QuizAgent()

    assert len(agent.quiz_knowledge) >= 8
    assert any(item["answer_text"] == "Mars" for item in agent.quiz_knowledge)
