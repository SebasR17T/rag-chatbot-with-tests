"""Tests for CourseSearchTool execute method outputs"""

import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from search_tools import CourseSearchTool, ToolManager
from test_helpers import MockVectorStore, create_test_course, create_test_chunks
from vector_store import SearchResults

class TestCourseSearchTool(unittest.TestCase):
    """Test cases for CourseSearchTool execution and output formatting"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_vector_store = MockVectorStore()
        self.search_tool = CourseSearchTool(self.mock_vector_store)
        self.tool_manager = ToolManager()
        self.tool_manager.register_tool(self.search_tool)
    
    def test_get_tool_definition(self):
        """Test that tool definition is correctly structured"""
        definition = self.search_tool.get_tool_definition()
        
        # Check required fields
        self.assertIn("name", definition)
        self.assertIn("description", definition)
        self.assertIn("input_schema", definition)
        
        # Check tool name
        self.assertEqual(definition["name"], "search_course_content")
        
        # Check schema structure
        schema = definition["input_schema"]
        self.assertEqual(schema["type"], "object")
        self.assertIn("properties", schema)
        self.assertIn("required", schema)
        
        # Check required fields
        self.assertIn("query", schema["required"])
        
        # Check optional fields exist in properties
        properties = schema["properties"]
        self.assertIn("query", properties)
        self.assertIn("course_name", properties)
        self.assertIn("lesson_number", properties)
    
    def test_execute_basic_query(self):
        """Test basic query execution with successful results"""
        result = self.search_tool.execute("python")
        
        # Should return formatted results
        self.assertIsInstance(result, str)
        self.assertIn("Python Fundamentals", result)
        self.assertIn("Python is a programming language", result)
        
        # Check that sources are tracked
        self.assertTrue(len(self.search_tool.last_sources) > 0)
        self.assertIn("Python Fundamentals", self.search_tool.last_sources[0])
    
    def test_execute_with_course_filter(self):
        """Test query execution with course name filter"""
        result = self.search_tool.execute("python", course_name="Python Fundamentals")
        
        # Check that vector store received the course filter
        self.assertEqual(self.mock_vector_store.last_filters["course_name"], "Python Fundamentals")
        
        # Should return formatted results
        self.assertIsInstance(result, str)
        self.assertIn("Python Fundamentals", result)
    
    def test_execute_with_lesson_filter(self):
        """Test query execution with lesson number filter"""
        result = self.search_tool.execute("python", lesson_number=1)
        
        # Check that vector store received the lesson filter
        self.assertEqual(self.mock_vector_store.last_filters["lesson_number"], 1)
        
        # Should return formatted results
        self.assertIsInstance(result, str)
    
    def test_execute_with_both_filters(self):
        """Test query execution with both course and lesson filters"""
        result = self.search_tool.execute("python", course_name="Python Fundamentals", lesson_number=1)
        
        # Check that vector store received both filters
        self.assertEqual(self.mock_vector_store.last_filters["course_name"], "Python Fundamentals")
        self.assertEqual(self.mock_vector_store.last_filters["lesson_number"], 1)
    
    def test_execute_no_results(self):
        """Test query execution that returns no results"""
        result = self.search_tool.execute("no results query")
        
        # Should return appropriate message
        self.assertIsInstance(result, str)
        self.assertIn("No relevant content found", result)
        
        # Sources should be empty
        self.assertEqual(len(self.search_tool.last_sources), 0)
    
    def test_execute_no_results_with_filters(self):
        """Test no results message includes filter information"""
        result = self.search_tool.execute("no results query", course_name="Test Course", lesson_number=1)
        
        # Should include filter info in the message
        self.assertIn("No relevant content found", result)
        self.assertIn("Test Course", result)
        self.assertIn("lesson 1", result)
    
    def test_execute_error_handling(self):
        """Test error handling when vector store returns error"""
        result = self.search_tool.execute("error query")
        
        # Should return the error message
        self.assertIsInstance(result, str)
        self.assertIn("Mock search error", result)
    
    def test_format_results_with_lesson_numbers(self):
        """Test result formatting includes lesson numbers when available"""
        # Create mock search results
        results = SearchResults(
            documents=["Test content for lesson 1", "Test content for lesson 2"],
            metadata=[
                {"course_title": "Test Course", "lesson_number": 1},
                {"course_title": "Test Course", "lesson_number": 2}
            ],
            distances=[0.1, 0.2]
        )
        
        formatted = self.search_tool._format_results(results)
        
        # Should include lesson numbers in headers
        self.assertIn("[Test Course - Lesson 1]", formatted)
        self.assertIn("[Test Course - Lesson 2]", formatted)
        self.assertIn("Test content for lesson 1", formatted)
        self.assertIn("Test content for lesson 2", formatted)
    
    def test_format_results_without_lesson_numbers(self):
        """Test result formatting works without lesson numbers"""
        # Create mock search results without lesson numbers
        results = SearchResults(
            documents=["General course content"],
            metadata=[{"course_title": "Test Course"}],
            distances=[0.1]
        )
        
        formatted = self.search_tool._format_results(results)
        
        # Should include course title but no lesson number
        self.assertIn("[Test Course]", formatted)
        self.assertNotIn("Lesson", formatted)
        self.assertIn("General course content", formatted)
    
    def test_sources_tracking(self):
        """Test that sources are properly tracked and retrievable"""
        # Execute a query
        self.search_tool.execute("python")
        
        # Check sources are tracked
        self.assertTrue(len(self.search_tool.last_sources) > 0)
        
        # Execute another query
        self.search_tool.execute("no results query")
        
        # Sources should be cleared for empty results
        self.assertEqual(len(self.search_tool.last_sources), 0)
    
    def test_tool_manager_integration(self):
        """Test integration with ToolManager"""
        # Test tool registration
        self.assertIn("search_course_content", self.tool_manager.tools)
        
        # Test tool execution through manager
        result = self.tool_manager.execute_tool("search_course_content", query="python")
        self.assertIsInstance(result, str)
        
        # Test source retrieval through manager
        sources = self.tool_manager.get_last_sources()
        self.assertIsInstance(sources, list)
        
        # Test source reset through manager
        self.tool_manager.reset_sources()
        sources_after_reset = self.tool_manager.get_last_sources()
        self.assertEqual(len(sources_after_reset), 0)
    
    def test_invalid_tool_execution(self):
        """Test handling of invalid tool names"""
        result = self.tool_manager.execute_tool("invalid_tool", query="test")
        self.assertIn("not found", result)

class TestCourseSearchToolEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for CourseSearchTool"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_vector_store = MockVectorStore()
        self.search_tool = CourseSearchTool(self.mock_vector_store)
    
    def test_empty_query(self):
        """Test execution with empty query"""
        result = self.search_tool.execute("")
        self.assertIsInstance(result, str)
    
    def test_none_query(self):
        """Test execution with None query - should return error message"""
        result = self.search_tool.execute(None)
        self.assertIn("Error: Query cannot be None", result)
    
    def test_special_characters_in_query(self):
        """Test query with special characters"""
        result = self.search_tool.execute("What is Python? & How does it work!")
        self.assertIsInstance(result, str)
    
    def test_unicode_query(self):
        """Test query with unicode characters"""
        result = self.search_tool.execute("¿Qué es Python? 中文 العربية")
        self.assertIsInstance(result, str)
    
    def test_very_long_query(self):
        """Test with very long query"""
        long_query = "What is Python? " * 100
        result = self.search_tool.execute(long_query)
        self.assertIsInstance(result, str)
    
    def test_negative_lesson_number(self):
        """Test with negative lesson number"""
        result = self.search_tool.execute("python", lesson_number=-1)
        self.assertIsInstance(result, str)
    
    def test_zero_lesson_number(self):
        """Test with zero lesson number"""
        result = self.search_tool.execute("python", lesson_number=0)
        self.assertIsInstance(result, str)
    
    def test_large_lesson_number(self):
        """Test with very large lesson number"""
        result = self.search_tool.execute("python", lesson_number=9999)
        self.assertIsInstance(result, str)

if __name__ == '__main__':
    # Create a test suite
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Add all test cases
    suite.addTest(loader.loadTestsFromTestCase(TestCourseSearchTool))
    suite.addTest(loader.loadTestsFromTestCase(TestCourseSearchToolEdgeCases))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTest Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")