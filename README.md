# TaskManager
## Client - Claude Server, Server - Custom MCP



While creating a MCP server for the first time install uv using
- powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex     # windows
- curl -LsSf https://astral.sh/uv/install.sh | sh     # macOS/Linux


Create the MCP server code with tools
Open terminal:
- uv init weather
- uv venv
- ./.venv/Scripts/activate
- uv add mcp[cli] httpx
- new-item weather.py


After the server is created, open the "claude_desktop_config.json" file by using
- code $env:AppData\Claude\claude_desktop_config.json

edit the above config file with created MCP server
``` json
{
  "mcpServers":{
    "weather":{
      "command":"C:\\Users\\lenovo\\.local\\bin\\uv.EXE",      # give the installed uv path
      "args":[
        "--directory",
        "C:\\Users\\lenovo\\Desktop\\MCP\\MCP-Git\\weather",     # give the created server folder
        "run",
        "weather.py"
      ]
    }
  }
}
``` 

Close and open the claude desktop





