from langchain_groq import ChatGroq
from .config import GROQ_API_KEY, GROQ_MODEL

def get_llm():
    return ChatGroq(model=GROQ_MODEL, temperature=0.3, api_key=GROQ_API_KEY)
