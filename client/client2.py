from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
import json
from langchain_core.prompts import ChatPromptTemplate
import time
import os
from dotenv import load_dotenv
import sys
from pathlib import Path
import asyncio



INSTRUCTION_PROMPT = """You are an orchestration agent. 
Your job is ONLY to use the available MCP tools to answer the user.
- Never invent or answer hypothetically.
- If the information cannot be obtained via a tool or shows error due to insufficient parameters and required few parameters to fetch the data
then ask the user to provide missing parameters.
- You have to run the tools in any case
"""

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# env_path = Path('.env') 
# load_dotenv(dotenv_path=env_path, override=True)
LLM_endpoint = os.getenv("http://localhost:11434")
MODEL_NAME='llama3.2:3b'

async def main(prompt: str):
    start_time=time.time()
    # Load MCP servers
    client = MultiServerMCPClient({
        "Archive": {
            "command": "python3",
            "args": ['/home/bharat-nobel/Documents/MCP/Server/mcpServer.py'],
            "transport": "stdio",
        }
    })
    

    try:
        tools = await client.get_tools()
    except Exception as e:
        print("Failed to load MCP tools:", e)
        return {"status": "error", "message": str(e)}

    # Plug external Ollama model into LangChain
    model = ChatOllama(
        model=MODEL_NAME,
        base_url=LLM_endpoint,  # Remove /api/chat
        temperature=0.5
)
    # Create ReAct agent with tools
    system_prompt = ChatPromptTemplate.from_messages([
    ("system", INSTRUCTION_PROMPT),
    ("user", prompt)
])
    constrained_model = model.with_config({"prompt": system_prompt})
    agent = create_react_agent(constrained_model, tools)

    # Run with prompt
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": prompt}]}
    )

    try:
        # tool_content = next((m.content for m in result["messages"] if getattr(m, 'type', None) == "tool"), None)
        
        # # 2. Extract string if content is a list like [{'type': 'text', 'text': '...'}]
        # if isinstance(tool_content, list) and len(tool_content) > 0:
        #     raw_str = tool_content[0].get('text', '{}')

        # else:
        #     raw_str = tool_content
        raw_str=result
            
        ans = json.loads(raw_str) if raw_str else {"error": "No tool content found"}
    except Exception as e:
        print ("Exception: ",e)
        ans=result['messages']
    end_time=time.time()
    print("time_taken", end_time-start_time)
    return ans 
    
prompt="""give me all job list"""
ans=asyncio.run(main(prompt))
# for key,val in ans.items():
#     print(key,val)
print(ans)
