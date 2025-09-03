from typing import Dict, Any, Optional, Protocol
from abc import ABC, abstractmethod
from vector_store import VectorStore, SearchResults


class Tool(ABC):
    """Abstract base class for all tools"""
    
    @abstractmethod
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return Anthropic tool definition for this tool"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool with given parameters"""
        pass


class CourseSearchTool(Tool):
    """Tool for searching course content with semantic course name matching"""
    
    def __init__(self, vector_store: VectorStore):
        self.store = vector_store
        self.last_sources = []  # Track sources from last search
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return Anthropic tool definition for this tool"""
        return {
            "name": "search_course_content",
            "description": "Search course materials with smart course name matching and lesson filtering",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string", 
                        "description": "What to search for in the course content"
                    },
                    "course_name": {
                        "type": "string",
                        "description": "Course title (partial matches work, e.g. 'MCP', 'Introduction')"
                    },
                    "lesson_number": {
                        "type": "integer",
                        "description": "Specific lesson number to search within (e.g. 1, 2, 3)"
                    }
                },
                "required": ["query"]
            }
        }
    
    def execute(self, query: str, course_name: Optional[str] = None, lesson_number: Optional[int] = None) -> str:
        """
        Execute the search tool with given parameters.
        
        Args:
            query: What to search for
            course_name: Optional course filter
            lesson_number: Optional lesson filter
            
        Returns:
            Formatted search results or error message
        """
        
        # Input validation
        if query is None:
            return "Error: Query cannot be None. Please provide a search query."
        
        if not isinstance(query, str):
            return f"Error: Query must be a string, got {type(query).__name__}."
        
        if not query.strip():
            return "Error: Query cannot be empty. Please provide a search query."
        
        # Parameter validation
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
        
        # Handle empty results
        if results.is_empty():
            self.last_sources = []  # Explicitly clear sources for empty results
            filter_info = ""
            if course_name:
                filter_info += f" in course '{course_name}'"
            if lesson_number:
                filter_info += f" in lesson {lesson_number}"
            return f"No relevant content found{filter_info}."
        
        # Format and return results
        return self._format_results(results)
    
    def _format_results(self, results: SearchResults) -> str:
        """Format search results with course and lesson context"""
        formatted = []
        sources = []  # Track sources for the UI
        
        for doc, meta in zip(results.documents, results.metadata):
            course_title = meta.get('course_title', 'unknown')
            lesson_num = meta.get('lesson_number')
            
            # Build context header
            header = f"[{course_title}"
            if lesson_num is not None:
                header += f" - Lesson {lesson_num}"
            header += "]"
            
            # Track source for the UI
            source = course_title
            if lesson_num is not None:
                source += f" - Lesson {lesson_num}"
            sources.append(source)
            
            formatted.append(f"{header}\n{doc}")
        
        # Store sources for retrieval
        self.last_sources = sources
        
        return "\n\n".join(formatted)


class CourseOutlineTool(Tool):
    """Tool for retrieving complete course outlines with lessons"""
    
    def __init__(self, vector_store: VectorStore):
        self.store = vector_store
        self.last_sources = []
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return Anthropic tool definition for this tool"""
        return {
            "name": "get_course_outline",
            "description": "Get complete course outline including course title, link, and all lessons with their numbers and titles",
            "input_schema": {
                "type": "object",
                "properties": {
                    "course_title": {
                        "type": "string",
                        "description": "Course title (partial matches work, e.g. 'MCP', 'Introduction', 'Build Rich-Context AI Apps')"
                    }
                },
                "required": ["course_title"]
            }
        }
    
    def execute(self, course_title: str) -> str:
        """
        Execute the course outline tool to get course structure.
        
        Args:
            course_title: Course title to get outline for
            
        Returns:
            Formatted course outline or error message
        """
        
        # Get course metadata from the vector store
        try:
            course_data = self._get_course_metadata(course_title)
            
            if not course_data:
                return f"No course found matching '{course_title}'. Please check the course title and try again."
            
            # Format and return the outline
            return self._format_course_outline(course_data)
            
        except Exception as e:
            return f"Error retrieving course outline: {str(e)}"
    
    def _get_course_metadata(self, course_title: str) -> Optional[Dict[str, Any]]:
        """Get course metadata from the vector store"""
        
        # Search for course metadata using the vector store's search functionality
        # This will help us find the course even with partial matches
        results = self.store.search(
            query=f"course outline {course_title}",
            course_name=course_title,
            limit=50  # Get more results to ensure we capture all lessons
        )
        
        if results.error or results.is_empty():
            return None
        
        # Extract course metadata from search results
        course_data = {
            'title': None,
            'link': None,
            'lessons': []
        }
        
        # Process metadata to extract course information
        for doc, metadata in zip(results.documents, results.metadata):
            course_title_meta = metadata.get('course_title')
            course_link = metadata.get('course_link', '')
            lesson_number = metadata.get('lesson_number')
            lesson_title = metadata.get('lesson_title', '')
            
            # Set course title and link (use first match)
            if not course_data['title'] and course_title_meta:
                course_data['title'] = course_title_meta
                course_data['link'] = course_link
            
            # Add lesson information if available
            if lesson_number is not None and lesson_title:
                lesson_info = {
                    'number': lesson_number,
                    'title': lesson_title
                }
                
                # Avoid duplicates
                if lesson_info not in course_data['lessons']:
                    course_data['lessons'].append(lesson_info)
        
        # Sort lessons by number
        course_data['lessons'].sort(key=lambda x: x['number'])
        
        return course_data if course_data['title'] else None
    
    def _format_course_outline(self, course_data: Dict[str, Any]) -> str:
        """Format course outline for display"""
        
        outline_parts = []
        
        # Course title
        outline_parts.append(f"**Course Title:** {course_data['title']}")
        
        # Course link (if available)
        if course_data.get('link'):
            outline_parts.append(f"**Course Link:** {course_data['link']}")
        
        # Lessons
        if course_data['lessons']:
            outline_parts.append(f"**Total Lessons:** {len(course_data['lessons'])}")
            outline_parts.append("\n**Course Outline:**")
            
            for lesson in course_data['lessons']:
                outline_parts.append(f"  {lesson['number']}. {lesson['title']}")
        else:
            outline_parts.append("**Lessons:** No lesson information available")
        
        # Set sources for UI
        self.last_sources = [course_data['title']]
        
        return "\n".join(outline_parts)


class ToolManager:
    """Manages available tools for the AI"""
    
    def __init__(self):
        self.tools = {}
    
    def register_tool(self, tool: Tool):
        """Register any tool that implements the Tool interface"""
        tool_def = tool.get_tool_definition()
        tool_name = tool_def.get("name")
        if not tool_name:
            raise ValueError("Tool must have a 'name' in its definition")
        self.tools[tool_name] = tool

    
    def get_tool_definitions(self) -> list:
        """Get all tool definitions for Anthropic tool calling"""
        return [tool.get_tool_definition() for tool in self.tools.values()]
    
    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool by name with given parameters"""
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
    
    def get_last_sources(self) -> list:
        """Get sources from the last search operation"""
        # Check all tools for last_sources attribute
        for tool in self.tools.values():
            if hasattr(tool, 'last_sources') and tool.last_sources:
                return tool.last_sources
        return []

    def reset_sources(self):
        """Reset sources from all tools that track sources"""
        for tool in self.tools.values():
            if hasattr(tool, 'last_sources'):
                tool.last_sources = []