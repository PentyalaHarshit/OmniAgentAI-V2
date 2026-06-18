import os
import re
from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from crews.loan_crew import LoanCrew


class LoanAgent(BaseAgent):
    name = "LoanAgent"
    agent_type = "Loan"
    rag_category = "finance"

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = LoanCrew()
        self.conversation_state = {}
        self.finance_kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "finance")

    def run(self, query: str, conversation_history: list = None, user_input: str = None, conversation_state: dict = None):
        # Handle conversational flow
        if conversation_history is None:
            conversation_history = []
        
        # Restore conversation state if provided
        if conversation_state:
            self.conversation_state = conversation_state
        
        # Check if this is the start of a new conversation
        if not conversation_history and not self.conversation_state:
            return self.start_conversation(query)
        
        # If user_input is provided, process it as a response to a question
        if user_input:
            return self.process_user_input(user_input)

        # Router-managed follow-ups arrive as the next query while a loan
        # conversation state is active.
        if self.conversation_state and not self.conversation_state.get("complete"):
            return self.process_user_input(query)
        
        # Otherwise, run analysis with collected data
        if self.conversation_state.get("complete"):
            return self.run_analysis()
        
        return self.start_conversation(query)

    def start_conversation(self, query: str):
        """Start the loan conversation by asking the first question."""
        self.conversation_state = {
            "step": 0,
            "data": {},
            "complete": False
        }
        
        questions = [
            "What is your current loan balance?",
            "What is your interest rate (%)?",
            "What is your minimum monthly payment?",
            "How much do you currently have in emergency savings?",
            "Do you also invest for retirement? (yes/no)"
        ]
        
        self.conversation_state["current_question"] = questions[0]
        
        result = self.response(
            query,
            ["Starting loan payoff conversation", "Gathering loan information"],
            questions[0],
            {"conversation_state": self.conversation_state}
        )
        # Include conversation state in the result for persistence
        result["conversation_state"] = self.conversation_state
        return result

    def process_user_input(self, user_input: str):
        """Process user's response to a question."""
        step = self.conversation_state.get("step", 0)
        data = self.conversation_state.get("data", {})
        
        questions = [
            "What is your current loan balance?",
            "What is your interest rate (%)?",
            "What is your minimum monthly payment?",
            "How much do you currently have in emergency savings?",
            "Do you also invest for retirement? (yes/no)"
        ]
        
        data_keys = ["balance", "interest_rate", "monthly_payment", "emergency_savings", "invests_for_retirement"]
        
        # Parse and store the user input
        try:
            if step < 4:  # Numeric fields
                value = self.parse_money_or_percent(user_input)
                data[data_keys[step]] = value
            else:  # Boolean field
                data[data_keys[step]] = user_input.lower().startswith("y")
        except ValueError:
            result = self.response(
                user_input,
                ["Error parsing input", "Requesting clarification"],
                f"Please provide a valid {data_keys[step]} value.",
                {"conversation_state": self.conversation_state}
            )
            result["conversation_state"] = self.conversation_state
            return result
        
        self.conversation_state["data"] = data
        self.conversation_state["step"] = step + 1
        
        # Check if all questions have been answered
        if step + 1 >= len(questions):
            self.conversation_state["complete"] = True
            result = self.run_analysis()
            result["conversation_state"] = {"complete": True}
            return result
        
        # Ask the next question
        self.conversation_state["current_question"] = questions[step + 1]
        
        result = self.response(
            user_input,
            [f"Collected {data_keys[step]}", "Asking next question"],
            questions[step + 1],
            {"conversation_state": self.conversation_state}
        )
        result["conversation_state"] = self.conversation_state
        return result

    @staticmethod
    def parse_money_or_percent(user_input: str) -> float:
        """Parse common numeric answers such as "$30,000", "30000$", or "6.5%"."""
        text = str(user_input).strip()
        match = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", text)
        if not match:
            raise ValueError("No numeric value found")
        return float(match.group(0).replace(",", ""))

    def retrieve_finance_rag(self, query: str) -> str:
        """Retrieve relevant information from finance knowledge base."""
        rag_content = ""
        
        finance_files = {
            "student_loans.txt": "Federal student loan guidance, repayment plans, forgiveness programs",
            "budgeting.txt": "Budgeting rules, emergency fund recommendations, debt payoff strategies",
            "investing.txt": "Investment priorities, expected returns, asset allocation",
            "mortgage.txt": "Mortgage types, refinancing considerations, home equity"
        }
        
        for filename, description in finance_files.items():
            file_path = os.path.join(self.finance_kb_path, filename)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        rag_content += f"\n--- {filename} ({description}) ---\n{content}\n"
                except Exception as e:
                    continue
        
        return rag_content

    def run_analysis(self):
        """Run the loan analysis with collected data."""
        data = self.conversation_state.get("data", {})
        
        tasks = [
            "Assess risk level",
            "Analyze interest rate",
            "Calculate payoff scenarios",
            "Generate recommendation",
            "Provide explanation",
            "Retrieve finance knowledge"
        ]
        
        thoughts = self.tot.create_thoughts(self.agent_type, str(data), tasks, max_thoughts=12)
        crew_result = self.crew.run(data)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        
        # Retrieve finance RAG content
        rag_content = self.retrieve_finance_rag("loan payoff strategy")
        crew_result["rag_content"] = rag_content
        
        answer = self.build_analysis_answer(crew_result)
        
        result = self.response(
            str(data),
            thoughts + crew_thoughts,
            answer,
            {"crew_result": crew_result}
        )
        # Reset conversation state for next conversation after producing the
        # result payload.
        self.conversation_state = {}
        return result

    def build_analysis_answer(self, crew_result: dict):
        """Build the comprehensive analysis answer."""
        data = crew_result.get("loan_data", {})
        risk_level = crew_result.get("risk_level", "")
        interest_analysis = crew_result.get("interest_analysis", "")
        scenarios = crew_result.get("scenarios", [])
        recommendation = crew_result.get("recommendation", {})
        rag_content = crew_result.get("rag_content", "")
        
        answer = (
            "Analysis Agent\n\n"
            f"Loan Balance: ${data.get('balance', 0):,.0f}\n"
            f"Interest Rate: {data.get('interest_rate', 0)}%\n"
            f"Monthly Payment: ${data.get('monthly_payment', 0):,.0f}\n"
            f"Emergency Savings: ${data.get('emergency_savings', 0):,.0f}\n\n"
            f"Risk Level: {risk_level}\n\n"
            "Interest Analysis:\n"
            f"{interest_analysis}\n\n"
        )
        
        # Add scenarios
        answer += "Payoff Scenarios:\n"
        for idx, scenario in enumerate(scenarios, start=1):
            answer += f"\nScenario {idx}: {scenario['name']}\n"
            answer += f"- Monthly Payment: ${scenario.get('monthly_payment', 0):,.0f}\n"
            answer += f"- Time to Payoff: {scenario.get('years_to_payoff', 0):.1f} years\n"
            answer += f"- Total Interest: ${scenario.get('total_interest', 0):,.0f}\n"
            if 'interest_saved' in scenario:
                answer += f"- Interest Savings: ${scenario['interest_saved']:,.0f}\n"
            if 'years_saved' in scenario:
                answer += f"- Time Saved: {scenario['years_saved']:.1f} years\n"
        
        # Add recommendation
        answer += "\n\nXAI Agent\nRecommendation Explanation\n\n"
        answer += f"Action: {recommendation.get('action', 'N/A')}\n"
        answer += f"Priority: {recommendation.get('priority', 'N/A')}\n\n"
        answer += "Why?\n"
        for idx, reason in enumerate(recommendation.get('why', []), start=1):
            answer += f"{idx}. {reason}\n"
        
        answer += "\nNext Steps:\n"
        for step in recommendation.get('next_steps', []):
            answer += f"- {step}\n"
        
        # Add Finance RAG section
        if rag_content:
            answer += "\n\nFinance RAG\n\n"
            answer += "Retrieved guidance from finance/ knowledge base:\n"
            answer += "- Federal student loan guidance\n"
            answer += "- Debt payoff strategies\n"
            answer += "- Emergency fund recommendations\n"
            answer += "- Investment priority tradeoffs\n"
            answer += "\nSources:\n"
            answer += "- finance/student_loans.txt\n"
            answer += "- finance/budgeting.txt\n"
            answer += "- finance/investing.txt\n"
            answer += "- finance/mortgage.txt"
        
        return answer
