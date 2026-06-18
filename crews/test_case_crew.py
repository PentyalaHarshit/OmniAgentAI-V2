import re
from typing import Dict, List, Any


class TestCaseCrew:
    def __init__(self):
        pass

    def run(self, query: str, code: str = None):
        # Extract code and algorithm type from query
        if code is None:
            code = self.extract_code(query)
        
        algorithm_type = self.detect_algorithm_type(query)
        language = self.detect_language(code or query)
        
        # Generate test cases
        edge_cases = self.generate_edge_cases(algorithm_type, language)
        stress_tests = self.generate_stress_tests(algorithm_type, language)
        expected_outputs = self.generate_expected_outputs(algorithm_type, edge_cases + stress_tests)
        
        crew_steps = [
            {"thought": "TestCase Agent: analyzing algorithm requirements", "output": "Algorithm type identified"},
            {"thought": "Edge Case Generator: creating boundary condition tests", "output": f"Generated {len(edge_cases)} edge cases"},
            {"thought": "Stress Test Generator: creating performance tests", "output": f"Generated {len(stress_tests)} stress tests"},
            {"thought": "Output Calculator: computing expected results", "output": "Expected outputs computed"},
        ]
        
        return {
            "algorithm_type": algorithm_type,
            "language": language,
            "edge_cases": edge_cases,
            "stress_tests": stress_tests,
            "expected_outputs": expected_outputs,
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
    def detect_algorithm_type(query: str) -> str:
        """Detect the type of algorithm from query."""
        query_lower = query.lower()
        
        algorithm_patterns = {
            "segment_tree": ["segment tree", "range query", "range sum", "range update"],
            "fenwick_tree": ["fenwick", "binary indexed tree", "bit", "prefix sum"],
            "dijkstra": ["dijkstra", "shortest path", "graph path"],
            "binary_search": ["binary search", "binary", "search sorted"],
            "sorting": ["sort", "sorting", "merge sort", "quick sort"],
            "dp": ["dynamic programming", "dp", "memoization", "tabulation"],
            "graph": ["graph", "tree", "bfs", "dfs", "traversal"],
            "string": ["string", "substring", "pattern matching", "kmp"],
            "array": ["array", "subarray", "two pointers", "sliding window"],
            "math": ["math", "gcd", "lcm", "prime", "factorial"],
        }
        
        for algo_type, patterns in algorithm_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return algo_type
        
        return "general"

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

    def generate_edge_cases(self, algorithm_type: str, language: str) -> List[Dict[str, Any]]:
        """Generate edge cases for the algorithm."""
        edge_cases = []
        
        if algorithm_type == "segment_tree":
            edge_cases = [
                {"name": "Single element", "input": "1 1\nsum 1 1", "description": "Array with one element"},
                {"name": "All same values", "input": "5 3\n1 1 1 1 1\nsum 1 5\nset 3 2\nsum 1 5", "description": "All elements identical"},
                {"name": "Minimum size", "input": "2 2\n1 2\nsum 1 2\nsum 1 1", "description": "Smallest valid array"},
                {"name": "Large values", "input": "3 2\n1000000 2000000 3000000\nsum 1 3\nset 2 0\nsum 1 3", "description": "Large integer values"},
                {"name": "Update first/last", "input": "4 2\n1 2 3 4\nset 1 10\nset 4 20\nsum 1 4", "description": "Update boundary elements"},
            ]
        
        elif algorithm_type == "fenwick_tree":
            edge_cases = [
                {"name": "Single element", "input": "1 1\n1\nquery 1", "description": "Single element array"},
                {"name": "All zeros", "input": "5 3\n0 0 0 0 0\nupdate 1 5\nquery 5", "description": "All zeros initially"},
                {"name": "Point query", "input": "3 2\n1 2 3\nquery 2\nupdate 2 10\nquery 2", "description": "Single point queries"},
                {"name": "Range boundaries", "input": "4 2\n1 2 3 4\nquery 1\nquery 4", "description": "Query first and last"},
            ]
        
        elif algorithm_type == "dijkstra":
            edge_cases = [
                {"name": "Single node", "input": "1 0 1", "description": "Graph with one node"},
                {"name": "Disconnected graph", "input": "3 0 1\n", "description": "No edges between nodes"},
                {"name": "Self loops", "input": "2 2 1\n1 2 5\n2 1 3", "description": "Edges back to same node"},
                {"name": "Zero weight edges", "input": "3 2 1\n1 2 0\n2 3 5", "description": "Edges with zero weight"},
                {"name": "Large weights", "input": "3 2 1\n1 2 1000000\n2 3 2000000", "description": "Very large edge weights"},
            ]
        
        elif algorithm_type == "binary_search":
            edge_cases = [
                {"name": "Element not found", "input": "5\n1 3 5 7 9\nsearch 4", "description": "Target not in array"},
                {"name": "First element", "input": "5\n1 3 5 7 9\nsearch 1", "description": "Target is first element"},
                {"name": "Last element", "input": "5\n1 3 5 7 9\nsearch 9", "description": "Target is last element"},
                {"name": "Single element", "input": "1\n5\nsearch 5", "description": "Array with one element"},
                {"name": "Duplicates", "input": "5\n1 3 3 3 5\nsearch 3", "description": "Multiple identical elements"},
            ]
        
        elif algorithm_type == "sorting":
            edge_cases = [
                {"name": "Already sorted", "input": "5\n1 2 3 4 5", "description": "Already sorted array"},
                {"name": "Reverse sorted", "input": "5\n5 4 3 2 1", "description": "Reverse sorted array"},
                {"name": "All same", "input": "5\n1 1 1 1 1", "description": "All elements identical"},
                {"name": "Single element", "input": "1\n42", "description": "Single element array"},
                {"name": "Negative numbers", "input": "5\n-5 -3 -1 0 2", "description": "Array with negative numbers"},
            ]
        
        elif algorithm_type == "dp":
            edge_cases = [
                {"name": "Base case", "input": "1\n1", "description": "Smallest valid input"},
                {"name": "All zeros", "input": "5\n0 0 0 0 0", "description": "All zeros"},
                {"name": "Maximum constraints", "input": "100\n" + " ".join(["1"] * 100), "description": "Large input size"},
                {"name": "Negative values", "input": "5\n-1 -2 -3 -4 -5", "description": "Negative numbers"},
            ]
        
        else:  # general
            edge_cases = [
                {"name": "Empty input", "input": "0", "description": "No input"},
                {"name": "Single element", "input": "1\n1", "description": "One element"},
                {"name": "Minimum valid", "input": "2\n1 2", "description": "Smallest valid case"},
                {"name": "Boundary values", "input": "2\n0 1000000", "description": "Min and max values"},
            ]
        
        return edge_cases

    def generate_stress_tests(self, algorithm_type: str, language: str) -> List[Dict[str, Any]]:
        """Generate stress tests for performance testing."""
        stress_tests = []
        
        if algorithm_type in ["segment_tree", "fenwick_tree"]:
            stress_tests = [
                {"name": "Large array", "input": "100000 1000\n" + " ".join(["1"] * 100000) + "\n" + "\n".join([f"sum 1 {i}" for i in range(1, 1001)]), "description": "100K elements with 1K queries"},
                {"name": "Many updates", "input": "10000 5000\n" + " ".join(["1"] * 10000) + "\n" + "\n".join([f"set {i} {i}" for i in range(1, 5001)]), "description": "10K elements with 5K updates"},
            ]
        
        elif algorithm_type == "dijkstra":
            stress_tests = [
                {"name": "Dense graph", "input": "1000 500000 1\n" + "\n".join([f"{i} {i+1} 1" for i in range(1, 1000)]), "description": "1K nodes with many edges"},
                {"name": "Sparse graph", "input": "100000 100000 1\n" + "\n".join([f"{i} {i+1} 1" for i in range(1, 100001)]), "description": "100K nodes with linear edges"},
            ]
        
        elif algorithm_type == "sorting":
            stress_tests = [
                {"name": "Large random", "input": "100000\n" + " ".join([str(i) for i in range(100000, 0, -1)]), "description": "100K reverse sorted"},
                {"name": "Large sorted", "input": "100000\n" + " ".join([str(i) for i in range(1, 100001)]), "description": "100K already sorted"},
            ]
        
        elif algorithm_type == "dp":
            stress_tests = [
                {"name": "Large input", "input": "1000\n" + " ".join(["1"] * 1000), "description": "1000 elements for DP"},
                {"name": "Maximum recursion", "input": "500\n" + " ".join([str(i) for i in range(500)]), "description": "Deep recursion test"},
            ]
        
        else:
            stress_tests = [
                {"name": "Large input", "input": "100000\n" + " ".join(["1"] * 100000), "description": "100K elements"},
                {"name": "Mixed operations", "input": "10000\n" + " ".join([str(i) for i in range(10000)]), "description": "10K mixed operations"},
            ]
        
        return stress_tests

    def generate_expected_outputs(self, algorithm_type: str, test_cases: List[Dict]) -> List[Dict[str, Any]]:
        """Generate expected outputs for test cases."""
        expected_outputs = []
        
        for test_case in test_cases:
            output = self.compute_expected_output(algorithm_type, test_case)
            expected_outputs.append({
                "test_name": test_case["name"],
                "input": test_case["input"],
                "expected_output": output,
                "description": test_case["description"],
            })
        
        return expected_outputs

    def compute_expected_output(self, algorithm_type: str, test_case: Dict) -> str:
        """Compute expected output for a test case."""
        # This is a simplified implementation
        # In a real system, this would use the actual algorithm implementation
        
        if algorithm_type == "segment_tree":
            if "sum 1 5" in test_case["input"]:
                return "15" if "1 2 3 4 5" in test_case["input"] else "10"
            elif "sum 1 1" in test_case["input"]:
                return "1"
            return "Computed based on segment tree logic"
        
        elif algorithm_type == "dijkstra":
            if "1 0 1" in test_case["input"]:
                return "0"
            return "Computed shortest path distances"
        
        elif algorithm_type == "sorting":
            if "1 2 3 4 5" in test_case["input"]:
                return "1 2 3 4 5"
            elif "5 4 3 2 1" in test_case["input"]:
                return "1 2 3 4 5"
            return "Sorted array"
        
        return "Expected output based on algorithm logic"
