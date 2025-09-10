# from typing import Optional
# from contextlib import AsyncExitStack
# import traceback
# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client
# from datetime import datetime
# from utils.logger import logger
# import json 
# import os

# from google.generativeai.types import FunctionDeclaration, Tool
# import asyncio

# import google.generativeai as genai 
# from dotenv import load_dotenv

# load_dotenv(r"C:\Users\lenovo\Desktop\MCP\YT\Client\C_Trail1\api\.env")

# class MCPClient:

#     # initialization
#     def __init__(self):
#         self.session: Optional[ClientSession] = None
#         self.exit_stack = AsyncExitStack()  
#         api_key = os.getenv("GOOGLE_API_KEY")
#         if not api_key:
#             raise RuntimeError("GOOGLE_API_KEY is not set. Please add it to your environment or .env file.")
#         genai.configure(api_key=api_key)
#         self.llm = genai.GenerativeModel("gemini-1.5-flash")
#         self.tools = []
#         self.messages = []
#         self.logger = logger



#     def _sanitize_schema(self, schema) -> dict:
#         """Remove fields unsupported by Gemini tool parameter schemas.

#         Gemini expects JSON Schema-like objects but rejects unknown fields like
#         "title" at the top level. This function removes known-problematic keys
#         recursively.
#         """
#         # Handle None
#         if schema is None:
#             return {}
        
#         # Handle lists - convert to object with indexed properties
#         if isinstance(schema, list):
#             if not schema:  # empty list
#                 return {}
#             # Convert list to object with indexed properties
#             return {
#                 "type": "object",
#                 "properties": {f"item_{i}": self._sanitize_schema(item) for i, item in enumerate(schema)}
#             }
        
#         # Handle non-dict types (strings, numbers, booleans, etc.)
#         if not isinstance(schema, dict):
#             return schema

#         disallowed_keys = {"title", "$id", "$schema"}
#         sanitized: dict = {}
        
#         for key, value in schema.items():
#             if key in disallowed_keys:
#                 continue
#             if isinstance(value, dict):
#                 sanitized[key] = self._sanitize_schema(value)
#             elif isinstance(value, list):
#                 sanitized[key] = [self._sanitize_schema(v) for v in value]
#             else:
#                 sanitized[key] = value
        
#         return sanitized
    
#     def _make_json_safe(self, value):
#         """Best-effort conversion to JSON-serializable types for tool responses."""
#         try:
#             # Primitive types are already safe
#             if isinstance(value, (str, int, float, bool)) or value is None:
#                 return value
#             # Lists: coerce each element
#             if isinstance(value, list):
#                 return [self._make_json_safe(v) for v in value]
#             # Dicts: coerce values
#             if isinstance(value, dict):
#                 return {str(k): self._make_json_safe(v) for k, v in value.items()}
#             # Objects with to_dict/dict/model_dump
#             if hasattr(value, "to_dict"):
#                 return self._make_json_safe(value.to_dict())
#             if hasattr(value, "dict"):
#                 return self._make_json_safe(value.dict())
#             if hasattr(value, "model_dump"):
#                 return self._make_json_safe(value.model_dump())
#             # Fallback: string representation
#             return str(value)
#         except Exception:
#             return str(value)
#     #connect to MCP server
#     async def connect_to_server(self, server_script_path: str):
#         try:
#             is_python = server_script_path.endswith(".py")
#             is_js = server_script_path.endswith(".js")
#             if not (is_python or is_js):
#                 raise ValueError("Server script must be a .py or .js file")

#             command = "python" if is_python else "node"
#             server_params = StdioServerParameters(
#                 command=command, args=[server_script_path], env=None
#             )

#             stdio_transport = await self.exit_stack.enter_async_context(
#                 stdio_client(server_params)
#             )
#             self.stdio, self.write = stdio_transport
#             self.session = await self.exit_stack.enter_async_context(
#                 ClientSession(self.stdio, self.write)
#             )

#             await self.session.initialize()

#             self.logger.info("Connected to MCP server")

#             # mcp_tools = await self.get_mcp_tools()
#             # self.tools = []
#             # for tool in mcp_tools:
#             #     input_schema = getattr(tool, "inputSchema", None)
#             #     if isinstance(input_schema, dict):
#             #         input_schema = self._sanitize_schema(input_schema)
#             #     self.tools.append({
#             #         "name": tool.name,
#             #         "description": tool.description,
#             #         "input_schema": input_schema,
#             #     })
#             # Add this in your connect_to_server method after getting MCP tools
#             mcp_tools = await self.get_mcp_tools()
#             self.tools = []
#             for tool in mcp_tools:
#                 input_schema = getattr(tool, "inputSchema", None)
                
#                 # Debug logging
#                 self.logger.info(f"Tool {tool.name} original schema type: {type(input_schema)}")
#                 self.logger.info(f"Tool {tool.name} original schema: {input_schema}")
                
#                 # Skip tools without a valid name
#                 if not getattr(tool, "name", None):
#                     self.logger.info("Skipping tool with empty name")
#                     continue

#                 if isinstance(input_schema, dict):
#                     input_schema = self._sanitize_schema(input_schema)
#                 elif isinstance(input_schema, list):
#                     # Handle list schemas
#                     self.logger.info(f"Converting list schema for tool {tool.name}")
#                     input_schema = self._sanitize_schema(input_schema)
#                 elif input_schema is None:
#                     input_schema = {}
#                 else:
#                     # Handle other types
#                     self.logger.info(f"Unexpected schema type for tool {tool.name}: {type(input_schema)}")
#                     input_schema = {}
                
#                 # Debug logging after sanitization
#                 self.logger.info(f"Tool {tool.name} sanitized schema: {input_schema}")
                
#                 self.tools.append({
#                     "name": tool.name,
#                     "description": tool.description,
#                     "input_schema": input_schema,
#                 })
#             self.logger.info(
#                 f"Available tools: {[tool['name'] for tool in self.tools]}"
#             )

#             return True

#         except Exception as e:
#             self.logger.error(f"Error connecting to MCP server: {e}")
#             traceback.print_exc()
#             raise

#     # get mcp tool list
#     async def get_mcp_tools(self):
#         try:
#             response = await self.session.list_tools()
#             return response.tools
#         except Exception as e:
#             self.logger.error(f"Error getting MCP tools: {e}")
#             raise




#     # process query from client
#     async def process_query(self, query: str):
#         try:
#             self.logger.info(f"Processing query: {query}")
#             user_message = {"role": "user", "content": query}
#             self.messages = [user_message]

#             while True:
#                 response = await self.call_llm()

#                 # the response is a text message
#                 if response.content[0].type == "text" and len(response.content) == 1:
#                     assistant_message = {
#                         "role": "assistant",
#                         "content": response.content[0].text,
#                     }
#                     self.messages.append(assistant_message)
#                     await self.log_conversation()
#                     break

#                 # the response is a tool call
#                 assistant_message = {
#                     "role": "assistant",
#                     "content": response.to_dict()["content"],
#                 }
#                 self.messages.append(assistant_message)
#                 await self.log_conversation()

#                 for content in response.content:
#                     if content.type == "tool_use":
#                         tool_name = content.name
#                         tool_args = content.input
#                         tool_use_id = content.id
#                         self.logger.info(
#                             f"Calling tool {tool_name} with args {tool_args}"
#                         )
#                         try:
#                             # Guard against empty tool name and non-dict args
#                             if not tool_name:
#                                 raise ValueError("Empty tool name in tool_use")
#                             if not isinstance(tool_args, dict):
#                                 tool_args = {}

#                             result = await self.session.call_tool(tool_name, tool_args)
#                             self.logger.info(f"Tool {tool_name} result: {result}...")
#                             print("Result:\n", result)
#                             print("Result_content:\n", result.content)
#                             safe_content = self._make_json_safe(getattr(result, "content", None))
#                             self.messages.append(
#                                 {
#                                     "role": "user",
#                                     "content": [
#                                         {
#                                             "type": "tool_result",
#                                             "tool_use_id": tool_use_id,
#                                             "tool_name": tool_name,
#                                             "content": safe_content,
#                                         }
#                                     ],
#                                 }
#                             )
#                             await self.log_conversation()
#                         except Exception as e:
#                             self.logger.error(f"Error calling tool {tool_name}: {e}")
#                             # Feed the error back as a tool_result so the model can recover
#                             self.messages.append(
#                                 {
#                                     "role": "user",
#                                     "content": [
#                                         {
#                                             "type": "tool_result",
#                                             "tool_use_id": tool_use_id,
#                                             "tool_name": tool_name or "",
#                                             "content": {"error": str(e)},
#                                         }
#                                     ],
#                                 }
#                             )
#                             await self.log_conversation()
#                             # Continue the loop without crashing
#                             continue

#             return self.messages

#         except Exception as e:
#             self.logger.error(f"Error processing query: {e}")
#             raise
    
#     # call llm
#     async def call_llm(self):
#         try:
#             print("Calling Gemini LLM")

#             # --- 1. Build Gemini messages from self.messages ---
#             gemini_messages = []
#             for msg in self.messages:
#                 role = "model" if msg["role"] == "assistant" else msg["role"]
#                 content = msg["content"]
#                 parts = []
#                 if isinstance(content, str):
#                     parts.append(content)
#                 elif isinstance(content, list):
#                     for item in content:
#                         if isinstance(item, dict) and item.get("type") == "tool_result":
#                             # Tool response from our tool execution
#                             parts.append({
#                                 "function_response": {
#                                     "name": item.get("tool_name", "tool"),
#                                     "response": item.get("content"),
#                                     "id": item.get("tool_use_id"),
#                                 }
#                             })
#                         else:
#                             parts.append(str(item))
#                             print("Partssss\n",parts)
#                 else:
#                     parts.append(str(content))
#                 gemini_messages.append({"role": role, "parts": parts})
#                 print("G_messages:\n",gemini_messages)

#             # --- 2. Convert MCP tools to Gemini Tool objects ---
#             gemini_tools: list[Tool] = []
#             for t in self.tools:
#                 # Ensure parameters is a dict; if not, coerce to an empty object schema
#                 params = t.get("input_schema") or {}
#                 if not isinstance(params, dict):
#                     params = {"type": "object", "properties": {}}
#                 fd = FunctionDeclaration(
#                     name=t["name"],
#                     description=t["description"],
#                     parameters=params
#                 )
#                 gemini_tools.append(Tool(function_declarations=[fd]))


#             # --- 3. Build kwargs for generate_content ---
#             args = dict(
#                 contents=gemini_messages,
#                 generation_config=genai.types.GenerationConfig(max_output_tokens=1000)
#             )
#             if gemini_tools:  # only pass if non-empty
#                 args["tools"] = gemini_tools

#             # --- 4. Call Gemini in a background thread (non-async function) ---
#             response = await asyncio.to_thread(self.llm.generate_content, **args)

#             # --- 5. Adapt Gemini response to our expected interface ---
#             class ContentObj:
#                 def __init__(self, type_, text=None, name=None, input_=None, id_=None):
#                     self.type = type_
#                     self.text = text
#                     self.name = name
#                     self.input = input_
#                     self.id = id_

#             class SimpleResponse:
#                 def __init__(self, contents):
#                     self.content = contents
#                 def to_dict(self):
#                     out = []
#                     for c in self.content:
#                         if c.type == "text":
#                             out.append({"type": "text", "text": c.text})
#                         elif c.type == "tool_use":
#                             out.append({
#                                 "type": "tool_use",
#                                 "name": c.name,
#                                 "input": c.input,
#                                 "id": c.id,
#                             })
#                     return {"content": out}

#             # --- 6. Parse Gemini parts into ContentObj list ---
#             parts = []
#             candidate = response.candidates[0] if response.candidates else None
#             if candidate and candidate.content and getattr(candidate.content, "parts", None):
#                 for p in candidate.content.parts:
#                     if hasattr(p, "function_call") and p.function_call is not None:
#                         fc = p.function_call
#                         parts.append(ContentObj(
#                             type_="tool_use",
#                             name=getattr(fc, "name", None),
#                             input_=getattr(fc, "args", {}),
#                             id_=getattr(fc, "id", None),
#                         ))
#                     elif hasattr(p, "text") and p.text is not None:
#                         parts.append(ContentObj(type_="text", text=p.text))
#             # Fallback to response.text if nothing structured
#             if not parts:
#                 text = getattr(response, "text", "")
#                 parts = [ContentObj(type_="text", text=text)]

#             return SimpleResponse(parts)

#         except Exception as e:
#             print(f"Error calling Gemini LLM: {e}")
#             raise
#     # cleanup
#     async def cleanup(self):
#         try:
#             await self.exit_stack.aclose()
#             self.logger.info("Disconnected from MCP server")
#         except Exception as e:
#             self.logger.error(f"Error during cleanup: {e}")
#             traceback.print_exc()
#             raise

#     async def log_conversation(self):
#         os.makedirs("conversations", exist_ok=True)

#         serializable_conversation = []

#         for message in self.messages:
#             try:
#                 serializable_message = {"role": message["role"], "content": []}

#                 # Handle both string and list content
#                 if isinstance(message["content"], str):
#                     serializable_message["content"] = message["content"]
#                 elif isinstance(message["content"], list):
#                     for content_item in message["content"]:
#                         if hasattr(content_item, "to_dict"):
#                             serializable_message["content"].append(
#                                 content_item.to_dict()
#                             )
#                         elif hasattr(content_item, "dict"):
#                             serializable_message["content"].append(content_item.dict())
#                         elif hasattr(content_item, "model_dump"):
#                             serializable_message["content"].append(
#                                 content_item.model_dump()
#                             )
#                         else:
#                             serializable_message["content"].append(content_item)

#                 serializable_conversation.append(serializable_message)
#             except Exception as e:
#                 self.logger.error(f"Error processing message: {str(e)}")
#                 self.logger.debug(f"Message content: {message}")
#                 raise

#         timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#         filepath = os.path.join("conversations", f"conversation_{timestamp}.json")

#         try:
#             with open(filepath, "w") as f:
#                 json.dump(serializable_conversation, f, indent=2, default=str)
#         except Exception as e:
#             self.logger.error(f"Error writing conversation to file: {str(e)}")
#             self.logger.debug(f"Serializable conversation: {serializable_conversation}")
#             raise




# Import necessary libraries
import asyncio  # For handling asynchronous operations
import os       # For environment variable access
import sys      # For system-specific parameters and functions
import json     # For handling JSON data (used when printing function declarations)

# Import MCP client components
from typing import Optional  # For type hinting optional values
from contextlib import AsyncExitStack  # For managing multiple async tasks
from mcp import ClientSession, StdioServerParameters  # MCP session management
from mcp.client.stdio import stdio_client  # MCP client for standard I/O communication

# Import Google's Gen AI SDK
from google import genai
from google.genai import types
from google.genai.types import Tool, FunctionDeclaration
from google.genai.types import GenerateContentConfig

from dotenv import load_dotenv  # For loading API keys from a .env file

# Load environment variables from .env file
load_dotenv(r"C:\Users\lenovo\Desktop\MCP\YT\Server\Trail1\api\.env")

class MCPClient:
    def __init__(self):
        """Initialize the MCP client and configure the Gemini API."""
        self.session: Optional[ClientSession] = None  # MCP session for communication
        self.exit_stack = AsyncExitStack()  # Manages async resource cleanup

        # Retrieve the Gemini API key from environment variables
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found. Please add it to your .env file.")

        # Configure the Gemini AI client
        self.genai_client = genai.Client(api_key=gemini_api_key)

    async def connect_to_server(self, server_script_path: str):
        """Connect to the MCP server and list available tools."""

        # Determine whether the server script is written in Python or JavaScript
        # This allows us to execute the correct command to start the MCP server
        command = "python" if server_script_path.endswith('.py') else "node"

        # Define the parameters for connecting to the MCP server
        server_params = StdioServerParameters(command=command, args=[server_script_path])

        # Establish communication with the MCP server using standard input/output (stdio)
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))

        # Extract the read/write streams from the transport object
        self.stdio, self.write = stdio_transport

        # Initialize the MCP client session, which allows interaction with the server
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        # Send an initialization request to the MCP server
        await self.session.initialize()

        # Request the list of available tools from the MCP server
        response = await self.session.list_tools()
        tools = response.tools  # Extract the tool list from the response

        # Print a message showing the names of the tools available on the server
        print("\nConnected to server with tools:", [tool.name for tool in tools])

        # Convert MCP tools to Gemini format
        self.function_declarations = convert_mcp_tools_to_gemini(tools)


    async def process_query(self, query: str) -> str:
        """
        Process a user query using the Gemini API and execute tool calls if needed.

        Args:
            query (str): The user's input query.

        Returns:
            str: The response generated by the Gemini model.
        """

        # Format user input as a structured Content object for Gemini
        user_prompt_content = types.Content(
            role='user',  # Indicates that this is a user message
            parts=[types.Part.from_text(text=query)]  # Convert the text query into a Gemini-compatible format
        )

        # Send user input to Gemini AI and include available tools for function calling
        response = self.genai_client.models.generate_content(
            model='gemini-2.0-flash-001',  # Specifies which Gemini model to use
            contents=[user_prompt_content],  # Send user input to Gemini
            config=types.GenerateContentConfig(
                tools=self.function_declarations,  # Pass the list of available MCP tools for Gemini to use
            ),
        )

        # Initialize variables to store final response text and assistant messages
        final_text = []  # Stores the final formatted response
        assistant_message_content = []  # Stores assistant responses

        # Process the response received from Gemini
        for candidate in response.candidates:
            if candidate.content.parts:  # Ensure response has content
                for part in candidate.content.parts:
                    if isinstance(part, types.Part):  # Check if part is a valid Gemini response unit
                        if part.function_call:  # If Gemini suggests a function call, process it
                            # Extract function call details
                            function_call_part = part  # Store the function call response
                            tool_name = function_call_part.function_call.name  # Name of the MCP tool Gemini wants to call
                            tool_args = function_call_part.function_call.args  # Arguments required for the tool execution

                            # Print debug info: Which tool is being called and with what arguments
                            print(f"\n[Gemini requested tool call: {tool_name} with args {tool_args}]")

                            # Execute the tool using the MCP server
                            try:
                                result = await self.session.call_tool(tool_name, tool_args)  # Call MCP tool with arguments
                                function_response = {"result": result.content}  # Store the tool's output
                            except Exception as e:
                                function_response = {"error": str(e)}  # Handle errors if tool execution fails

                            # Format the tool response for Gemini in a way it understands
                            function_response_part = types.Part.from_function_response(
                                name=tool_name,  # Name of the function/tool executed
                                response=function_response  # The result of the function execution
                            )

                            # Structure the tool response as a Content object for Gemini
                            function_response_content = types.Content(
                                role='tool',  # Specifies that this response comes from a tool
                                parts=[function_response_part]  # Attach the formatted response part
                            )

                            # Send tool execution results back to Gemini for processing
                            response = self.genai_client.models.generate_content(
                                model='gemini-2.0-flash-001',  # Use the same model
                                contents=[
                                    user_prompt_content,  # Include original user query
                                    function_call_part,  # Include Gemini's function call request
                                    function_response_content,  # Include tool execution result
                                ],
                                config=types.GenerateContentConfig(
                                    tools=self.function_declarations,  # Provide the available tools for continued use
                                ),
                            )

                            # Extract final response text from Gemini after processing the tool call
                            final_text.append(response.candidates[0].content.parts[0].text)
                        else:
                            # If no function call was requested, simply add Gemini's text response
                            final_text.append(part.text)

        # Return the combined response as a single formatted string
        return "\n".join(final_text)


    async def chat_loop(self):
        """Run an interactive chat session with the user."""
        print("\nMCP Client Started! Type 'quit' to exit.")

        while True:
            query = input("\nQuery: ").strip()
            if query.lower() == 'quit':
                break

            # Process the user's query and display the response
            response = await self.process_query(query)
            print("\n" + response)

    async def cleanup(self):
        """Clean up resources before exiting."""
        await self.exit_stack.aclose()

def clean_schema(schema):
    """
    Recursively removes 'title' fields from the JSON schema.

    Args:
        schema (dict): The schema dictionary.

    Returns:
        dict: Cleaned schema without 'title' fields.
    """
    if isinstance(schema, dict):
        schema.pop("title", None)  # Remove title if present

        # Recursively clean nested properties
        if "properties" in schema and isinstance(schema["properties"], dict):
            for key in schema["properties"]:
                schema["properties"][key] = clean_schema(schema["properties"][key])

    return schema

def convert_mcp_tools_to_gemini(mcp_tools):
    """
    Converts MCP tool definitions to the correct format for Gemini API function calling.

    Args:
        mcp_tools (list): List of MCP tool objects with 'name', 'description', and 'inputSchema'.

    Returns:
        list: List of Gemini Tool objects with properly formatted function declarations.
    """
    gemini_tools = []

    for tool in mcp_tools:
        # Ensure inputSchema is a valid JSON schema and clean it
        parameters = clean_schema(tool.inputSchema)

        # Construct the function declaration
        function_declaration = FunctionDeclaration(
            name=tool.name,
            description=tool.description,
            parameters=parameters  # Now correctly formatted
        )

        # Wrap in a Tool object
        gemini_tool = Tool(function_declarations=[function_declaration])
        gemini_tools.append(gemini_tool)

    return gemini_tools



async def main():
    """Main function to start the MCP client."""
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        # Connect to the MCP server and start the chat loop
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        # Ensure resources are cleaned up
        await client.cleanup()

if __name__ == "__main__":
    # Run the main function within the asyncio event loop
    asyncio.run(main())

