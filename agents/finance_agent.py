import math
import re

from agents.base_agent import BaseAgent
from tools.finance_data_store import FinanceDataStore


class FinanceAgent(BaseAgent):
    name = "FinanceAgent"
    agent_type = "Finance"
    rag_category = "finance"

    def __init__(self):
        super().__init__()
        self.finance_store = FinanceDataStore()

    def run(self, query: str, prefilled_fields: dict | None = None, session_id: str = "default"):
        intent = self.detect_intent(query)
        if intent == "expense":
            return self.expense_agent(query)
        if intent == "budget":
            return self.budget_agent(query)
        if intent == "savings":
            return self.savings_agent(query)
        if intent == "loan":
            return self.loan_agent(query)
        if intent == "tax":
            return self.tax_agent(query)
        if intent == "investment":
            return self.investment_agent(query)
        if intent == "stock":
            return self.stock_agent(query)
        if intent == "crypto":
            return self.crypto_agent(query)
        return self.financial_report_agent(query)

    def detect_intent(self, query: str):
        q = query.lower()
        if any(k in q for k in ["add", "record"]) and "expense" in q:
            return "expense"
        if "expense" in q or "spend" in q or "spent" in q:
            return "report"
        if "budget" in q:
            return "budget"
        if "save" in q or "savings" in q:
            return "savings"
        if "loan" in q or "debt" in q:
            return "loan"
        if "tax" in q:
            return "tax"
        if "etf" in q or "investment" in q or "s&p" in q or "nasdaq" in q:
            return "investment"
        if "stock" in q or re.search(r"\b[A-Z]{2,5}\b", query):
            return "stock"
        if "crypto" in q or "bitcoin" in q or "ethereum" in q:
            return "crypto"
        return "report"

    def expense_agent(self, query: str):
        amount = FinanceDataStore.parse_money(query)
        category = self.extract_expense_category(query)
        if amount <= 0:
            answer = "ExpenseAgent / finance\n\nInvalid expense amount. Please enter an amount like $25."
            return self.response(query, ["ExpenseAgent: invalid amount."], answer, {"status": "failed"})

        record = self.finance_store.add_expense(category, amount)
        answer = "\n".join([
            "ExpenseAgent / finance",
            "",
            "Expense recorded successfully.",
            f"Date: {record['date']}",
            f"Category: {record['category']}",
            f"Amount: ${record['amount']:.2f}",
            "",
            f"Stored in: {self.finance_store.expenses_json}",
            f"Excel: {self.finance_store.expenses_xlsx}",
        ])
        return self.response(query, [
            "ExpenseAgent: parsed category and amount.",
            "Storage Agent: saved expense to JSON and Excel.",
        ], answer, {
            "selected_finance_agent": "ExpenseAgent",
            "expense": record,
            "data_sources": self.finance_store.ensure_ready(),
        })

    def budget_agent(self, query: str):
        income = FinanceDataStore.parse_money(query) or 6000
        budget = {
            "Housing": round(income * 0.30),
            "Food": round(income * 0.10),
            "Transportation": round(income * 0.0833),
            "Savings": round(income * 0.20),
            "Entertainment": round(income * 0.05),
        }
        remaining = round(income - sum(budget.values()))
        answer = "\n".join([
            "BudgetAgent / finance",
            "",
            f"Monthly Income: ${income:.0f}",
            "",
            f"Housing: ${budget['Housing']}",
            f"Food: ${budget['Food']}",
            f"Transportation: ${budget['Transportation']}",
            f"Savings: ${budget['Savings']}",
            f"Entertainment: ${budget['Entertainment']}",
            f"Remaining: ${remaining}",
            "",
            "This is a planning estimate, not financial advice.",
        ])
        return self.response(query, ["BudgetAgent: created 50/30/20-style monthly budget."], answer, {
            "selected_finance_agent": "BudgetAgent",
            "budget": {**budget, "Remaining": remaining},
        })

    def savings_agent(self, query: str):
        monthly = self.extract_monthly_savings(query) or 500
        years = self.extract_years(query) or 10
        annual_return = self.extract_percent(query) or 8
        monthly_rate = annual_return / 100 / 12
        months = years * 12
        future_value = monthly * (((1 + monthly_rate) ** months - 1) / monthly_rate) if monthly_rate else monthly * months
        answer = "\n".join([
            "SavingsAgent / finance",
            "",
            "Future Value Formula",
            "FV = PMT * (((1 + r)^n - 1) / r)",
            "",
            f"Monthly Savings: ${monthly:.0f}",
            f"Years: {years}",
            f"Annual Return: {annual_return:.1f}%",
            f"Estimated Future Value: ${future_value:,.2f}",
            "",
            "Explanation: consistent monthly contributions compound over time; the estimate depends strongly on actual returns.",
        ])
        return self.response(query, ["SavingsAgent: calculated compound future value."], answer, {
            "selected_finance_agent": "SavingsAgent",
            "future_value": round(future_value, 2),
        })

    def loan_agent(self, query: str):
        answer = "\n".join([
            "LoanAgent / finance",
            "",
            "Loan Details",
            "- Gather balance, interest rate, minimum payment, and payoff goal.",
            "",
            "Interest Analysis",
            "- Paying early usually helps most when the loan interest rate is higher than expected investment returns.",
            "",
            "Payoff Scenarios",
            "1. Minimum payments: maximum flexibility, higher total interest.",
            "2. Extra monthly payments: lower interest and faster payoff.",
            "3. Lump-sum payoff: best interest reduction if emergency savings are already healthy.",
            "",
            "Recommendation",
            "Pay high-interest debt early after keeping an emergency fund. For low-interest student loans, compare the rate against your savings/investment priorities.",
            "",
            "This is educational support, not financial advice.",
        ])
        return self.response(query, ["LoanAgent: generated payoff scenario framework."], answer, {
            "selected_finance_agent": "LoanAgent",
        })

    def tax_agent(self, query: str):
        salary = FinanceDataStore.parse_money(query) or 100000
        standard_deduction = 14600
        taxable = max(0, salary - standard_deduction)
        tax = self.estimate_single_federal_tax(taxable)
        net = salary - tax
        effective = tax / salary * 100 if salary else 0
        answer = "\n".join([
            "TaxAgent / finance",
            "",
            f"Gross Salary: ${salary:,.0f}",
            f"Estimated Taxable Income: ${taxable:,.0f}",
            f"Estimated Federal Tax: ${tax:,.2f}",
            f"Estimated Net Income Before State/FICA: ${net:,.2f}",
            f"Effective Federal Tax Rate: {effective:.2f}%",
            "",
            "Assumption: single filer, standard deduction, simplified federal estimate. This is not tax advice.",
        ])
        return self.response(query, ["TaxAgent: estimated simplified federal income tax."], answer, {
            "selected_finance_agent": "TaxAgent",
            "estimated_tax": round(tax, 2),
        })

    def investment_agent(self, query: str):
        answer = "\n".join([
            "InvestmentAgent / finance",
            "",
            "Compare: S&P 500 ETF vs NASDAQ ETF",
            "",
            "Research",
            "- S&P 500 ETFs track a broad large-cap US equity index.",
            "- NASDAQ-focused ETFs are typically more technology-heavy and growth-oriented.",
            "",
            "Historical Performance",
            "- NASDAQ ETFs may outperform during tech-led bull markets.",
            "- S&P 500 ETFs are usually more diversified across sectors.",
            "",
            "Risk Analysis",
            "- S&P 500 ETF: Medium equity risk, broader diversification.",
            "- NASDAQ ETF: Higher concentration risk, higher volatility.",
            "",
            "Recommendation",
            "Use S&P 500 as a broad core holding; add NASDAQ exposure if you accept higher tech concentration and volatility.",
            "",
            "This is educational support, not investment advice.",
        ])
        return self.response(query, ["InvestmentAgent: compared ETF risk and use cases."], answer, {
            "selected_finance_agent": "InvestmentAgent",
        })

    def stock_agent(self, query: str):
        ticker = self.extract_ticker(query) or "AAPL"
        answer = "\n".join([
            "StockAgent / finance",
            "",
            f"Stock Analysis: {ticker}",
            "",
            "Market Data",
            "- Live market data is not connected in this local run.",
            "",
            "Price History",
            "- Add a market-data API to fetch historical candles and 52-week range.",
            "",
            "Technical Indicators",
            "- Suggested: 20/50/200-day moving averages, RSI, volume trend, support/resistance.",
            "",
            "Analysis",
            "Current Trend: Needs live market data",
            "52-week High: Requires market API",
            "52-week Low: Requires market API",
            "Risk Level: Medium for large-cap equities, but verify with live data.",
            "",
            "This is educational support, not investment advice.",
        ])
        return self.response(query, ["StockAgent: generated market-analysis scaffold."], answer, {
            "selected_finance_agent": "StockAgent",
            "ticker": ticker,
        })

    def crypto_agent(self, query: str):
        answer = "\n".join([
            "CryptoAgent / finance",
            "",
            "Crypto Analysis",
            "- Crypto assets are highly volatile and can have large drawdowns.",
            "- Evaluate liquidity, custody, regulation, security, and allocation size.",
            "",
            "Recommendation",
            "Use small position sizing, avoid leverage, and verify live market data before acting.",
            "",
            "This is educational support, not investment advice.",
        ])
        return self.response(query, ["CryptoAgent: generated risk-first crypto summary."], answer, {
            "selected_finance_agent": "CryptoAgent",
        })

    def financial_report_agent(self, query: str):
        income = self.extract_income(query)
        spending = self.extract_spending(query)
        summary = self.finance_store.monthly_summary()
        lines = [
            "FinancialReportAgent / finance",
            "",
            "Financial Report",
        ]
        if income:
            lines.append(f"Income: ${income:,.2f}")
        if spending:
            lines.append(f"Expenses: ${spending:,.2f}")
            savings = income - spending if income else 0
            if income:
                lines.append(f"Potential Savings: ${savings:,.2f}")
                lines.append(f"Savings Rate: {(savings / income * 100):.1f}%")
                lines.append(f"Recommendation: Save at least ${max(income * 0.20, savings):,.2f} if cash flow allows.")
        lines += [
            "",
            "Tracked Expenses",
            f"- Count: {summary['count']}",
            f"- Total: ${summary['total']:,.2f}",
        ]
        for category, amount in summary["by_category"].items():
            lines.append(f"- {category}: ${amount:,.2f}")
        lines += ["", "This is educational support, not financial advice."]
        return self.response(query, ["FinancialReportAgent: summarized income, spending, and stored expenses."], "\n".join(lines), {
            "selected_finance_agent": "FinancialReportAgent",
            "summary": summary,
        })

    @staticmethod
    def extract_expense_category(query: str):
        q = query.lower()
        categories = {
            "restaurant": "Food",
            "food": "Food",
            "grocery": "Groceries",
            "groceries": "Groceries",
            "rent": "Housing",
            "gas": "Transportation",
            "uber": "Transportation",
            "movie": "Entertainment",
        }
        for key, category in categories.items():
            if key in q:
                return category
        return "Other"

    @staticmethod
    def extract_income(query: str):
        match = re.search(r"(?:earn|income|salary)\D{0,20}\$?\s*(\d[\d,]*(?:\.\d+)?)", query, re.I)
        return float(match.group(1).replace(",", "")) if match else 0.0

    @staticmethod
    def extract_spending(query: str):
        match = re.search(r"(?:spend|spent|expenses?)\D{0,20}\$?\s*(\d[\d,]*(?:\.\d+)?)", query, re.I)
        return float(match.group(1).replace(",", "")) if match else 0.0

    @staticmethod
    def extract_monthly_savings(query: str):
        match = re.search(r"save\s+\$?\s*(\d[\d,]*(?:\.\d+)?)\s*/?\s*month", query, re.I)
        return float(match.group(1).replace(",", "")) if match else FinanceDataStore.parse_money(query)

    @staticmethod
    def extract_years(query: str):
        match = re.search(r"(\d+)\s*years?", query, re.I)
        return int(match.group(1)) if match else 0

    @staticmethod
    def extract_percent(query: str):
        match = re.search(r"(\d+(?:\.\d+)?)\s*%", query)
        return float(match.group(1)) if match else 0.0

    @staticmethod
    def extract_ticker(query: str):
        match = re.search(r"\b([A-Z]{2,5})\b", query)
        return match.group(1) if match else ""

    @staticmethod
    def estimate_single_federal_tax(taxable: float):
        brackets = [
            (11600, 0.10),
            (47150, 0.12),
            (100525, 0.22),
            (191950, 0.24),
            (243725, 0.32),
            (609350, 0.35),
            (math.inf, 0.37),
        ]
        tax = 0.0
        previous = 0.0
        for limit, rate in brackets:
            if taxable <= previous:
                break
            taxed = min(taxable, limit) - previous
            tax += taxed * rate
            previous = limit
        return tax
