"""
Proposed fixes for issues identified by the RAG system tests.

This file contains the specific code changes needed to fix the failing tests
and improve system robustness.
"""

# Fix 1: CourseSearchTool input validation
# File: search_tools.py, Line: 52
def execute_fixed(self, query: str, course_name: Optional[str] = None, lesson_number: Optional[int] = None) -> str:
    """
    FIXED VERSION: Execute the search tool with given parameters.
    
    Args:
        query: What to search for
        course_name: Optional course filter
        lesson_number: Optional lesson filter
        
    Returns:
        Formatted search results or error message
    """
    
    # INPUT VALIDATION (NEW)
    if query is None:
        return "Error: Query cannot be None. Please provide a search query."
    
    if not isinstance(query, str):
        return f"Error: Query must be a string, got {type(query).__name__}."
    
    if not query.strip():
        return "Error: Query cannot be empty. Please provide a search query."
    
    # PARAMETER VALIDATION (NEW)
    if course_name is not None and not isinstance(course_name, str):
        return f"Error: Course name must be a string, got {type(course_name).__name__}."
    
    if lesson_number is not None and not isinstance(lesson_number, int):
        return f"Error: Lesson number must be an integer, got {type(lesson_number).__name__}."
    
    # Use the vector store's unified search interface
    try:
        results = self.store.search(
            query=query,
            course_name=course_name,
            lesson_number=lesson_number
        )
    except Exception as e:
        return f"Search error: {str(e)}"
    
    # Handle errors
    if results.error:
        return results.error
    
    # Handle empty results - FIXED: Clear sources explicitly
    if results.is_empty():
        self.last_sources = []  # FIXED: Explicitly clear sources
        filter_info = ""
        if course_name:
            filter_info += f" in course '{course_name}'"
        if lesson_number:
            filter_info += f" in lesson {lesson_number}"
        return f"No relevant content found{filter_info}."
    
    # Format and return results
    return self._format_results(results)


# Fix 2: ToolManager error handling
# File: search_tools.py, Line: 261
def execute_tool_fixed(self, tool_name: str, **kwargs) -> str:
    """FIXED VERSION: Execute a tool by name with given parameters"""
    if tool_name not in self.tools:
        return f"Tool '{tool_name}' not found. Available tools: {', '.join(self.tools.keys())}"
    
    try:
        return self.tools[tool_name].execute(**kwargs)
    except TypeError as e:
        # Handle missing required parameters gracefully
        error_msg = str(e)
        if "required positional argument" in error_msg:
            return f"Error: Missing required parameter for tool '{tool_name}'. {error_msg}"
        return f"Error executing tool '{tool_name}': {error_msg}"
    except ValueError as e:
        return f"Error: Invalid parameter value for tool '{tool_name}': {str(e)}"
    except Exception as e:
        return f"Unexpected error in tool '{tool_name}': {str(e)}"


# Fix 3: Enhanced MockVectorStore for better testing
# File: test_helpers.py
class MockVectorStoreFixed:
    """Enhanced mock vector store that matches real VectorStore interface"""
    
    def __init__(self, mock_courses=None, mock_content=None):
        self.mock_courses = mock_courses or {}
        self.mock_content = mock_content or []
        self.last_query = None
        self.last_filters = None
        self._existing_titles = set()
        self._course_metadata = {}
        self._content_chunks = []
    
    def search(self, query: str, course_name=None, lesson_number=None, limit=None):
        """FIXED: Mock search method with proper None handling"""
        
        # Handle None query (FIXED)
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
        """FIXED: Added missing method"""
        return list(self._existing_titles)
    
    def clear_all_data(self):
        """FIXED: Added missing method"""
        self._existing_titles.clear()
        self._course_metadata.clear()
        self._content_chunks.clear()
    
    def add_course_metadata(self, course):
        """FIXED: Track added courses"""
        self._existing_titles.add(course.title)
        self._course_metadata[course.title] = course
    
    def add_course_content(self, chunks):
        """FIXED: Track added content"""
        self._content_chunks.extend(chunks)
    
    def get_course_count(self) -> int:
        """Added for completeness"""
        return len(self._existing_titles)


# Fix 4: Vector store input validation
# File: vector_store.py, Line: 61
def search_fixed(self, 
               query: str,
               course_name: Optional[str] = None,
               lesson_number: Optional[int] = None,
               limit: Optional[int] = None) -> SearchResults:
    """
    FIXED VERSION: Main search interface with input validation
    """
    
    # INPUT VALIDATION (NEW)
    if query is None:
        return SearchResults.empty("Query cannot be None")
    
    if not isinstance(query, str):
        return SearchResults.empty(f"Query must be a string, got {type(query).__name__}")
    
    if not query.strip():
        return SearchResults.empty("Query cannot be empty")
    
    # PARAMETER VALIDATION (NEW) 
    if course_name is not None and not isinstance(course_name, str):
        return SearchResults.empty(f"Course name must be a string, got {type(course_name).__name__}")
    
    if lesson_number is not None and not isinstance(lesson_number, int):
        return SearchResults.empty(f"Lesson number must be an integer, got {type(lesson_number).__name__}")
    
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        return SearchResults.empty("Limit must be a positive integer")
    
    # Step 1: Resolve course name if provided
    course_title = None
    if course_name:
        try:
            course_title = self._resolve_course_name(course_name)
            if not course_title:
                return SearchResults.empty(f"No course found matching '{course_name}'")
        except Exception as e:
            return SearchResults.empty(f"Error resolving course name: {str(e)}")
    
    # Step 2: Build filter for content search
    filter_dict = self._build_filter(course_title, lesson_number)
    
    # Step 3: Search course content
    search_limit = limit if limit is not None else self.max_results
    
    try:
        results = self.course_content.query(
            query_texts=[query],
            n_results=search_limit,
            where=filter_dict
        )
        return SearchResults.from_chroma(results)
    except Exception as e:
        return SearchResults.empty(f"Search error: {str(e)}")


# Usage Instructions:
"""
To implement these fixes:

1. Apply Fix 1 to search_tools.py:52 (CourseSearchTool.execute method)
2. Apply Fix 2 to search_tools.py:261 (ToolManager.execute_tool method) 
3. Apply Fix 3 to test_helpers.py (replace MockVectorStore class)
4. Apply Fix 4 to vector_store.py:61 (VectorStore.search method)

After applying fixes, run tests again to verify 98%+ success rate.
"""