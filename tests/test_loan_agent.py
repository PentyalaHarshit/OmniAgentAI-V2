from agents.agent_router import AgentRouter


def test_student_loan_flow_collects_answers_and_returns_analysis():
    router = AgentRouter()
    session_id = "test_student_loan_flow"

    first = router.run("Should I pay off my student loan early?", session_id=session_id)
    assert first["agent"] == "LoanAgent"
    assert "What is your current loan balance?" in first["answer"]

    second = router.run("25000", session_id=session_id)
    assert second["router"]["route"] == "loan"
    assert "What is your interest rate (%)?" in second["answer"]

    third = router.run("6.5", session_id=session_id)
    assert "What is your minimum monthly payment?" in third["answer"]

    fourth = router.run("300", session_id=session_id)
    assert "How much do you currently have in emergency savings?" in fourth["answer"]

    fifth = router.run("10000", session_id=session_id)
    assert "Do you also invest for retirement? (yes/no)" in fifth["answer"]

    final = router.run("yes", session_id=session_id)
    answer = final["answer"]

    assert final["agent"] == "LoanAgent"
    assert final["conversation_state"]["complete"] is True
    assert "Analysis Agent" in answer
    assert "Loan Balance: $25,000" in answer
    assert "Interest Rate: 6.5%" in answer
    assert "Monthly Payment: $300" in answer
    assert "Emergency Savings: $10,000" in answer
    assert "Risk Level: Moderate" in answer
    assert "At 6.5%, paying early provides a guaranteed 6.5% return equivalent" in answer
    assert "Scenario 1: Minimum Payments" in answer
    assert "Scenario 2: Extra $200/month" in answer
    assert "Scenario 3: Lump-sum payment of $5,000" in answer
    assert "XAI Agent" in answer
    assert "Why?" in answer
    assert "1. Interest rate is relatively high." in answer
    assert "2. Emergency fund already exists." in answer
    assert "3. Early payoff reduces total interest cost." in answer
    assert "Finance RAG" in answer
    assert "finance/student_loans.txt" in answer


def test_loan_flow_accepts_trailing_currency_symbol():
    router = AgentRouter()
    session_id = "test_student_loan_trailing_currency"

    first = router.run("Should I pay off my student loan early?", session_id=session_id)
    assert first["router"]["route"] == "loan"

    second = router.run("30000$", session_id=session_id)

    assert second["agent"] == "LoanAgent"
    assert second["router"]["route"] == "loan"
    assert "What is your interest rate (%)?" in second["answer"]
    assert "valid balance value" not in second["answer"]
