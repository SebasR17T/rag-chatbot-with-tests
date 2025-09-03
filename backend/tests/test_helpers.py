"""Test helper utilities and fixtures for RAG system testing"""

import os
import tempfile
import shutil
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from vector_store import VectorStore, SearchResults
from models import Course, Lesson, CourseChunk

class MockVectorStore:
    """Mock vector store for testing without ChromaDB dependencies"""
    
    def __init__(self, mock_courses=None, mock_content=None):
        self.mock_courses = mock_courses or {}
        self.mock_content = mock_content or []
        self.last_query = None
        self.last_filters = None
        self._existing_titles = set()
        self._course_metadata = {}
        self._content_chunks = []
    
    def search(self, query: str, course_name=None, lesson_number=None, limit=None):
        """Mock search method that returns predefined results"""
        
        # Handle None query
        if query is None:
            return SearchResults.empty("Query cannot be None")
        
        if not isinstance(query, str):
            return SearchResults.empty(f"Query must be string, got {type(query).__name__}")
        
        self.last_query = query
        self.last_filters = {'course_name': course_name, 'lesson_number': lesson_number}
        
        # Return different results based on the query
        if "no results" in query.lower():
            return SearchResults(documents=[], metadata=[], distances=[])
        
        if "error" in query.lower():
            return SearchResults.empty("Mock search error")
        
        # Return mock course content
        if any(term in query.lower() for term in ["python", "introduction", "lesson"]):
            return SearchResults(
                documents=[
                    "Python is a programming language used for data science and web development.",
                    "This lesson covers basic Python syntax and variables."
                ],
                metadata=[
                    {"course_title": "Python Fundamentals", "lesson_number": 1, "lesson_title": "Introduction to Python"},
                    {"course_title": "Python Fundamentals", "lesson_number": 2, "lesson_title": "Variables and Data Types"}
                ],
                distances=[0.2, 0.3]
            )
        
        # Return empty results for unknown queries
        return SearchResults(documents=[], metadata=[], distances=[])
    
    def get_existing_course_titles(self) -> list:
        """Get all existing course titles"""
        return list(self._existing_titles)
    
    def clear_all_data(self):
        """Clear all data from the mock store"""
        self._existing_titles.clear()
        self._course_metadata.clear()
        self._content_chunks.clear()
    
    def add_course_metadata(self, course):
        """Add course metadata to the mock store"""
        self._existing_titles.add(course.title)
        self._course_metadata[course.title] = course
    
    def add_course_content(self, chunks):
        """Add course content chunks to the mock store"""
        self._content_chunks.extend(chunks)
    
    def get_course_count(self) -> int:
        """Get the total number of courses"""
        return len(self._existing_titles)
    
    def _resolve_course_name(self, course_name: str):
        """Mock course name resolution"""
        mock_mapping = {
            "python": "Python Fundamentals",
            "mcp": "MCP Introduction",
            "unknown": None
        }
        return mock_mapping.get(course_name.lower())

def create_test_course() -> Course:
    """Create a test course object"""
    lessons = [
        Lesson(lesson_number=1, title="Introduction to Python", lesson_link="http://example.com/lesson1"),
        Lesson(lesson_number=2, title="Variables and Data Types", lesson_link="http://example.com/lesson2")
    ]
    return Course(
        title="Python Fundamentals",
        instructor="Test Instructor",
        course_link="http://example.com/course",
        lessons=lessons
    )

def create_test_chunks() -> List[CourseChunk]:
    """Create test course chunks"""
    return [
        CourseChunk(
            course_title="Python Fundamentals",
            lesson_number=1,
            chunk_index=0,
            content="Python is a programming language used for data science and web development."
        ),
        CourseChunk(
            course_title="Python Fundamentals", 
            lesson_number=2,
            chunk_index=1,
            content="This lesson covers basic Python syntax and variables."
        )
    ]

class MockAIGenerator:
    """Mock AI generator for testing without API calls"""
    
    def __init__(self):
        self.last_query = None
        self.last_tools = None
        self.last_tool_manager = None
        self.responses = {
            "default": "This is a mock AI response.",
            "python": "Python is a versatile programming language.",
            "tool_use": "Using search tools to find course content."
        }
    
    def generate_response(self, query: str, conversation_history=None, tools=None, tool_manager=None):
        """Mock response generation"""
        self.last_query = query
        self.last_tools = tools
        self.last_tool_manager = tool_manager
        
        # Simulate tool use if tools are provided
        if tools and tool_manager:
            # Mock tool execution
            if hasattr(tool_manager, 'execute_tool'):
                tool_result = tool_manager.execute_tool("search_course_content", query="python")
                return f"Based on course content: {tool_result[:100]}..."
        
        # Return response based on query content
        for key, response in self.responses.items():
            if key.lower() in query.lower():
                return response
        
        return self.responses["default"]

def create_temp_test_file(content: str) -> str:
    """Create a temporary test file with given content"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    temp_file.write(content)
    temp_file.close()
    return temp_file.name

def cleanup_temp_file(file_path: str):
    """Clean up temporary test file"""
    if os.path.exists(file_path):
        os.unlink(file_path)

class TestConfig:
    """Test configuration object"""
    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 100
    CHROMA_PATH = "./test_chroma_db"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    MAX_RESULTS = 5
    MAX_HISTORY = 2
    AI_PROVIDER = "anthropic"
    ANTHROPIC_API_KEY = "test-key"
    ANTHROPIC_MODEL = "claude-3-sonnet-20240229"