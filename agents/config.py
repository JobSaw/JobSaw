"""
config -- Environment loading and shared LLM factory.

Provides a single factory function to create a configured
ChatOllama instance backed by a locally-running Ollama server.
"""

from langchain_ollama import ChatOllama

# Model selection: qwen2.5:7b is a strong local model for
# structured extraction tasks via Ollama.
MODEL_NAME = "qwen2.5:7b"


def get_llm(temperature: float = 0.0) -> ChatOllama:
    """Return a configured Ollama chat model instance.

    Args:
        temperature: Sampling temperature. Defaults to 0 for deterministic
                     extraction results.

    Returns:
        ChatOllama instance ready for chain composition.
    """
    return ChatOllama(
        model=MODEL_NAME,
        temperature=temperature,
    )
