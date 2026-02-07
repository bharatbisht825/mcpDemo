from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
import json
from langchain_core.prompts import ChatPromptTemplate
import time
import os
from dotenv import load_dotenv
import sys
from pathlib import Path
import asyncio
from langchain_core.messages import AIMessage



INSTRUCTION_PROMPT = """You are a data-processing orchestration agent.

STRICT RULES:
1. You MUST call at least one MCP tool.
2. Treat tool output as authoritative JSON data.
3. You MUST explicitly parse and reason over the JSON fields.
4. You MUST filter the data strictly based on the user request.
5. You MUST discard any entries that do not match.
6. You MUST NOT summarize or generalize.
7. Your final answer MUST be derived only from the filtered JSON.
8. If filtering cannot be done due to missing fields, ask the user.
"""

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# env_path = Path('.env') 
# load_dotenv(dotenv_path=env_path, override=True)
LLM_endpoint = os.getenv("http://localhost:11434")
MODEL_NAME='qwen3:4b'

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
    ("system", "First reason over the JSON internally. Then produce the final filtered result."),
    ("user", prompt)
])
    constrained_model = model.with_config({"prompt": system_prompt})
    agent = create_agent(constrained_model, tools)

    # Run with prompt
    # Build a proper prompt with system instructions
    full_prompt = f"""{INSTRUCTION_PROMPT}

    User Query: {prompt}

    IMPORTANT: 
    1. Call the MCP tool to get job listings
    2. Parse the JSON response
    3. Filter jobs according to user prompt.
    5. filter based on brief_description key.
    6. Return ONLY the filtered results

    """
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": full_prompt}]}
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
    
prompt="""give me all node js job list"""
ans=asyncio.run(main(prompt))
# for key,val in ans.items():
#     print(key,val)
# print(ans)
# for msg in ans:
#     print(msg)
#     print("****************************")
for msg in ans:
    if isinstance(msg, AIMessage):
        print(msg.content)
