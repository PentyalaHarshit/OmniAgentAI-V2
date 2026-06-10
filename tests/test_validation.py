from agents.general_agent import GeneralAgent, validate_query, FactVerificationAgent


def test_query_validation_invalid():
    valid, message = validate_query("what is capital of paris")
    assert not valid
    assert "Paris is a city and therefore does not have a capital." in message
    assert "What is the capital of France?" in message


def test_query_validation_valid():
    valid, message = validate_query("what is the capital of France?")
    assert valid
    assert message == ""


def test_fact_verification_invalid():
    verifier = FactVerificationAgent()
    result = verifier.verify("what is capital of paris", "Paris is a city.")
    assert not result["verified"]
    assert result["reason"] == "Paris is a city not a country."


def test_fact_verification_valid():
    verifier = FactVerificationAgent()
    result = verifier.verify("what is the capital of France?", "Paris.")
    assert result["verified"]


def test_general_agent_validation_flow():
    agent = GeneralAgent()
    result = agent.run("what is capital of paris")
    assert result["agent"] == "GeneralAgent"
    assert "Paris is a city and therefore does not have a capital." in result["answer"]
    assert "What is the capital of France?" in result["answer"]
    assert result["extra"].get("source") == "query_validation"


def test_entity_extractor():
    from agents.general_agent import EntityExtractor
    extractor = EntityExtractor()
    
    e1 = extractor.extract("What is the GDP of Paris?")
    assert e1.get("entity") == "Paris"
    assert e1.get("attribute") == "GDP"
    assert e1.get("type") == "city"

    e2 = extractor.extract("What is the population?")
    assert "entity" not in e2
    assert e2.get("attribute") == "population"


def test_general_agent_memory_resolution():
    from tools.chat_memory import ChatMemory
    memory = ChatMemory()
    session_id = "test_session_123"
    memory.clear(session_id)
    
    agent = GeneralAgent()

    # User: What is the capital of France?
    # Assistant: The capital of France is Paris.
    memory.add(session_id, "user", "What is the capital of France?")
    memory.add(session_id, "assistant", "The capital of France is Paris.")

    # User: What is the population?
    result1 = agent.run("What is the population?", session_id=session_id)
    assert "Population of Paris is approximately 2.1 million" in result1["answer"]

    # Add to memory
    memory.add(session_id, "user", "What is the population?")
    memory.add(session_id, "assistant", result1["answer"])

    # User: What is the GDP?
    result2 = agent.run("What is the GDP?", session_id=session_id)
    assert "GDP of Paris" in result2["answer"]


def test_answer_compression():
    from agents.general_agent import AnswerExtractionAgent
    extractor = AnswerExtractionAgent()

    # Test Capital
    c1 = extractor.extract("What is the capital of France?", "France, officially the French Republic, is a country. The capital and largest city is Paris.")
    assert "Paris" in c1

    # Test Population
    c2 = extractor.extract("What is the population of France?", "France has a population of about 68 million. Its economy is large.")
    assert "Approximately 69 million people." in c2

    # Test GDP
    c3 = extractor.extract("What is the GDP of France?", "France has a strong economy. Its GDP is around 3 trillion USD.")
    assert "Approximately $3 trillion USD." in c3
