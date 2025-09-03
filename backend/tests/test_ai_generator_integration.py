"""Tests for AI generator CourseSearchTool integration"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ai_generator import AIGenerator
from search_tools import ToolManager, CourseSearchTool
from test_helpers import MockVectorStore, MockAIGenerator, TestConfig

class TestAIGeneratorToolIntegration(unittest.TestCase):
    """Test AI generator's integration with CourseSearchTool"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_vector_store = MockVectorStore()
        self.search_tool = CourseSearchTool(self.mock_vector_store)
        self.tool_manager = ToolManager()
        self.tool_manager.register_tool(self.search_tool)
        
        # Mock AI generator to avoid API calls
        self.mock_ai_generator = MockAIGenerator()
    
    def test_tool_definitions_structure(self):
        """Test that tool definitions are properly structured for AI"""
        definitions = self.tool_manager.get_tool_definitions()
        
        # Should have at least one tool definition
        self.assertTrue(len(definitions) > 0)
        
        # Check structure of CourseSearchTool definition
        search_def = None
        for definition in definitions:
            if definition.get("name") == "search_course_content":
                search_def = definition
                break
        
        self.assertIsNotNone(search_def)
        
        # Check required fields for AI tool calling
        self.assertIn("name", search_def)
        self.assertIn("description", search_def)
        self.assertIn("input_schema", search_def)
        
        # Check input schema structure
        schema = search_def["input_schema"]
        self.assertEqual(schema["type"], "object")
        self.assertIn("properties", schema)
        self.assertIn("required", schema)
        
        # Check that query is required
        self.assertIn("query", schema["required"])
    
    def test_mock_ai_generator_tool_usage(self):
        """Test mock AI generator uses tools correctly"""
        # Test without tools
        response = self.mock_ai_generator.generate_response("What is Python?")
        self.assertIsInstance(response, str)
        self.assertIsNone(self.mock_ai_generator.last_tools)
        
        # Test with tools
        tools = self.tool_manager.get_tool_definitions()
        response = self.mock_ai_generator.generate_response(
            "What is Python?",
            tools=tools,
            tool_manager=self.tool_manager
        )
        
        # Check that AI generator received tools
        self.assertEqual(self.mock_ai_generator.last_tools, tools)
        self.assertEqual(self.mock_ai_generator.last_tool_manager, self.tool_manager)
        
        # Response should indicate tool usage
        self.assertIn("course content", response.lower())
    
    @patch('anthropic.Anthropic')
    def test_real_ai_generator_initialization(self, mock_anthropic):
        """Test that real AI generator initializes correctly with tools"""
        # Mock the Anthropic client
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        # Initialize AI generator
        ai_generator = AIGenerator(
            api_key="test-key",
            model="claude-3-sonnet-20240229",
            provider="anthropic"
        )
        
        # Check initialization
        self.assertEqual(ai_generator.provider, "anthropic")
        self.assertEqual(ai_generator.model, "claude-3-sonnet-20240229")
        self.assertIsNotNone(ai_generator.client)
    
    @patch('anthropic.Anthropic')
    def test_anthropic_tool_calling_format(self, mock_anthropic):
        """Test that tools are formatted correctly for Anthropic API"""
        # Mock the Anthropic client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_response.stop_reason = "stop"
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        # Initialize AI generator
        ai_generator = AIGenerator(
            api_key="test-key",
            model="claude-3-sonnet-20240229",
            provider="anthropic"
        )
        
        # Generate response with tools
        tools = self.tool_manager.get_tool_definitions()
        response = ai_generator.generate_response(
            query="What is Python?",
            tools=tools,
            tool_manager=self.tool_manager
        )
        
        # Check that API was called
        mock_client.messages.create.assert_called_once()
        
        # Check API call parameters
        call_args = mock_client.messages.create.call_args
        self.assertIn("tools", call_args.kwargs)
        self.assertIn("tool_choice", call_args.kwargs)
        self.assertEqual(call_args.kwargs["tool_choice"]["type"], "auto")
    
    def test_tool_execution_flow(self):
        """Test the complete tool execution flow"""
        # Create a mock that simulates tool use
        class MockToolUseGenerator(MockAIGenerator):
            def generate_response(self, query, conversation_history=None, tools=None, tool_manager=None):
                if tools and tool_manager:
                    # Simulate tool execution
                    tool_result = tool_manager.execute_tool("search_course_content", query="python")
                    return f"Based on search results: {tool_result}"
                return "No tools available"
        
        mock_generator = MockToolUseGenerator()
        tools = self.tool_manager.get_tool_definitions()
        
        response = mock_generator.generate_response(
            "What is Python?",
            tools=tools,
            tool_manager=self.tool_manager
        )
        
        # Should include tool results
        self.assertIn("Based on search results", response)
        self.assertIn("Python Fundamentals", response)
    
    def test_system_prompt_structure(self):
        """Test that system prompt is properly structured"""
        # Create a real AI generator instance (but don't call API)
        with patch('anthropic.Anthropic'):
            ai_generator = AIGenerator(
                api_key="test-key",
                model="claude-3-sonnet-20240229",
                provider="anthropic"
            )
        
        # Check system prompt exists and has key components
        system_prompt = ai_generator.SYSTEM_PROMPT
        self.assertIsInstance(system_prompt, str)
        self.assertTrue(len(system_prompt) > 0)
        
        # Check for key sections
        self.assertIn("search_course_content", system_prompt)
        self.assertIn("get_course_outline", system_prompt)
        self.assertIn("Tool Selection Guidelines", system_prompt)
    
    def test_conversation_history_integration(self):
        """Test that conversation history is properly integrated with tool usage"""
        history = "Previous conversation:\nUser: What is programming?\nAI: Programming is writing code."
        
        response = self.mock_ai_generator.generate_response(
            "What about Python specifically?",
            conversation_history=history,
            tools=self.tool_manager.get_tool_definitions(),
            tool_manager=self.tool_manager
        )
        
        # Response should be generated (mock returns something)
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

class TestToolCallErrorHandling(unittest.TestCase):
    """Test error handling in tool calling scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_vector_store = MockVectorStore()
        self.search_tool = CourseSearchTool(self.mock_vector_store)
        self.tool_manager = ToolManager()
        self.tool_manager.register_tool(self.search_tool)
        self.mock_ai_generator = MockAIGenerator()
    
    def test_tool_execution_with_invalid_parameters(self):
        """Test tool execution with invalid parameters"""
        # Test missing required parameter
        result = self.tool_manager.execute_tool("search_course_content")
        self.assertIn("error", result.lower())
    
    def test_tool_execution_with_invalid_tool_name(self):
        """Test execution of non-existent tool"""
        result = self.tool_manager.execute_tool("non_existent_tool", query="test")
        self.assertIn("not found", result)
    
    def test_vector_store_error_handling(self):
        """Test handling of vector store errors"""
        # Mock vector store to raise exception
        error_vector_store = MockVectorStore()
        
        # Create tool with error-prone vector store
        error_search_tool = CourseSearchTool(error_vector_store)
        
        # Test error query
        result = error_search_tool.execute("error query")
        self.assertIn("Mock search error", result)
    
    def test_empty_tool_definitions(self):
        """Test behavior with empty tool definitions"""
        empty_tool_manager = ToolManager()
        definitions = empty_tool_manager.get_tool_definitions()
        
        self.assertEqual(len(definitions), 0)
        self.assertIsInstance(definitions, list)

class TestAIGeneratorSystemPrompt(unittest.TestCase):
    """Test system prompt effectiveness and structure"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('anthropic.Anthropic'):
            self.ai_generator = AIGenerator(
                api_key="test-key",
                model="claude-3-sonnet-20240229",
                provider="anthropic"
            )
    
    def test_system_prompt_tool_instructions(self):
        """Test that system prompt contains proper tool usage instructions"""
        prompt = self.ai_generator.SYSTEM_PROMPT
        
        # Check for tool-specific instructions
        self.assertIn("search_course_content", prompt)
        self.assertIn("get_course_outline", prompt)
        
        # Check for usage guidelines
        self.assertIn("Tool Selection Guidelines", prompt)
        self.assertIn("Content-specific queries", prompt)
        self.assertIn("Course outline/structure queries", prompt)
    
    def test_system_prompt_response_protocol(self):
        """Test system prompt contains response formatting instructions"""
        prompt = self.ai_generator.SYSTEM_PROMPT
        
        # Check for response protocols
        self.assertIn("Response Protocol", prompt)
        self.assertIn("Brief, Concise and focused", prompt)
        self.assertIn("Educational", prompt)
        
        # Check for formatting guidelines
        self.assertIn("No meta-commentary", prompt)
    
    def test_system_prompt_search_limitations(self):
        """Test system prompt includes search limitations"""
        prompt = self.ai_generator.SYSTEM_PROMPT
        
        # Check for search limitations
        self.assertIn("One search per query maximum", prompt)
        self.assertIn("If search yields no results", prompt)

if __name__ == '__main__':
    # Create a test suite
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Add all test cases
    suite.addTest(loader.loadTestsFromTestCase(TestAIGeneratorToolIntegration))
    suite.addTest(loader.loadTestsFromTestCase(TestToolCallErrorHandling))
    suite.addTest(loader.loadTestsFromTestCase(TestAIGeneratorSystemPrompt))
    
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