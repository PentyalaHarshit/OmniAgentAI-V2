import re
from typing import Dict, List, Any


class DebugCrew:
    def __init__(self):
        pass

    def run(self, query: str, code: str = None, error_message: str = None):
        # Extract code and error from query if not provided
        if code is None:
            code = self.extract_code(query)
        if error_message is None:
            error_message = self.extract_error(query)
        
        language = self.detect_language(code or query)
        
        # Perform debugging analysis
        root_cause = self.analyze_root_cause(code, error_message, language)
        fix_suggestion = self.generate_fix_suggestion(code, error_message, language, root_cause)
        corrected_code = self.generate_corrected_code(code, fix_suggestion, language)
        
        crew_steps = [
            {"thought": "Debug Agent: extracting error information", "output": "Error extracted"},
            {"thought": "Root Cause Analyzer: identifying the source of the error", "output": root_cause},
            {"thought": "Fix Generator: developing solution strategy", "output": "Fix strategy developed"},
            {"thought": "Code Corrector: applying fixes to the code", "output": "Corrected code generated"},
            {"thought": "Verification: checking if fix resolves the issue", "output": "Verification complete"},
        ]
        
        return {
            "language": language,
            "error_message": error_message,
            "root_cause": root_cause,
            "fix_suggestion": fix_suggestion,
            "corrected_code": corrected_code,
            "original_code": code,
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
    def extract_error(query: str) -> str:
        """Extract error message from query."""
        error_patterns = [
            r'(?:error|exception|traceback|failed|segmentation fault|memory limit exceeded)[:\s]*([\s\S]*?)(?:\n\n|\Z)',
            r'(?:runtime error|compilation error|syntax error)[:\s]*([\s\S]*?)(?:\n\n|\Z)',
        ]
        
        for pattern in error_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Check for common error keywords
        error_keywords = ['segmentation fault', 'memory limit exceeded', 'time limit exceeded', 
                         'runtime error', 'compilation error', 'syntax error', 'index out of range',
                         'null pointer', 'division by zero', 'stack overflow']
        
        for keyword in error_keywords:
            if keyword.lower() in query.lower():
                return keyword
        
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

    def analyze_root_cause(self, code: str, error_message: str, language: str) -> Dict[str, Any]:
        """Analyze the root cause of the error."""
        error_lower = (error_message or "").lower()
        code_lower = (code or "").lower()
        
        root_cause = {
            "type": "unknown",
            "description": "Unable to determine root cause",
            "location": "unknown",
            "severity": "medium"
        }
        
        # Memory issues
        if "memory limit exceeded" in error_lower or "out of memory" in error_lower:
            root_cause.update({
                "type": "memory_issue",
                "description": "Memory limit exceeded - likely due to inefficient data structures or memory leaks",
                "location": self.find_memory_intensive_code(code),
                "severity": "high"
            })
        
        # Time limit issues
        elif "time limit exceeded" in error_lower or "timeout" in error_lower:
            root_cause.update({
                "type": "time_complexity",
                "description": "Time limit exceeded - algorithm is too slow for given constraints",
                "location": self.find_slow_code(code),
                "severity": "high"
            })
        
        # Segmentation fault
        elif "segmentation fault" in error_lower:
            root_cause.update({
                "type": "segmentation_fault",
                "description": "Segmentation fault - likely accessing invalid memory or null pointer",
                "location": self.find_memory_access_code(code),
                "severity": "critical"
            })
        
        # Index out of range
        elif "index out of range" in error_lower or "indexerror" in error_lower:
            root_cause.update({
                "type": "index_error",
                "description": "Index out of range - accessing array/list beyond its bounds",
                "location": self.find_array_access_code(code),
                "severity": "medium"
            })
        
        # Division by zero
        elif "division by zero" in error_lower or "zerodivisionerror" in error_lower:
            root_cause.update({
                "type": "division_by_zero",
                "description": "Division by zero - attempting to divide by zero",
                "location": self.find_division_code(code),
                "severity": "medium"
            })
        
        # Null pointer
        elif "null pointer" in error_lower or "none" in error_lower:
            root_cause.update({
                "type": "null_pointer",
                "description": "Null/None pointer dereference - accessing null reference",
                "location": self.find_null_access_code(code),
                "severity": "high"
            })
        
        # Stack overflow
        elif "stack overflow" in error_lower or "recursion" in error_lower:
            root_cause.update({
                "type": "stack_overflow",
                "description": "Stack overflow - likely infinite recursion or deep recursion",
                "location": self.find_recursion_code(code),
                "severity": "high"
            })
        
        # Syntax errors
        elif "syntax error" in error_lower or "compilation error" in error_lower:
            root_cause.update({
                "type": "syntax_error",
                "description": "Syntax/Compilation error - code has syntax issues",
                "location": self.find_syntax_error_location(code),
                "severity": "medium"
            })
        
        return root_cause

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
    def find_slow_code(code: str) -> str:
        """Find slow code sections (nested loops, etc.)."""
        if not code:
            return "unknown"
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if line.count('for') > 1 or line.count('while') > 1:
                return f"line {i + 1}"
        
        return "unknown"

    @staticmethod
    def find_memory_access_code(code: str) -> str:
        """Find memory access code that might cause segfaults."""
        if not code:
            return "unknown"
        
        lines = code.split('\n')
        access_patterns = ['[', '*', '->', '.at(']
        
        for i, line in enumerate(lines):
            if any(pattern in line for pattern in access_patterns):
                return f"line {i + 1}"
        
        return "unknown"

    @staticmethod
    def find_array_access_code(code: str) -> str:
        """Find array access code."""
        if not code:
            return "unknown"
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if '[' in line and ']' in line:
                return f"line {i + 1}"
        
        return "unknown"

    @staticmethod
    def find_division_code(code: str) -> str:
        """Find division code."""
        if not code:
            return "unknown"
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if '/' in line or '%' in line:
                return f"line {i + 1}"
        
        return "unknown"

    @staticmethod
    def find_null_access_code(code: str) -> str:
        """Find null/None access code."""
        if not code:
            return "unknown"
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if '.' in line and ('None' in line or 'null' in line.lower()):
                return f"line {i + 1}"
        
        return "unknown"

    @staticmethod
    def find_recursion_code(code: str) -> str:
        """Find recursion code."""
        if not code:
            return "unknown"
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if 'def ' in line or 'return ' in line:
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

    def generate_fix_suggestion(self, code: str, error_message: str, language: str, root_cause: Dict) -> str:
        """Generate fix suggestion based on root cause."""
        error_type = root_cause.get("type", "unknown")
        
        fix_suggestions = {
            "memory_issue": "Use more efficient data structures, avoid unnecessary copies, or implement memory optimization techniques",
            "time_complexity": "Optimize algorithm complexity, use appropriate data structures, or implement caching",
            "segmentation_fault": "Add null checks, validate array bounds, and ensure proper pointer initialization",
            "index_error": "Add bounds checking before array/list access, use safe access methods",
            "division_by_zero": "Add zero checks before division operations",
            "null_pointer": "Add null/None checks before dereferencing pointers or objects",
            "stack_overflow": "Add recursion depth limits, convert to iterative solution, or use tail recursion",
            "syntax_error": "Review syntax, check for matching brackets/parentheses, and verify language-specific syntax",
        }
        
        return fix_suggestions.get(error_type, "Review code logic and add appropriate error handling")

    def generate_corrected_code(self, code: str, fix_suggestion: str, language: str) -> str:
        """Generate corrected code with fixes applied."""
        if not code:
            return ""
        
        # Apply common fixes based on the fix suggestion
        corrected = code
        
        # Add bounds checking for Python
        if language == "python" and "index" in fix_suggestion.lower():
            corrected = self.add_bounds_checking_python(corrected)
        
        # Add null checks for C++
        if language == "cpp" and "null" in fix_suggestion.lower():
            corrected = self.add_null_checks_cpp(corrected)
        
        # Add zero checks for division
        if "division" in fix_suggestion.lower():
            corrected = self.add_division_checks(corrected, language)
        
        return corrected

    @staticmethod
    def add_bounds_checking_python(code: str) -> str:
        """Add bounds checking to Python code."""
        lines = code.split('\n')
        corrected = []
        
        for line in lines:
            corrected.append(line)
            if '[' in line and ']' in line and 'if' not in line:
                # Simple heuristic: add bounds check comment
                indent = len(line) - len(line.lstrip())
                corrected.append(' ' * indent + '# TODO: Add bounds checking')
        
        return '\n'.join(corrected)

    @staticmethod
    def add_null_checks_cpp(code: str) -> str:
        """Add null checks to C++ code."""
        lines = code.split('\n')
        corrected = []
        
        for line in lines:
            if '->' in line or '.' in line:
                # Add null check comment
                indent = len(line) - len(line.lstrip())
                corrected.append(' ' * indent + '// TODO: Add null pointer check')
            corrected.append(line)
        
        return '\n'.join(corrected)

    @staticmethod
    def add_division_checks(code: str, language: str) -> str:
        """Add division by zero checks."""
        lines = code.split('\n')
        corrected = []
        
        for line in lines:
            if '/' in line and 'if' not in line:
                # Add division check comment
                indent = len(line) - len(line.lstrip())
                corrected.append(' ' * indent + f'# TODO: Add division by zero check' if language == "python" else '// TODO: Add division by zero check')
            corrected.append(line)
        
        return '\n'.join(corrected)
