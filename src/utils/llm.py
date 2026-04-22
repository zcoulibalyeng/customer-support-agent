"""
LLM and embedding factory functions.

Every agent and tool imports from here — never instantiates its own client.
"""

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.utils.config import EMBEDDING_MODEL, LLM_MODEL, LLM_TEMPERATURE, OPENAI_API_KEY


def get_llm(temperature: float | None = None) -> ChatOpenAI:
    return ChatOpenAI(
        model=LLM_MODEL,
        temperature=temperature if temperature is not None else LLM_TEMPERATURE,
        api_key=OPENAI_API_KEY,
    )


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=OPENAI_API_KEY,
    )
