"""Tests for RAG system content-query handling"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os
import tempfile
import shutil
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from rag_system import RAGSystem
from test_helpers import MockVectorStore, MockAIGenerator, TestConfig, create_test_course, create_test_chunks
from document_processor import DocumentProcessor
from session_manager import SessionManager

class TestRAGSystemContentQueries(unittest.TestCase):
    """Test RAG system's handling of content-related queries"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = TestConfig()
        
        # Create a RAG system with mocked components
        with patch('rag_system.VectorStore') as mock_vector_store_class, \
             patch('rag_system.AIGenerator') as mock_ai_generator_class, \
             patch('rag_system.DocumentProcessor') as mock_doc_processor_class, \
             patch('rag_system.SessionManager') as mock_session_manager_class:
            
            # Set up mock instances
            self.mock_vector_store = MockVectorStore()
            self.mock_ai_generator = MockAIGenerator()
            self.mock_doc_processor = Mock()
            self.mock_session_manager = Mock()
            
            # Configure mock classes to return our mock instances
            mock_vector_store_class.return_value = self.mock_vector_store
            mock_ai_generator_class.return_value = self.mock_ai_generator
            mock_doc_processor_class.return_value = self.mock_doc_processor
            mock_session_manager_class.return_value = self.mock_session_manager
            
            # Initialize RAG system
            self.rag_system = RAGSystem(self.config)
    
    def test_basic_content_query(self):
        """Test basic content query processing"""
        query = "What is Python?"
        response, sources = self.rag_system.query(query)
        
        # Should return string response
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)
        
        # Should return sources list
        self.assertIsInstance(sources, list)
        
        # Check that AI generator was called with proper prompt
        self.assertIsNotNone(self.mock_ai_generator.last_query)
        self.assertIn(query, self.mock_ai_generator.last_query)
    
    def test_content_query_with_session(self):
        """Test content query with session history"""
        session_id = "test_session_123"
        query = "What is Python?"
        
        # Mock session manager to return some history
        self.mock_session_manager.get_conversation_history.return_value = "Previous: User asked about programming"
        
        response, sources = self.rag_system.query(query, session_id)
        
        # Should call session manager for history
        self.mock_session_manager.get_conversation_history.assert_called_with(session_id)
        
        # Should add exchange to session
        self.mock_session_manager.add_exchange.assert_called_once()
        
        # Verify the call arguments
        call_args = self.mock_session_manager.add_exchange.call_args
        self.assertEqual(call_args[0][0], session_id)  # session_id
        self.assertEqual(call_args[0][1], query)       # query
        self.assertEqual(call_args[0][2], response)    # response
    
    def test_tool_integration_in_query(self):
        """Test that tools are properly integrated in query processing"""
        query = "What is covered in Python lesson 1?"
        response, sources = self.rag_system.query(query)
        
        # Check that AI generator received tools
        self.assertIsNotNone(self.mock_ai_generator.last_tools)
        self.assertTrue(len(self.mock_ai_generator.last_tools) > 0)
        
        # Check that tool manager was passed
        self.assertIsNotNone(self.mock_ai_generator.last_tool_manager)
        
        # Verify tool definitions contain expected tools
        tool_names = [tool["name"] for tool in self.mock_ai_generator.last_tools]
        self.assertIn("search_course_content", tool_names)
    
    def test_source_tracking_and_reset(self):
        """Test that sources are properly tracked and reset"""
        # Execute a query that should return sources
        query = "What is Python?"
        response, sources = self.rag_system.query(query)
        
        # Sources should be retrieved from tool manager
        self.assertIsInstance(sources, list)
        
        # Note: In real implementation, sources would come from tool manager
        # Here we test the flow works without errors
    
    def test_different_query_types(self):
        """Test different types of content queries"""
        test_queries = [
            "What is Python?",
            "Explain variables in Python",
            "How do I use loops?",
            "What's in lesson 1?",
            "Show me the course outline"
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                response, sources = self.rag_system.query(query)
                
                # Each query should return valid response
                self.assertIsInstance(response, str)
                self.assertTrue(len(response) > 0)
                self.assertIsInstance(sources, list)
    
    def test_empty_query_handling(self):
        """Test handling of empty or invalid queries"""
        # Test empty query
        response, sources = self.rag_system.query("")
        self.assertIsInstance(response, str)
        self.assertIsInstance(sources, list)
        
        # Test whitespace-only query
        response, sources = self.rag_system.query("   ")
        self.assertIsInstance(response, str)
        self.assertIsInstance(sources, list)
    
    def test_course_analytics_integration(self):
        """Test that course analytics work properly"""
        # Mock vector store methods
        self.mock_vector_store.get_course_count = Mock(return_value=5)
        self.mock_vector_store.get_existing_course_titles = Mock(return_value=["Course 1", "Course 2"])
        
        analytics = self.rag_system.get_course_analytics()
        
        # Should return proper analytics structure
        self.assertIn("total_courses", analytics)
        self.assertIn("course_titles", analytics)
        self.assertEqual(analytics["total_courses"], 5)
        self.assertEqual(len(analytics["course_titles"]), 2)

class TestRAGSystemDocumentProcessing(unittest.TestCase):
    """Test RAG system's document processing capabilities"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = TestConfig()
        
        # Create a RAG system with mocked components
        with patch('rag_system.VectorStore') as mock_vector_store_class, \
             patch('rag_system.AIGenerator') as mock_ai_generator_class, \
             patch('rag_system.DocumentProcessor') as mock_doc_processor_class, \
             patch('rag_system.SessionManager') as mock_session_manager_class:
            
            # Set up mock instances
            self.mock_vector_store = MockVectorStore()
            self.mock_ai_generator = MockAIGenerator()
            self.mock_doc_processor = Mock()
            self.mock_session_manager = Mock()
            
            # Configure mock classes to return our mock instances
            mock_vector_store_class.return_value = self.mock_vector_store
            mock_ai_generator_class.return_value = self.mock_ai_generator
            mock_doc_processor_class.return_value = self.mock_doc_processor
            mock_session_manager_class.return_value = self.mock_session_manager
            
            # Initialize RAG system
            self.rag_system = RAGSystem(self.config)
    
    def test_add_course_document(self):
        """Test adding a single course document"""
        # Mock document processor return
        test_course = create_test_course()
        test_chunks = create_test_chunks()
        self.mock_doc_processor.process_course_document.return_value = (test_course, test_chunks)
        
        # Mock vector store methods
        self.mock_vector_store.add_course_metadata = Mock()
        self.mock_vector_store.add_course_content = Mock()
        
        # Add course document
        course, chunk_count = self.rag_system.add_course_document("/fake/path/course.pdf")
        
        # Check return values
        self.assertEqual(course.title, "Python Fundamentals")
        self.assertEqual(chunk_count, 2)
        
        # Check that vector store methods were called
        self.mock_vector_store.add_course_metadata.assert_called_once_with(test_course)
        self.mock_vector_store.add_course_content.assert_called_once_with(test_chunks)
    
    def test_add_course_document_error_handling(self):
        """Test error handling when document processing fails"""
        # Mock document processor to raise exception
        self.mock_doc_processor.process_course_document.side_effect = Exception("Processing failed")
        
        # Add course document
        course, chunk_count = self.rag_system.add_course_document("/fake/path/course.pdf")
        
        # Should return None and 0 for error case
        self.assertIsNone(course)
        self.assertEqual(chunk_count, 0)
    
    def test_add_course_folder_with_clear(self):
        """Test adding course folder with clear existing data"""
        with patch('os.path.exists') as mock_exists, \
             patch('os.listdir') as mock_listdir, \
             patch('os.path.isfile') as mock_isfile:
            
            # Mock file system
            mock_exists.return_value = True
            mock_listdir.return_value = ['course1.pdf', 'course2.txt', 'other.jpg']
            mock_isfile.return_value = True
            
            # Mock document processor
            test_course = create_test_course()
            test_chunks = create_test_chunks()
            self.mock_doc_processor.process_course_document.return_value = (test_course, test_chunks)
            
            # Mock vector store methods - start with empty titles
            self.mock_vector_store._existing_titles.clear()
            self.mock_vector_store.clear_all_data = Mock()
            self.mock_vector_store.add_course_metadata = Mock()
            self.mock_vector_store.add_course_content = Mock()
            
            # Add course folder with clear
            total_courses, total_chunks = self.rag_system.add_course_folder("/fake/path", clear_existing=True)
            
            # Should clear existing data
            self.mock_vector_store.clear_all_data.assert_called_once()
            
            # Should process valid files (pdf and txt, not jpg)
            self.assertEqual(self.mock_doc_processor.process_course_document.call_count, 2)
    
    def test_add_course_folder_skip_existing(self):
        """Test that existing courses are skipped when adding folder"""
        with patch('os.path.exists') as mock_exists, \
             patch('os.listdir') as mock_listdir, \
             patch('os.path.isfile') as mock_isfile:
            
            # Mock file system
            mock_exists.return_value = True
            mock_listdir.return_value = ['course1.pdf']
            mock_isfile.return_value = True
            
            # Mock document processor
            test_course = create_test_course()
            test_chunks = create_test_chunks()
            self.mock_doc_processor.process_course_document.return_value = (test_course, test_chunks)
            
            # Mock vector store to return existing course
            self.mock_vector_store._existing_titles.add("Python Fundamentals")
            self.mock_vector_store.add_course_metadata = Mock()
            self.mock_vector_store.add_course_content = Mock()
            
            # Add course folder
            total_courses, total_chunks = self.rag_system.add_course_folder("/fake/path")
            
            # Should skip existing course
            self.assertEqual(total_courses, 0)
            self.assertEqual(total_chunks, 0)
            
            # Should not call add methods
            self.mock_vector_store.add_course_metadata.assert_not_called()
            self.mock_vector_store.add_course_content.assert_not_called()
    
    def test_add_nonexistent_folder(self):
        """Test handling of non-existent folder"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            total_courses, total_chunks = self.rag_system.add_course_folder("/fake/nonexistent/path")
            
            # Should return 0, 0 for non-existent folder
            self.assertEqual(total_courses, 0)
            self.assertEqual(total_chunks, 0)

class TestRAGSystemComponentInitialization(unittest.TestCase):
    """Test RAG system component initialization"""
    
    def test_anthropic_provider_initialization(self):
        """Test initialization with Anthropic provider"""
        config = TestConfig()
        config.AI_PROVIDER = "anthropic"
        
        with patch('rag_system.VectorStore'), \
             patch('rag_system.AIGenerator') as mock_ai_gen, \
             patch('rag_system.DocumentProcessor'), \
             patch('rag_system.SessionManager'):
            
            rag_system = RAGSystem(config)
            
            # Should initialize with anthropic settings
            mock_ai_gen.assert_called_with(
                api_key=config.ANTHROPIC_API_KEY,
                model=config.ANTHROPIC_MODEL,
                provider="anthropic"
            )
    
    def test_deepseek_provider_initialization(self):
        """Test initialization with DeepSeek provider"""
        config = TestConfig()
        config.AI_PROVIDER = "deepseek"
        config.DEEPSEEK_API_KEY = "deepseek-key"
        config.DEEPSEEK_MODEL = "deepseek-chat"
        config.DEEPSEEK_BASE_URL = "https://api.deepseek.com"
        
        with patch('rag_system.VectorStore'), \
             patch('rag_system.AIGenerator') as mock_ai_gen, \
             patch('rag_system.DocumentProcessor'), \
             patch('rag_system.SessionManager'):
            
            rag_system = RAGSystem(config)
            
            # Should initialize with deepseek settings
            mock_ai_gen.assert_called_with(
                api_key=config.DEEPSEEK_API_KEY,
                model=config.DEEPSEEK_MODEL,
                provider="deepseek",
                base_url=config.DEEPSEEK_BASE_URL
            )
    
    def test_tool_manager_setup(self):
        """Test that tool manager is properly set up with tools"""
        config = TestConfig()
        
        with patch('rag_system.VectorStore') as mock_vs, \
             patch('rag_system.AIGenerator'), \
             patch('rag_system.DocumentProcessor'), \
             patch('rag_system.SessionManager'):
            
            # Create mock vector store instance
            mock_vector_store = MockVectorStore()
            mock_vs.return_value = mock_vector_store
            
            rag_system = RAGSystem(config)
            
            # Should have tool manager with registered tools
            self.assertIsNotNone(rag_system.tool_manager)
            self.assertIn("search_course_content", rag_system.tool_manager.tools)
            
            # Should have search and outline tools
            self.assertIsNotNone(rag_system.search_tool)
            self.assertIsNotNone(rag_system.outline_tool)

if __name__ == '__main__':
    # Create a test suite
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Add all test cases
    suite.addTest(loader.loadTestsFromTestCase(TestRAGSystemContentQueries))
    suite.addTest(loader.loadTestsFromTestCase(TestRAGSystemDocumentProcessing))
    suite.addTest(loader.loadTestsFromTestCase(TestRAGSystemComponentInitialization))
    
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