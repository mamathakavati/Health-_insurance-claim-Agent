
from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings

from app.config import (
    OLLAMA_BASE_URL,
    OLLAMA_CHAT_MODEL,
    OLLAMA_EMBED_MODEL,
)


def get_chat_model():
    """Create the local Ollama chat model."""
    return ChatOllama(
        model=OLLAMA_CHAT_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
    )


def get_embedding_model():
    """Create the local embedding model."""
    return OllamaEmbeddings(
        model=OLLAMA_EMBED_MODEL,
        base_url=OLLAMA_BASE_URL,
    )


if __name__ == "__main__":
    print("Testing local AI connection...")

    llm = get_chat_model()
    response = llm.invoke(
        "Explain health insurance pre-authorization in simple English."
    )

    print("\nAI Response:")
    print(response.content)

    embeddings = get_embedding_model()
    vector = embeddings.embed_query(
        "Health insurance policy coverage"
    )

    print("\nEmbedding test successful!")
    print("Vector length:", len(vector))
