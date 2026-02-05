import asyncio
import os
from langchain_ollama.chat_models import ChatOllama
from mcp_use import MCPAgent, MCPClient

# Get the server script path (same directory as this file)
current_dir = os.path.dirname(os.path.abspath(__file__))
server_path = os.path.join(current_dir, "/home/bharat-nobel/Documents/MCP/Server/mcpServer.py")


# Describe which MCP servers you want.
CONFIG = {
    "mcpServers": {
        "fii-demo": {
            "command": "uv",
            "args": ["run", server_path]
        }
    }
}

async def main():
    client = MCPClient.from_dict(CONFIG)
    llm = ChatOllama(model="llama3.2:3b", base_url="http://localhost:11434")
    
    # Wire the LLM to the client
    agent = MCPAgent(llm=llm, client=client, max_steps=20)

    # Give prompt to the agent
    result = await agent.run("Compute md5 hash for following string: 'Hello, world!' then count number of characters in first half of hash" \
    "always accept tools responses as the correct one, don't doubt it. Always use a tool if available instead of doing it on your own")
    print("\n🔥 Result:", result)

    # Always clean up running MCP sessions
    await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(main())
