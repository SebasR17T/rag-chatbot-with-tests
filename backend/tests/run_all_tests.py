"""Main test runner for RAG system tests"""

import unittest
import sys
import os
from io import StringIO

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import all test modules
from test_course_search_tool import TestCourseSearchTool, TestCourseSearchToolEdgeCases
from test_ai_generator_integration import (
    TestAIGeneratorToolIntegration, 
    TestToolCallErrorHandling,
    TestAIGeneratorSystemPrompt
)
from test_rag_system import (
    TestRAGSystemContentQueries,
    TestRAGSystemDocumentProcessing, 
    TestRAGSystemComponentInitialization
)

class TestResults:
    """Helper class to aggregate and display test results"""
    
    def __init__(self):
        self.total_tests = 0
        self.total_failures = 0
        self.total_errors = 0
        self.results_by_category = {}
    
    def add_result(self, category, result):
        """Add test result for a category"""
        self.total_tests += result.testsRun
        self.total_failures += len(result.failures)
        self.total_errors += len(result.errors)
        
        self.results_by_category[category] = {
            'tests': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'failure_details': result.failures,
            'error_details': result.errors
        }
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("=" * 80)
        print("RAG SYSTEM TEST RESULTS SUMMARY")
        print("=" * 80)
        
        # Overall summary
        print(f"\nOVERALL RESULTS:")
        print(f"Total Tests Run: {self.total_tests}")
        print(f"Total Failures: {self.total_failures}")
        print(f"Total Errors: {self.total_errors}")
        success_rate = ((self.total_tests - self.total_failures - self.total_errors) / self.total_tests) * 100 if self.total_tests > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Category breakdown
        print(f"\nRESULTS BY CATEGORY:")
        for category, results in self.results_by_category.items():
            print(f"\n{category}:")
            print(f"  Tests: {results['tests']}")
            print(f"  Failures: {results['failures']}")
            print(f"  Errors: {results['errors']}")
            
            if results['failures'] > 0:
                print(f"  Failure Details:")
                for test, traceback in results['failure_details']:
                    print(f"    - {test}")
                    # Print first few lines of traceback
                    lines = traceback.split('\n')[:3]
                    for line in lines:
                        if line.strip():
                            print(f"      {line.strip()}")
            
            if results['errors'] > 0:
                print(f"  Error Details:")
                for test, traceback in results['error_details']:
                    print(f"    - {test}")
                    # Print first few lines of traceback
                    lines = traceback.split('\n')[:3]
                    for line in lines:
                        if line.strip():
                            print(f"      {line.strip()}")
    
    def get_failing_components(self):
        """Identify which components are failing based on test results"""
        failing_components = []
        
        for category, results in self.results_by_category.items():
            if results['failures'] > 0 or results['errors'] > 0:
                failing_components.append({
                    'component': category,
                    'failures': results['failures'],
                    'errors': results['errors'],
                    'issues': []
                })
                
                # Analyze failure patterns
                for test, traceback in results['failure_details'] + results['error_details']:
                    test_name = str(test).split('.')[-1]
                    failing_components[-1]['issues'].append(test_name)
        
        return failing_components

def run_test_category(category_name, test_classes, verbosity=1):
    """Run tests for a specific category"""
    print(f"\n{'='*60}")
    print(f"RUNNING {category_name.upper()} TESTS")
    print(f"{'='*60}")
    
    # Create test suite using TestLoader (makeSuite is deprecated)
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for test_class in test_classes:
        suite.addTest(loader.loadTestsFromTestCase(test_class))
    
    # Capture output
    output = StringIO()
    runner = unittest.TextTestRunner(stream=output, verbosity=verbosity)
    result = runner.run(suite)
    
    # Print output
    print(output.getvalue())
    
    return result

def main():
    """Main test execution function"""
    print("Starting RAG System Comprehensive Tests...")
    
    # Initialize results tracker
    test_results = TestResults()
    
    # Define test categories
    test_categories = [
        ("CourseSearchTool Tests", [TestCourseSearchTool, TestCourseSearchToolEdgeCases]),
        ("AI Generator Integration Tests", [
            TestAIGeneratorToolIntegration, 
            TestToolCallErrorHandling,
            TestAIGeneratorSystemPrompt
        ]),
        ("RAG System Tests", [
            TestRAGSystemContentQueries,
            TestRAGSystemDocumentProcessing,
            TestRAGSystemComponentInitialization
        ])
    ]
    
    # Run each test category
    for category_name, test_classes in test_categories:
        try:
            result = run_test_category(category_name, test_classes, verbosity=2)
            test_results.add_result(category_name, result)
        except Exception as e:
            print(f"Error running {category_name}: {e}")
            # Create a mock failed result
            mock_result = unittest.TestResult()
            mock_result.testsRun = 0
            mock_result.errors = [("Setup Error", str(e))]
            test_results.add_result(category_name, mock_result)
    
    # Print comprehensive summary
    test_results.print_summary()
    
    # Analyze failing components
    failing_components = test_results.get_failing_components()
    
    if failing_components:
        print(f"\n{'='*80}")
        print("COMPONENT FAILURE ANALYSIS")
        print(f"{'='*80}")
        
        for component in failing_components:
            print(f"\nX FAILING COMPONENT: {component['component']}")
            print(f"   Failures: {component['failures']}")
            print(f"   Errors: {component['errors']}")
            print(f"   Failing Tests: {', '.join(component['issues'][:5])}")
            if len(component['issues']) > 5:
                print(f"   ... and {len(component['issues']) - 5} more")
        
        print(f"\n{'='*80}")
        print("RECOMMENDED FIXES")
        print(f"{'='*80}")
        
        # Generate fix recommendations based on failing components
        recommendations = generate_fix_recommendations(failing_components)
        for i, recommendation in enumerate(recommendations, 1):
            print(f"{i}. {recommendation}")
    
    else:
        print(f"\nOK ALL TESTS PASSED! No component issues detected.")
    
    return test_results

def generate_fix_recommendations(failing_components):
    """Generate fix recommendations based on failing test patterns"""
    recommendations = []
    
    component_names = [comp['component'] for comp in failing_components]
    
    if any('CourseSearchTool' in name for name in component_names):
        recommendations.append(
            "Check CourseSearchTool execute method: Verify vector store integration, "
            "result formatting, and error handling in search_tools.py:52"
        )
    
    if any('AI Generator' in name for name in component_names):
        recommendations.append(
            "Check AI Generator tool integration: Verify tool definitions format, "
            "tool calling mechanism, and API response handling in ai_generator.py:77"
        )
    
    if any('RAG System' in name for name in component_names):
        recommendations.append(
            "Check RAG System orchestration: Verify component initialization, "
            "query processing flow, and tool manager setup in rag_system.py:117"
        )
    
    # General recommendations
    recommendations.extend([
        "Verify all dependencies are installed correctly (ChromaDB, sentence-transformers, etc.)",
        "Check that API keys and configuration are properly set in config.py",
        "Ensure vector store is properly initialized and accessible",
        "Verify that mock objects in tests accurately reflect real component interfaces"
    ])
    
    return recommendations

if __name__ == '__main__':
    # Run all tests
    results = main()
    
    # Exit with appropriate code
    exit_code = 0 if (results.total_failures == 0 and results.total_errors == 0) else 1
    print(f"\nExiting with code {exit_code}")
    sys.exit(exit_code)