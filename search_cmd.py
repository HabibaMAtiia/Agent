import subprocess
import chainlit as cl
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_tavily import TavilySearch  # Search tool wrapper

# --- 1️⃣ CMD Tool ---
@tool
def cmd_tool(text: str) -> str:
    """Run Windows CMD commands."""
    result = subprocess.run(
        ["cmd", "/c", text],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return f"❌ Error:\n{result.stderr.strip()}"

# --- 2️⃣ Search Tool ---
search_tool = TavilySearch(
    max_results=3,                     # number of results to retrieve
    tavily_api_key="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"  # replace with your key
)

# --- 3️⃣ Initialize Agent ---
memory = MemorySaver()
model = init_chat_model(
    model="gemini-2.5-flash",
    model_provider="google_genai",
    api_key="AIzaSyChBOk7xWNPUqLGZ9H9LoLiPqxmDPT7nuI"
)

tools = [cmd_tool, search_tool]
agent_executor = create_react_agent(model, tools, checkpointer=memory)

config = {"configurable": {"thread_id": "session_001"}}  # default session

# --- 4️⃣ Chainlit message handler ---
@cl.on_message
async def main(message: cl.Message):
    input_message = {"role": "user", "content": message.content}
    msg = cl.Message(content="")

    # Stream the agent output
    for step, metadata in agent_executor.stream(
    {"messages": [input_message]}, config, stream_mode="messages"
):
        if metadata["langgraph_node"] == "agent" and (text := step.text()):

            await msg.stream_token(step.text())

    # Send final concatenated output (optional)
    await msg.update()
