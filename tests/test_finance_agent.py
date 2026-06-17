import json

from agents.agent_router import AgentRouter
from agents.finance_agent import FinanceAgent
from tools.finance_data_store import FinanceDataStore


def make_finance_agent(tmp_path):
    agent = FinanceAgent()
    agent.finance_store = FinanceDataStore(data_dir=str(tmp_path / "finance_data"))
    agent.finance_store.ensure_ready()
    return agent


def test_expense_agent_records_json_and_excel(tmp_path):
    agent = make_finance_agent(tmp_path)

    result = agent.run("Add $25 restaurant expense.")

    assert "Expense recorded successfully." in result["answer"]
    assert result["extra"]["expense"]["category"] == "Food"
    assert result["extra"]["expense"]["amount"] == 25

    expenses_path = tmp_path / "finance_data" / "expenses.json"
    excel_path = tmp_path / "finance_data" / "expenses.xlsx"
    saved = json.loads(expenses_path.read_text(encoding="utf-8"))
    assert saved[0]["category"] == "Food"
    assert saved[0]["amount"] == 25
    assert excel_path.exists()
    assert FinanceDataStore.read_sheet_names(excel_path) == ["Expenses"]


def test_budget_agent_monthly_budget():
    result = FinanceAgent().run("Create a monthly budget for $6000 income.")

    assert result["extra"]["selected_finance_agent"] == "BudgetAgent"
    assert "Housing: $1800" in result["answer"]
    assert "Food: $600" in result["answer"]
    assert "Savings: $1200" in result["answer"]


def test_financial_report_income_expenses():
    result = FinanceAgent().run("I earn $5000/month and spend $3500. How much should I save?")

    assert result["extra"]["selected_finance_agent"] == "FinancialReportAgent"
    assert "Potential Savings: $1,500.00" in result["answer"]
    assert "Savings Rate: 30.0%" in result["answer"]


def test_savings_agent_future_value():
    result = FinanceAgent().run("If I save $500/month for 10 years at 8% return, how much will I have?")

    assert result["extra"]["selected_finance_agent"] == "SavingsAgent"
    assert "Future Value Formula" in result["answer"]
    assert "Estimated Future Value" in result["answer"]


def test_tax_investment_stock_loan_outputs():
    tax = FinanceAgent().run("Estimate my federal tax for $100,000 salary.")
    assert "Estimated Federal Tax" in tax["answer"]

    investment = FinanceAgent().run("Compare S&P 500 ETF vs NASDAQ ETF.")
    assert "InvestmentAgent / finance" in investment["answer"]
    assert "Risk Analysis" in investment["answer"]

    stock = FinanceAgent().run("Analyze AAPL stock.")
    assert stock["extra"]["selected_finance_agent"] == "StockAgent"
    assert "Stock Analysis: AAPL" in stock["answer"]

    loan = FinanceAgent().run("Should I pay off my student loan early?")
    assert "Payoff Scenarios" in loan["answer"]


def test_router_sends_finance_queries_to_finance_agent():
    router = AgentRouter()
    for query in [
        "Track my monthly expenses.",
        "Add $25 restaurant expense.",
        "Create a monthly budget for $6000 income.",
        "Analyze AAPL stock.",
        "Estimate my federal tax for $100,000 salary.",
    ]:
        route, agent = router.route(query)
        assert route == "finance"
        assert agent.name == "FinanceAgent"
