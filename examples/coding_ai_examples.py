"""
Example usage of the Coding & AI Agent Architecture

This file demonstrates how to use the new coding and AI agents
that have been added to OmniAgentAI.
"""

from agents.coding_ai_agent import CodingAIAgent
from agents.code_review_agent import CodeReviewAgent
from agents.debug_agent import DebugAgent
from agents.test_case_agent import TestCaseAgent
from agents.algorithm_agent import AlgorithmAgent
from agents.system_design_agent import SystemDesignAgent
from agents.ml_agent import MLAgent
from agents.rag_agent import RAGAgent
from agents.ai_architect_agent import AIArchitectAgent


def example_coding_ai_parent():
    """Example using the parent CodingAIAgent router."""
    print("=== CodingAIAgent (Parent Router) ===\n")
    
    agent = CodingAIAgent()
    
    # The parent agent automatically routes to the appropriate sub-agent
    queries = [
        "Review this code for security issues",
        "Fix this segmentation fault",
        "Generate edge cases for segment tree",
        "Solve range query problem",
        "Design YouTube architecture",
        "Train house price prediction model",
        "Build multi-document RAG system",
        "Design Agentic RAG platform",
    ]
    
    for query in queries:
        print(f"Query: {query}")
        result = agent.run(query)
        print(f"Routed to: {result.get('router', {}).get('selected_leaf_agent', 'Unknown')}")
        print("-" * 50 + "\n")


def example_code_review():
    """Example using CodeReviewAgent directly."""
    print("=== CodeReviewAgent ===\n")
    
    agent = CodeReviewAgent()
    
    code = """
def calculate_sum(numbers):
    total = 0
    for i in range(len(numbers)):
        total = total + numbers[i]
    return total
"""
    
    query = "Review this code for optimization and security"
    result = agent.run(query, code=code)
    
    print(f"Language: {result['crew_result']['language']}")
    print(f"Code Quality Score: {result['crew_result']['code_quality_score']['overall']}/100")
    print(f"Time Complexity: {result['crew_result']['time_complexity']}")
    print(f"Memory Complexity: {result['crew_result']['memory_complexity']}")
    print(f"Potential Bugs: {len(result['crew_result']['potential_bugs'])}")
    print(f"Security Issues: {len(result['crew_result']['security_issues'])}")
    print(f"Optimization Suggestions: {len(result['crew_result']['optimization_suggestions'])}")


def example_debug():
    """Example using DebugAgent directly."""
    print("\n=== DebugAgent ===\n")
    
    agent = DebugAgent()
    
    code = """
def process_data(data):
    result = []
    for i in range(len(data)):
        result.append(data[i] * 2)
    return result[100]  # Potential index error
"""
    
    error_message = "IndexError: list index out of range"
    query = "Fix this error"
    
    result = agent.run(query, code=code, error_message=error_message)
    
    print(f"Root Cause: {result['crew_result']['failure_analysis']['root_cause']}")
    print(f"Failure Type: {result['crew_result']['failure_analysis']['failure_type']}")
    print(f"Fix Strategy: {result['crew_result']['improvement_strategy']['strategy']}")


def example_test_case():
    """Example using TestCaseAgent directly."""
    print("\n=== TestCaseAgent ===\n")
    
    agent = TestCaseAgent()
    
    query = "Generate edge cases for segment tree"
    result = agent.run(query)
    
    print(f"Algorithm Type: {result['crew_result']['algorithm_type']}")
    print(f"Edge Cases: {len(result['crew_result']['edge_cases'])}")
    print(f"Stress Tests: {len(result['crew_result']['stress_tests'])}")
    
    for case in result['crew_result']['edge_cases'][:3]:
        print(f"  - {case['name']}: {case['description']}")


def example_algorithm():
    """Example using AlgorithmAgent directly."""
    print("\n=== AlgorithmAgent ===\n")
    
    agent = AlgorithmAgent()
    
    query = "Solve range query problem with updates"
    result = agent.run(query)
    
    print(f"Problem Type: {result['crew_result']['problem_type']}")
    print(f"Best Algorithm: {result['crew_result']['best_algorithm']['name']}")
    print(f"Score: {result['crew_result']['best_algorithm']['score']}/100")
    print(f"Time Complexity: {result['crew_result']['best_algorithm']['time_complexity']}")
    
    print("\nTop 3 Algorithms:")
    for i, algo in enumerate(result['crew_result']['ranked_algorithms'][:3], 1):
        print(f"  {i}. {algo['name']} ({algo['score']}/100)")


def example_system_design():
    """Example using SystemDesignAgent directly."""
    print("\n=== SystemDesignAgent ===\n")
    
    agent = SystemDesignAgent()
    
    query = "Design YouTube architecture for billions of users"
    result = agent.run(query)
    
    print(f"System Type: {result['crew_result']['system_type']}")
    print(f"Architecture Pattern: {result['crew_result']['architecture']['pattern']}")
    print(f"Primary Database: {result['crew_result']['database_design']['primary']}")
    print(f"Scaling Strategy: {result['crew_result']['scaling_strategy']['strategy']}")


def example_ml():
    """Example using MLAgent directly."""
    print("\n=== MLAgent ===\n")
    
    agent = MLAgent()
    
    query = "Train house price prediction model"
    result = agent.run(query)
    
    print(f"Task Type: {result['crew_result']['task_type']}")
    print(f"Data Type: {result['crew_result']['data_type']}")
    print(f"Recommended Model: {result['crew_result']['model_selection']['model']}")
    print(f"Evaluation Metrics: {', '.join(result['crew_result']['evaluation_metrics'][:3])}")


def example_rag():
    """Example using RAGAgent directly."""
    print("\n=== RAGAgent ===\n")
    
    agent = RAGAgent()
    
    query = "Build multi-document RAG system for millions of documents"
    result = agent.run(query)
    
    print(f"RAG Type: {result['crew_result']['rag_type']}")
    print(f"Document Type: {result['crew_result']['document_type']}")
    print(f"Chunking Method: {result['crew_result']['chunking_strategy']['method']}")
    print(f"Vector Database: {result['crew_result']['vector_database']['database']}")
    print(f"Embedding Model: {result['crew_result']['embedding_model']['model']}")


def example_ai_architect():
    """Example using AIArchitectAgent directly."""
    print("\n=== AIArchitectAgent ===\n")
    
    agent = AIArchitectAgent()
    
    query = "Design autonomous agentic RAG platform"
    result = agent.run(query)
    
    print(f"System Type: {result['crew_result']['system_type']}")
    print(f"Complexity Level: {result['crew_result']['complexity']['level']}")
    print(f"Router Purpose: {result['crew_result']['router_agent']['purpose']}")
    print(f"Memory Architecture: {result['crew_result']['memory_system']['architecture']}")
    print(f"RAG Purpose: {result['crew_result']['rag_system']['purpose']}")
    print(f"Verification Layers: {len(result['crew_result']['verification']['layers'])}")


if __name__ == "__main__":
    print("Coding & AI Agent Architecture - Usage Examples\n")
    print("=" * 60 + "\n")
    
    # Run all examples
    example_coding_ai_parent()
    example_code_review()
    example_debug()
    example_test_case()
    example_algorithm()
    example_system_design()
    example_ml()
    example_rag()
    example_ai_architect()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
