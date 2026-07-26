from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from .llm import get_llm

class TutorState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    context: str

llm = get_llm()
memory = MemorySaver()

SYSTEM = """You are an AI tutor. A student is asking you questions about a YouTube video.
Use the transcript provided as context to answer their questions.
Be helpful, clear, and educational. If the transcript doesn't contain info to answer, say so.
Keep answers concise but thorough."""

def chatbot(state: TutorState):
    msgs = [SystemMessage(content=SYSTEM)]
    if state.get("context"):
        msgs.append(SystemMessage(content=f"Video transcript:\n{state['context']}"))
    msgs.extend(state["messages"])
    response = llm.invoke(msgs)
    return {"messages": [response]}

graph = StateGraph(TutorState)
graph.add_node("chatbot", chatbot)
graph.add_edge(START, "chatbot")
graph.add_edge("chatbot", END)
tutor_graph = graph.compile(checkpointer=memory)

def chat(message: str, thread_id: str, context: str = "") -> str:
    config = {"configurable": {"thread_id": thread_id}}
    result = tutor_graph.invoke(
        {"messages": [("user", message)], "context": context},
        config=config,
    )
    return result["messages"][-1].content
