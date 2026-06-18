from typing import Dict, List, Any
import math


class LoanCrew:
    def __init__(self):
        pass

    def run(self, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        # Extract loan parameters
        balance = loan_data.get("balance", 0)
        interest_rate = loan_data.get("interest_rate", 0)
        monthly_payment = loan_data.get("monthly_payment", 0)
        emergency_savings = loan_data.get("emergency_savings", 0)
        invests_for_retirement = loan_data.get("invests_for_retirement", False)
        
        # Perform analysis
        risk_level = self.assess_risk_level(balance, interest_rate, emergency_savings)
        interest_analysis = self.analyze_interest_rate(interest_rate)
        scenarios = self.calculate_scenarios(balance, interest_rate, monthly_payment, emergency_savings)
        recommendation = self.generate_recommendation(balance, interest_rate, monthly_payment, emergency_savings, invests_for_retirement, risk_level)
        
        crew_steps = [
            {"thought": "Loan Analysis: assessing risk level", "output": f"Risk Level: {risk_level}"},
            {"thought": "Interest Analyzer: evaluating interest rate", "output": interest_analysis},
            {"thought": "Scenario Calculator: computing payoff scenarios", "output": f"{len(scenarios)} scenarios calculated"},
            {"thought": "Recommendation Engine: generating advice", "output": recommendation["action"]},
        ]
        
        return {
            "loan_data": loan_data,
            "risk_level": risk_level,
            "interest_analysis": interest_analysis,
            "scenarios": scenarios,
            "recommendation": recommendation,
            "crew_steps": crew_steps,
        }

    @staticmethod
    def assess_risk_level(balance: float, interest_rate: float, emergency_savings: float) -> str:
        """Assess the risk level of the loan situation."""
        # Calculate months of emergency savings
        monthly_expenses_estimate = balance / 100  # Rough estimate
        emergency_months = emergency_savings / monthly_expenses_estimate if monthly_expenses_estimate > 0 else 0
        
        if interest_rate > 8:
            return "High"
        elif interest_rate > 5:
            if emergency_months < 3:
                return "High"
            return "Moderate"
        else:
            if emergency_months < 3:
                return "Moderate"
            return "Low"

    @staticmethod
    def analyze_interest_rate(interest_rate: float) -> str:
        """Analyze the interest rate and provide context."""
        if interest_rate > 8:
            return f"At {interest_rate}%, this is a high-interest loan. Paying early provides a guaranteed {interest_rate}% return equivalent, which beats most conservative investments."
        elif interest_rate > 5:
            return f"At {interest_rate}%, paying early provides a guaranteed {interest_rate}% return equivalent. This is competitive with many investment returns."
        elif interest_rate > 3:
            return f"At {interest_rate}%, the guaranteed return from early payoff is moderate. Consider investment alternatives."
        else:
            return f"At {interest_rate}%, this is a low-interest loan. Investing may provide better returns than early payoff."

    def calculate_scenarios(self, balance: float, interest_rate: float, monthly_payment: float, emergency_savings: float) -> List[Dict[str, Any]]:
        """Calculate different payoff scenarios."""
        monthly_rate = interest_rate / 100 / 12
        scenarios = []
        
        # Scenario 1: Minimum payments
        if monthly_payment > 0:
            months_min = self.calculate_payoff_months(balance, monthly_rate, monthly_payment)
            total_interest_min = self.calculate_total_interest(balance, monthly_rate, monthly_payment, months_min)
            scenarios.append({
                "name": "Minimum Payments",
                "monthly_payment": monthly_payment,
                "months_to_payoff": months_min,
                "years_to_payoff": months_min / 12,
                "total_interest": total_interest_min,
                "total_paid": balance + total_interest_min,
            })
        
        # Scenario 2: Extra $200/month
        extra_payment = 200
        if monthly_payment + extra_payment > 0:
            months_extra = self.calculate_payoff_months(balance, monthly_rate, monthly_payment + extra_payment)
            total_interest_extra = self.calculate_total_interest(balance, monthly_rate, monthly_payment + extra_payment, months_extra)
            months_saved = scenarios[0]["months_to_payoff"] - months_extra if scenarios else 0
            interest_saved = scenarios[0]["total_interest"] - total_interest_extra if scenarios else 0
            scenarios.append({
                "name": "Extra $200/month",
                "monthly_payment": monthly_payment + extra_payment,
                "months_to_payoff": months_extra,
                "years_to_payoff": months_extra / 12,
                "total_interest": total_interest_extra,
                "total_paid": balance + total_interest_extra,
                "months_saved": months_saved,
                "years_saved": months_saved / 12,
                "interest_saved": interest_saved,
            })
        
        # Scenario 3: Lump-sum payment (if emergency savings allow)
        lump_sum = min(5000, emergency_savings * 0.5)  # Use up to 50% of emergency savings, max $5000
        if lump_sum > 0:
            new_balance = balance - lump_sum
            months_lump = self.calculate_payoff_months(new_balance, monthly_rate, monthly_payment)
            total_interest_lump = self.calculate_total_interest(new_balance, monthly_rate, monthly_payment, months_lump)
            months_saved = scenarios[0]["months_to_payoff"] - months_lump if scenarios else 0
            interest_saved = scenarios[0]["total_interest"] - total_interest_lump if scenarios else 0
            scenarios.append({
                "name": f"Lump-sum payment of ${lump_sum:,.0f}",
                "lump_sum": lump_sum,
                "new_balance": new_balance,
                "monthly_payment": monthly_payment,
                "months_to_payoff": months_lump,
                "years_to_payoff": months_lump / 12,
                "total_interest": total_interest_lump,
                "total_paid": lump_sum + new_balance + total_interest_lump,
                "months_saved": months_saved,
                "years_saved": months_saved / 12,
                "interest_saved": interest_saved,
            })
        
        return scenarios

    @staticmethod
    def calculate_payoff_months(balance: float, monthly_rate: float, monthly_payment: float) -> int:
        """Calculate months to payoff using amortization formula."""
        if monthly_rate == 0:
            return math.ceil(balance / monthly_payment)
        if monthly_payment <= balance * monthly_rate:
            return 999  # Will never pay off
        n = -math.log(1 - (balance * monthly_rate) / monthly_payment) / math.log(1 + monthly_rate)
        return math.ceil(n)

    @staticmethod
    def calculate_total_interest(balance: float, monthly_rate: float, monthly_payment: float, months: int) -> float:
        """Calculate total interest paid over the loan term."""
        total_paid = monthly_payment * months
        return total_paid - balance

    def generate_recommendation(self, balance: float, interest_rate: float, monthly_payment: float, 
                               emergency_savings: float, invests_for_retirement: bool, risk_level: str) -> Dict[str, Any]:
        """Generate personalized recommendation with explanation."""
        recommendation = {
            "action": "",
            "why": [],
            "priority": "",
            "next_steps": []
        }
        
        # Assess emergency fund
        emergency_months = emergency_savings / (monthly_payment * 2) if monthly_payment > 0 else 0
        
        if emergency_months < 3:
            recommendation["action"] = "Build emergency fund first"
            recommendation["priority"] = "High"
            recommendation["why"] = [
                f"You only have {emergency_months:.1f} months of emergency savings",
                "Financial experts recommend 3-6 months of expenses",
                "Build emergency fund before accelerating loan payoff"
            ]
            recommendation["next_steps"] = [
                "Save until you have 3-6 months of expenses in emergency fund",
                "Continue minimum payments on loan",
                "Once emergency fund is built, revisit loan payoff strategy"
            ]
        elif interest_rate >= 6:
            recommendation["action"] = "Pay off loan aggressively"
            recommendation["priority"] = "High" if interest_rate > 7 else "Medium"
            recommendation["why"] = [
                "Interest rate is relatively high.",
                "Emergency fund already exists.",
                "Early payoff reduces total interest cost."
            ]
            recommendation["next_steps"] = [
                "Consider extra payments of $200-500/month",
                "Use any bonuses or tax refunds for lump-sum payments",
                "Refinance if possible to lower rate"
            ]
        elif interest_rate > 4:
            recommendation["action"] = "Balanced approach"
            recommendation["priority"] = "Medium"
            recommendation["why"] = [
                f"Interest rate of {interest_rate}% is moderate",
                "Consider both loan payoff and investment",
                "Emergency fund is sufficient"
            ]
            if invests_for_retirement:
                recommendation["why"].append("You already invest for retirement")
                recommendation["next_steps"] = [
                    "Split extra money between loan payoff and investments",
                    "Consider 50/50 split or based on your risk tolerance",
                    "Pay off loan if investment returns are uncertain"
                ]
            else:
                recommendation["why"].append("No current retirement investing detected")
                recommendation["next_steps"] = [
                    "Start retirement investing (e.g., 401k match, IRA)",
                    "Consider moderate extra loan payments",
                    "Balance between debt payoff and investing"
                ]
        else:
            recommendation["action"] = "Invest instead of paying early"
            recommendation["priority"] = "Low"
            recommendation["why"] = [
                f"Interest rate of {interest_rate}% is low",
                "Investment returns may exceed loan interest",
                "Emergency fund is sufficient"
            ]
            recommendation["next_steps"] = [
                "Make minimum payments on loan",
                "Invest extra money in tax-advantaged accounts",
                "Consider high-yield savings for short-term goals"
            ]
        
        return recommendation
