import re
from typing import Dict, List, Any


class SelfCorrectionCrew:
    def __init__(self):
        pass

    def run(self, query: str, code: str = None, test_result: str = None):
        # Extract code and test result from query if not provided
        if code is None:
            code = self.extract_code(query)
        if test_result is None:
            test_result = self.extract_test_result(query)
        
        language = self.detect_language(code or query)
        
        # Perform self-correction analysis
        failure_analysis = self.analyze_failure(code, test_result, language)
        improvement_strategy = self.develop_improvement_strategy(failure_analysis)
        improved_code = self.generate_improved_code(code, improvement_strategy, language)
        verification_plan = self.create_verification_plan(improvement_strategy)
        
        crew_steps = [
            {"thought": "SelfCorrection Agent: analyzing code failure", "output": "Failure analyzed"},
            {"thought": "Reason Engine: identifying root cause", "output": failure_analysis["root_cause"]},
            {"thought": "Action Planner: developing improvement strategy", "output": improvement_strategy["strategy"]},
            {"thought": "Code Improver: applying corrections", "output": "Improved code generated"},
            {"thought": "Verification Designer: creating test plan", "output": "Verification plan created"},
        ]
        
        return {
            "language": language,
            "failure_analysis": failure_analysis,
            "improvement_strategy": improvement_strategy,
            "improved_code": improved_code,
            "verification_plan": verification_plan,
            "original_code": code,
            "test_result": test_result,
            "crew_steps": crew_steps,
        }

    @staticmethod
    def extract_code(query: str) -> str:
        """Extract code block from query if present."""
        code_pattern = r'```(?:python|cpp|c\+\+|java|javascript|js)?\n([\s\S]*?)```'
        match = re.search(code_pattern, query)
        if match:
            return match.group(1).strip()
        
        lines = query.strip().split('\n')
        if len(lines) > 1 and any(line.strip().startswith(('def ', 'class ', 'int ', 'void ', 'function ', 'import ', '#include')) for line in lines):
            return query.strip()
        
        return ""

    @staticmethod
    def extract_test_result(query: str) -> str:
        """Extract test result from query."""
        error_patterns = [
            r'(?:failed|error|wrong answer|time limit|memory limit)[:\s]*([\s\S]*?)(?:\n\n|\Z)',
            r'(?:test|output)[:\s]*([\s\S]*?)(?:\n\n|\Z)',
        ]
        
        for pattern in error_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""

    @staticmethod
    def detect_language(code_or_query: str) -> str:
        """Detect the programming language from code."""
        text = code_or_query.lower()
        
        if 'def ' in text and 'import ' in text:
            return "python"
        if '#include' in text or 'int main()' in text or 'std::' in text:
            return "cpp"
        if 'public class' in text or 'System.out' in text:
            return "java"
        if 'function ' in text or 'const ' in text and 'let ' in text:
            return "javascript"
        
        return "python"

    def analyze_failure(self, code: str, test_result: str, language: str) -> Dict[str, Any]:
        """Analyze why the code failed."""
        test_lower = (test_result or "").lower()
        code_lower = (code or "").lower()
        
        failure_analysis = {
            "root_cause": "unknown",
            "failure_type": "unknown",
            "location": "unknown",
            "confidence": 0
        }
        
        # Time limit exceeded
        if "time limit" in test_lower or "timeout" in test_lower:
            failure_analysis.update({
                "root_cause": "inefficient algorithm",
                "failure_type": "time_complexity",
                "location": self.find_inefficient_code(code),
                "confidence": 85
            })
        
        # Memory limit exceeded
        elif "memory limit" in test_lower or "out of memory" in test_lower:
            failure_analysis.update({
                "root_cause": "excessive memory usage",
                "failure_type": "space_complexity",
                "location": self.find_memory_intensive_code(code),
                "confidence": 85
            })
        
        # Wrong answer
        elif "wrong answer" in test_lower or "incorrect" in test_lower:
            failure_analysis.update({
                "root_cause": "logic error or incorrect algorithm",
                "failure_type": "logic_error",
                "location": self.find_logic_error_code(code),
                "confidence": 70
            })
        
        # Runtime error
        elif "runtime error" in test_lower or "exception" in test_lower:
            failure_analysis.update({
                "root_cause": "runtime exception or crash",
                "failure_type": "runtime_error",
                "location": self.find_risky_code(code),
                "confidence": 80
            })
        
        # Compilation error
        elif "compilation error" in test_lower or "syntax error" in test_lower:
            failure_analysis.update({
                "root_cause": "syntax or compilation issue",
                "failure_type": "syntax_error",
                "location": self.find_syntax_error_location(code),
                "confidence": 90
            })
        
        return failure_analysis

    @staticmethod
    def find_inefficient_code(code: str) -> str:
        """Find inefficient code sections."""
        if not code:
            return "unknown"
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if line.count('for') > 1 or line.count('while') > 1:
                return f"line {i + 1} (nested loops)"
            if 'O(n²)' in line or 'O(n^2)' in line:
                return f"line {i + 1}"
        
        return "unknown"

    @staticmethod
    def find_memory_intensive_code(code: str) -> str:
        """Find memory-intensive code sections."""
        if not code:
            return "unknown"
        
        lines = code.split('\n')
        memory_patterns = ['vector', 'array', 'list', 'dict', 'hashmap', 'malloc', 'new ']
        
        for i, line in enumerate(lines):
            if any(pattern in line.lower() for pattern in memory_patterns):
                return f"line {i + 1}"
        
        return "unknown"

    @staticmethod
    def find_logic_error_code(code: str) -> str:
        """Find code with potential logic errors."""
        if not code:
            return "unknown"
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if 'if' in line and 'else' not in line and i < len(lines) - 1:
                return f"line {i + 1} (potential missing else)"
            if '==' in line and '=' in line:
                return f"line {i + 1} (potential assignment vs comparison)"
        
        return "unknown"

    @staticmethod
    def find_risky_code(code: str) -> str:
        """Find risky code that might cause runtime errors."""
        if not code:
            return "unknown"
        
        lines = code.split('\n')
        risky_patterns = ['[', '*', '->', '/', '%']
        
        for i, line in enumerate(lines):
            if any(pattern in line for pattern in risky_patterns):
                return f"line {i + 1}"
        
        return "unknown"

    @staticmethod
    def find_syntax_error_location(code: str) -> str:
        """Find potential syntax error location."""
        if not code:
            return "unknown"
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if line.count('(') != line.count(')'):
                return f"line {i + 1} (unmatched parentheses)"
            if line.count('[') != line.count(']'):
                return f"line {i + 1} (unmatched brackets)"
        
        return "unknown"

    def develop_improvement_strategy(self, failure_analysis: Dict) -> Dict[str, Any]:
        """Develop strategy to improve the code."""
        failure_type = failure_analysis.get("failure_type", "unknown")
        
        strategies = {
            "time_complexity": {
                "strategy": "optimize algorithm complexity",
                "actions": [
                    "Replace nested loops with more efficient data structures",
                    "Use hash maps for O(1) lookups instead of linear search",
                    "Implement memoization or dynamic programming",
                    "Use binary search instead of linear search",
                    "Consider using segment trees or Fenwick trees for range queries"
                ],
                "priority": "high"
            },
            "space_complexity": {
                "strategy": "reduce memory usage",
                "actions": [
                    "Use in-place algorithms when possible",
                    "Free unused memory immediately",
                    "Use more compact data structures",
                    "Implement streaming processing instead of storing all data",
                    "Use bit manipulation for boolean arrays"
                ],
                "priority": "high"
            },
            "logic_error": {
                "strategy": "fix logic and algorithm",
                "actions": [
                    "Review problem statement and constraints",
                    "Add debug output to trace execution",
                    "Verify edge cases are handled correctly",
                    "Check for off-by-one errors",
                    "Validate algorithm correctness with simple examples"
                ],
                "priority": "critical"
            },
            "runtime_error": {
                "strategy": "add error handling and bounds checking",
                "actions": [
                    "Add null/None checks before dereferencing",
                    "Validate array indices before access",
                    "Add try-catch blocks for exception handling",
                    "Check for division by zero",
                    "Add input validation"
                ],
                "priority": "critical"
            },
            "syntax_error": {
                "strategy": "fix syntax issues",
                "actions": [
                    "Check for matching brackets and parentheses",
                    "Verify language-specific syntax",
                    "Review indentation and formatting",
                    "Check for missing semicolons or colons",
                    "Validate variable declarations"
                ],
                "priority": "critical"
            },
        }
        
        return strategies.get(failure_type, {
            "strategy": "general improvement",
            "actions": ["Review code structure", "Add comments", "Improve readability"],
            "priority": "medium"
        })

    def generate_improved_code(self, code: str, strategy: Dict, language: str) -> str:
        """Generate improved code based on strategy."""
        if not code:
            return ""
        
        improved = code
        actions = strategy.get("actions", [])
        
        # Apply common improvements
        for action in actions:
            if "hash map" in action.lower():
                improved = self.suggest_hashmap_usage(improved, language)
            elif "bounds checking" in action.lower():
                improved = self.add_bounds_checking(improved, language)
            elif "memoization" in action.lower():
                improved = self.suggest_memoization(improved, language)
        
        return improved

    @staticmethod
    def suggest_hashmap_usage(code: str, language: str) -> str:
        """Suggest using hash maps for lookups."""
        lines = code.split('\n')
        improved = []
        
        for line in lines:
            improved.append(line)
            if 'in ' in line and 'for' not in line:
                indent = len(line) - len(line.lstrip())
                improved.append(' ' * indent + f'# TODO: Consider using dict/set for O(1) lookup' if language == "python" else '// TODO: Consider using unordered_map/set for O(1) lookup')
        
        return '\n'.join(improved)

    @staticmethod
    def add_bounds_checking(code: str, language: str) -> str:
        """Add bounds checking to code."""
        lines = code.split('\n')
        improved = []
        
        for line in lines:
            improved.append(line)
            if '[' in line and ']' in line and 'if' not in line:
                indent = len(line) - len(line.lstrip())
                improved.append(' ' * indent + f'# TODO: Add bounds check' if language == "python" else '// TODO: Add bounds check')
        
        return '\n'.join(improved)

    @staticmethod
    def suggest_memoization(code: str, language: str) -> str:
        """Suggest adding memoization."""
        lines = code.split('\n')
        improved = []
        
        for line in lines:
            if 'def ' in line:
                indent = len(line) - len(line.lstrip())
                improved.append(' ' * indent + f'# TODO: Consider adding memoization' if language == "python" else '// TODO: Consider adding memoization')
            improved.append(line)
        
        return '\n'.join(improved)

    def create_verification_plan(self, strategy: Dict) -> Dict[str, Any]:
        """Create a plan to verify the improvements."""
        return {
            "test_cases": [
                "Edge case: minimum input",
                "Edge case: maximum input",
                "Edge case: boundary conditions",
                "Random test: medium input",
                "Stress test: large input"
            ],
            "verification_steps": [
                "Compile the improved code",
                "Run provided test cases",
                "Test with edge cases",
                "Compare with expected outputs",
                "Measure performance",
                "Verify memory usage"
            ],
            "success_criteria": [
                "All test cases pass",
                "Time complexity improved",
                "Memory usage within limits",
                "No runtime errors",
                "Correct output for all cases"
            ]
        }
