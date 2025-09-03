import anthropic
from openai import OpenAI
from typing import List, Optional, Dict, Any

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive search tools for course information.

Available Tools:
1. **search_course_content** - For detailed course content, lesson materials, and specific educational topics
2. **get_course_outline** - For course structure, lesson lists, course titles, and course links

Tool Selection Guidelines:
- **Course outline/structure queries**: Use get_course_outline for questions about:
  - Course outlines, lesson lists, course structure
  - "What is the outline of [course]?"
  - "What lessons are in [course]?"
  - "Show me the structure of [course]"
- **Content-specific queries**: Use search_course_content for questions about:
  - Specific lesson content, detailed explanations, examples
  - "What is covered in lesson X?"
  - "Explain concept Y from [course]"

Search Tool Usage:
- **One search per query maximum**
- Choose the most appropriate tool based on the query type
- Synthesize search results into accurate, fact-based responses
- If search yields no results, state this clearly without offering alternatives

Response Protocol for Course Outlines:
- When using get_course_outline, always include:
  - **Course title** (exact title from the tool)
  - **Course link** (if available)
  - **Complete lesson list** with lesson numbers and titles
  - **Total number of lessons**

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without searching
- **Course-specific questions**: Search first, then answer
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, search explanations, or question-type analysis
 - Do not mention "based on the search results"

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""
    
    def __init__(self, api_key: str, model: str, provider: str = "anthropic", base_url: str = None):
        self.provider = provider
        self.model = model
        
        if provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=api_key)
            # Pre-build base API parameters for Anthropic
            self.base_params = {
                "model": self.model,
                "temperature": 0,
                "max_tokens": 800
            }
        elif provider == "deepseek":
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            # Pre-build base API parameters for DeepSeek/OpenAI
            self.base_params = {
                "model": self.model,
                "temperature": 0,
                "max_tokens": 800
            }
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            
        Returns:
            Generated response as string
        """
        
        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history 
            else self.SYSTEM_PROMPT
        )
        
        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content
        }
        
        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}
        
        # Get response based on provider
        if self.provider == "anthropic":
            response = self.client.messages.create(**api_params)
        elif self.provider == "deepseek":
            # Convert to OpenAI format
            openai_messages = [{"role": "system", "content": system_content}] + api_params["messages"]
            openai_params = {
                "model": self.model,
                "messages": openai_messages,
                "temperature": 0,
                "max_tokens": 800
            }
            response = self.client.chat.completions.create(**openai_params)
            # Convert response format
            class MockResponse:
                def __init__(self, content_text, stop_reason="stop"):
                    self.content = [type('obj', (object,), {'text': content_text})]
                    self.stop_reason = stop_reason
            response = MockResponse(response.choices[0].message.content)
        
        # Handle tool execution if needed
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_tool_execution(response, api_params, tool_manager)
        
        # Return direct response
        return response.content[0].text
    
    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        Handle execution of tool calls and get follow-up response.
        
        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters
            tool_manager: Manager to execute tools
            
        Returns:
            Final response text after tool execution
        """
        # Start with existing messages
        messages = base_params["messages"].copy()
        
        # Add AI's tool use response
        messages.append({"role": "assistant", "content": initial_response.content})
        
        # Execute all tool calls and collect results
        tool_results = []
        for content_block in initial_response.content:
            if content_block.type == "tool_use":
                tool_result = tool_manager.execute_tool(
                    content_block.name, 
                    **content_block.input
                )
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": tool_result
                })
        
        # Add tool results as single message
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        
        # Prepare final API call without tools
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": base_params["system"]
        }
        
        # Get final response
        final_response = self.client.messages.create(**final_params)
        return final_response.content[0].text