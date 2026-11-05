from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from .llm import get_llm

class TutorState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    context: str
    system: str

llm = get_llm()
memory = MemorySaver()

SYSTEM = """You are an AI tutor for exactly one YouTube video. The only source of truth is the transcript provided with this conversation. Answer strictly from the transcript; do not use outside knowledge.

Rules:
1. If the transcript contains the answer, reply with a concise, educational answer grounded in it. Quote the supporting phrase from the transcript when it helps clarity.
2. If the transcript does not contain the information, reply: "The video doesn't cover that." Optionally add one sentence about what the video does cover. Never guess or fill gaps with outside knowledge.
3. Refuse the same way for opinions, comparisons, personal or financial advice, predictions, and questions about other topics — you only know this video.
4. If no transcript is available, reply: "I don't have the video transcript, so I can't answer that."
5. Stay concise and clear. Never invent names, numbers, dates, or quotes."""

def chatbot(state: TutorState):
    msgs = [SystemMessage(content=state.get("system") or SYSTEM)]
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

def chat(message: str, thread_id: str, context: str = "", system_prompt: str | None = None) -> str:
    config = {"configurable": {"thread_id": thread_id}}
    result = tutor_graph.invoke(
        {
            "messages": [("user", message)],
            "context": context,
            "system": system_prompt or "",
        },
        config=config,
    )
    return result["messages"][-1].content
