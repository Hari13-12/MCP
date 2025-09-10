# Weather & TaskManager
## Client - Gemini LLM, Server - Custom MCP

Create the MCP server code with tools
In terminal:
- uv init weather
- uv venv
- ./.venv/Scripts/activate
- uv add "mcp[client]" pandas openpyxl httpx


Create a client code to send input to server. In client give the server code path correctly.

Run the app with:
- python client.py <path to server.py>


