import re
from typing import Dict, List, Any


class CodeReviewCrew:
    def __init__(self):
        pass

    def run(self, query: str, code: str = None):
        # Extract code from query if not provided
        if code is None:
            code = self.extract_code(query)
        
        language = self.detect_language(code or query)
        if not self.has_code(code):
            return {
                "status": "need_code",
                "language": language,
                "message": "Please paste your C++ code so I can find the TLE bottleneck and optimize it.",
                "code_quality_score": None,
                "time_complexity": "Not available until code is provided",
                "memory_complexity": "Not available until code is provided",
                "potential_bugs": [],
                "security_issues": [],
                "optimization_suggestions": [],
                "crew_steps": [
                    {"thought": "Code Review Agent: code input validation", "output": "No reviewable code found"},
                    {"thought": "Language Detector: infer requested language from query", "output": language},
                ],
                "reviewed_code": "",
            }
        
        # Perform analysis
        code_quality_score = self.calculate_code_quality_score(code, language)
        time_complexity = self.analyze_time_complexity(code, language)
        memory_complexity = self.analyze_memory_complexity(code, language)
        potential_bugs = self.detect_potential_bugs(code, language)
        security_issues = self.detect_security_issues(code, language)
        optimization_suggestions = self.suggest_optimizations(code, language)
        
        crew_steps = [
            {"thought": "Code Review Agent: analyzing code structure and patterns", "output": "Structure analysis complete"},
            {"thought": "Complexity Analyzer: calculating time and space complexity", "output": f"Time: {time_complexity}, Memory: {memory_complexity}"},
            {"thought": "Bug Detector: scanning for common bugs and issues", "output": f"Found {len(potential_bugs)} potential bugs"},
            {"thought": "Security Scanner: checking for security vulnerabilities", "output": f"Found {len(security_issues)} security issues"},
            {"thought": "Optimization Advisor: suggesting performance improvements", "output": f"Generated {len(optimization_suggestions)} suggestions"},
        ]
        
        return {
            "language": language,
            "code_quality_score": code_quality_score,
            "time_complexity": time_complexity,
            "memory_complexity": memory_complexity,
            "potential_bugs": potential_bugs,
            "security_issues": security_issues,
            "optimization_suggestions": optimization_suggestions,
            "crew_steps": crew_steps,
            "reviewed_code": code,
        }

    @staticmethod
    def extract_code(query: str) -> str:
        """Extract code block from query if present."""
        code_pattern = r'```(?:python|cpp|c\+\+|java|javascript|js)?\n([\s\S]*?)```'
        match = re.search(code_pattern, query)
        if match:
            return match.group(1).strip()
        
        # If no code block, check if the entire query is code-like
        lines = query.strip().split('\n')
        if len(lines) > 1 and any(line.strip().startswith(('def ', 'class ', 'int ', 'void ', 'function ', 'import ', '#include')) for line in lines):
            return query.strip()
        
        return ""

    @staticmethod
    def detect_language(code_or_query: str) -> str:
        """Detect the programming language from code."""
        text = code_or_query.lower()
        
        if 'def ' in text and 'import ' in text:
            return "python"
        if '#include' in text or 'int main' in text or 'std::' in text or 'c++' in text or 'cpp' in text:
            return "cpp"
        if 'public class' in text or 'System.out' in text:
            return "java"
        if 'function ' in text or 'const ' in text and 'let ' in text:
            return "javascript"
        
        return "python"  # Default

    @staticmethod
    def has_code(text: str) -> bool:
        code_keywords = ["#include", "int main", "for", "while", "vector", "cin", "cout"]
        return any(keyword in (text or "") for keyword in code_keywords)

    def calculate_code_quality_score(self, code: str, language: str) -> Dict[str, Any]:
        """Calculate overall code quality score based on various metrics."""
        if not code:
            return {"overall": 0, "readability": 0, "maintainability": 0, "documentation": 0}
        
        readability = self.score_readability(code, language)
        maintainability = self.score_maintainability(code, language)
        documentation = self.score_documentation(code, language)
        
        overall = int((readability + maintainability + documentation) / 3)
        
        return {
            "overall": overall,
            "readability": readability,
            "maintainability": maintainability,
            "documentation": documentation,
        }

    def score_readability(self, code: str, language: str) -> int:
        """Score code readability (0-100)."""
        score = 100
        
        # Check for proper indentation
        lines = code.split('\n')
        inconsistent_indent = False
        prev_indent = None
        for line in lines:
            if line.strip():
                current_indent = len(line) - len(line.lstrip())
                if prev_indent is not None and current_indent % 4 != 0:
                    inconsistent_indent = True
                prev_indent = current_indent
        
        if inconsistent_indent:
            score -= 15
        
        # Check for line length
        long_lines = sum(1 for line in lines if len(line) > 100)
        if long_lines > len(lines) * 0.1:
            score -= 10
        
        # Check for meaningful variable names
        short_vars = len(re.findall(r'\b[a-z]\b', code))
        if short_vars > 3:
            score -= 10
        
        # Check for comments
        comment_ratio = len(re.findall(r'#|//|/\*', code)) / max(len(lines), 1)
        if comment_ratio < 0.05:
            score -= 10
        
        return max(0, min(100, score))

    def score_maintainability(self, code: str, language: str) -> int:
        """Score code maintainability (0-100)."""
        score = 100
        
        # Check function length
        if language == "python":
            func_pattern = r'def\s+\w+\([^)]*\):'
        else:
            func_pattern = r'(?:\w+\s+)+\w+\s*\([^)]*\)\s*\{'
        
        functions = re.finditer(func_pattern, code)
        for func in functions:
            func_start = func.start()
            func_code = code[func_start:]
            lines = func_code.split('\n')[:50]
            func_lines = 0
            indent_level = len(lines[0]) - len(lines[0].lstrip()) if lines else 0
            
            for line in lines[1:]:
                if line.strip() and len(line) - len(line.lstrip()) <= indent_level:
                    break
                func_lines += 1
            
            if func_lines > 50:
                score -= 15
        
        # Check for code duplication
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        unique_lines = set(lines)
        if len(unique_lines) < len(lines) * 0.7:
            score -= 10
        
        # Check for magic numbers
        magic_numbers = len(re.findall(r'\b\d{2,}\b', code))
        if magic_numbers > 5:
            score -= 10
        
        return max(0, min(100, score))

    def score_documentation(self, code: str, language: str) -> int:
        """Score code documentation (0-100)."""
        if not code:
            return 0
        
        score = 100
        
        # Check for docstrings/comments
        has_docstring = bool(re.search(r'""".*?"""|\'\'\'.*?\'\'\'', code, re.DOTALL))
        has_comments = bool(re.search(r'#.*|//.*|/\*.*?\*/', code, re.DOTALL))
        
        if not has_docstring:
            score -= 30
        if not has_comments:
            score -= 20
        
        # Check for function/class documentation
        if language == "python":
            functions = len(re.findall(r'def\s+\w+', code))
            documented_funcs = len(re.findall(r'def\s+\w+[^:]*:\s*"""', code))
            if functions > 0 and documented_funcs / functions < 0.5:
                score -= 20
        
        return max(0, min(100, score))

    def analyze_time_complexity(self, code: str, language: str) -> str:
        """Analyze and estimate time complexity."""
        if not code:
            return "Unknown"
        
        code_lower = code.lower()
        
        # Check for nested loops by approximate max depth instead of total loop
        # count. A setup loop plus a nested pair should be O(n^2), not O(n^3).
        nested_loops = self.max_loop_depth(code, language)
        if nested_loops >= 3:
            return "O(n³) or higher"
        elif nested_loops == 2:
            return "O(n²)"
        elif nested_loops == 1:
            return "O(n)"
        
        # Check for recursion
        if 'def ' in code_lower and code_lower.count('return ') > 2:
            return "O(n) or O(log n) depending on implementation"
        
        # Check for hash map/dictionary operations
        if 'dict' in code_lower or 'hashmap' in code_lower or 'unordered_map' in code_lower:
            return "O(n) on average"
        
        # Check for sorting
        if 'sort' in code_lower or 'sorted' in code_lower:
            return "O(n log n)"
        
        # Check for binary search patterns
        if 'binary' in code_lower or ('mid' in code_lower and 'left' in code_lower and 'right' in code_lower):
            return "O(log n)"
        
        return "O(1) or O(n)"

    @staticmethod
    def max_loop_depth(code: str, language: str) -> int:
        max_depth = 0
        if language == "cpp":
            depth = 0
            loop_stack = []
            pending_loop = False
            for line in code.splitlines():
                stripped = line.strip()
                if re.search(r'\b(for|while)\s*\(', stripped):
                    pending_loop = True
                opens = stripped.count("{")
                closes = stripped.count("}")
                for _ in range(opens):
                    if pending_loop:
                        loop_stack.append(depth)
                        pending_loop = False
                        max_depth = max(max_depth, len(loop_stack))
                    depth += 1
                depth = max(0, depth - closes)
                while loop_stack and loop_stack[-1] >= depth:
                    loop_stack.pop()
            return max_depth

        loop_indents = []
        for line in code.splitlines():
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip())
            loop_indents = [value for value in loop_indents if value < indent]
            if re.search(r'\b(for|while)\b', line):
                loop_indents.append(indent)
                max_depth = max(max_depth, len(loop_indents))
        return max_depth

    def analyze_memory_complexity(self, code: str, language: str) -> str:
        """Analyze and estimate memory complexity."""
        if not code:
            return "Unknown"
        
        code_lower = code.lower()
        
        # Check for large data structures
        if 'array' in code_lower or 'vector' in code_lower or 'list' in code_lower:
            if code_lower.count('[') >= 2:
                return "O(n²)"
            return "O(n)"
        
        # Check for hash maps
        if 'dict' in code_lower or 'hashmap' in code_lower or 'unordered_map' in code_lower:
            return "O(n)"
        
        # Check for recursion (stack space)
        if 'def ' in code_lower and code_lower.count('return ') > 2:
            return "O(n) stack space"
        
        # Check for matrices/2D arrays
        if code_lower.count('[') >= 4 or 'matrix' in code_lower or '2d' in code_lower:
            return "O(n²)"
        
        return "O(1) or O(n)"

    def detect_potential_bugs(self, code: str, language: str) -> List[Dict[str, str]]:
        """Detect potential bugs in the code."""
        bugs = []
        
        if not code:
            return bugs
        
        # Common bug patterns
        bug_patterns = {
            "Off-by-one error": [r'range\(len\([^)]+\)\)', r'\[i\]', r'\[i-1\]'],
            "Uninitialized variable": [r'= \w+$', r'int \w+;'],
            "Null/None check missing": [r'\.\w+\(', r'\['],
            "Resource leak": [r'open\(', r'FILE \*'],
            "Integer overflow": [r'\* \w+', r'\+ \w+'],
            "Infinite loop": [r'while True:', r'while\(1\)'],
            "Missing return": [r'def \w+\([^)]*\):'],
        }
        
        for bug_type, patterns in bug_patterns.items():
            for pattern in patterns:
                if re.search(pattern, code, re.MULTILINE):
                    bugs.append({
                        "type": bug_type,
                        "severity": "medium",
                        "description": f"Potential {bug_type} detected",
                        "suggestion": f"Review code for {bug_type.lower()}"
                    })
        
        # Language-specific bugs
        if language == "python":
            if 'except:' in code:
                bugs.append({
                    "type": "Broad exception handling",
                    "severity": "high",
                    "description": "Bare except clause catches all exceptions",
                    "suggestion": "Specify exception types (e.g., except ValueError)"
                })
            if '==' in code and 'None' in code:
                bugs.append({
                    "type": "None comparison",
                    "severity": "low",
                    "description": "Using == for None comparison",
                    "suggestion": "Use 'is None' instead"
                })
        
        elif language == "cpp":
            if 'delete ' in code and not 'delete[]' in code:
                bugs.append({
                    "type": "Memory management",
                    "severity": "high",
                    "description": "Potential memory leak with delete vs delete[]",
                    "suggestion": "Use delete[] for arrays, delete for single objects"
                })
            if 'scanf' in code or 'gets' in code:
                bugs.append({
                    "type": "Unsafe function",
                    "severity": "high",
                    "description": "Using unsafe C functions",
                    "suggestion": "Use safer alternatives like std::cin or fgets"
                })
        
        return bugs[:10]

    def detect_security_issues(self, code: str, language: str) -> List[Dict[str, str]]:
        """Detect security vulnerabilities in the code."""
        issues = []
        
        if not code:
            return issues
        
        code_lower = code.lower()
        
        # SQL Injection
        if 'sql' in code_lower and ('"' in code or "'" in code):
            issues.append({
                "type": "SQL Injection",
                "severity": "critical",
                "description": "Potential SQL injection vulnerability",
                "suggestion": "Use parameterized queries or prepared statements"
            })
        
        # Command Injection
        if 'exec' in code_lower or 'eval' in code_lower or 'system(' in code_lower:
            issues.append({
                "type": "Command Injection",
                "severity": "critical",
                "description": "Use of exec/eval/system with user input",
                "suggestion": "Avoid exec/eval/system with untrusted input"
            })
        
        # Hardcoded credentials
        if re.search(r'(password|secret|key|token)\s*=\s*["\']', code_lower):
            issues.append({
                "type": "Hardcoded Credentials",
                "severity": "high",
                "description": "Hardcoded sensitive information detected",
                "suggestion": "Use environment variables or configuration files"
            })
        
        # Weak cryptography
        if 'md5' in code_lower or 'sha1' in code_lower:
            issues.append({
                "type": "Weak Cryptography",
                "severity": "medium",
                "description": "Use of weak hash functions",
                "suggestion": "Use SHA-256 or stronger algorithms"
            })
        
        # Buffer overflow risks (C/C++)
        if language == "cpp":
            if 'strcpy' in code_lower or 'sprintf' in code_lower or 'gets' in code_lower:
                issues.append({
                    "type": "Buffer Overflow",
                    "severity": "critical",
                    "description": "Unsafe string functions",
                    "suggestion": "Use strncpy, snprintf, fgets instead"
                })
        
        return issues[:10]

    def suggest_optimizations(self, code: str, language: str) -> List[Dict[str, str]]:
        """Suggest performance optimizations."""
        suggestions = []
        
        if not code:
            return suggestions
        
        code_lower = code.lower()
        
        # Loop optimizations
        if 'for ' in code_lower and 'range(len(' in code_lower:
            suggestions.append({
                "type": "Loop Optimization",
                "description": "Use enumerate() instead of range(len())",
                "impact": "medium"
            })
        
        # List comprehension
        if language == "python" and code_lower.count('for ') > 2:
            suggestions.append({
                "type": "List Comprehension",
                "description": "Consider using list comprehensions for loops",
                "impact": "medium"
            })
        
        # String concatenation
        if code_lower.count('+') > 3 and 'string' in code_lower or 'str' in code_lower:
            suggestions.append({
                "type": "String Optimization",
                "description": "Use join() for string concatenation in loops",
                "impact": "high"
            })
        
        # Caching
        if code_lower.count('def ') > 1:
            suggestions.append({
                "type": "Memoization",
                "description": "Consider caching expensive function results",
                "impact": "high"
            })
        
        # Data structure choice
        if 'list' in code_lower and 'in ' in code_lower:
            suggestions.append({
                "type": "Data Structure",
                "description": "Use set/dict for O(1) lookups instead of list",
                "impact": "high"
            })
        
        return suggestions[:10]
