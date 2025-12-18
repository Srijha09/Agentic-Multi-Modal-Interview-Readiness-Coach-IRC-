"""
LLM initialization and utilities for LangChain integration.
"""
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

try:
    from langchain_ollama import ChatOllama
except ImportError:
    ChatOllama = None  # Optional dependency

from app.core.config import settings


def get_llm() -> BaseChatModel:
    """
    Initialize and return the appropriate LLM based on configuration.
    
    Returns:
        BaseChatModel: Configured LLM instance
    """
    provider = settings.LLM_PROVIDER.lower()
    model = settings.LLM_MODEL
    
    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment")
        return ChatOpenAI(
            model=model,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.0,  # Deterministic for skill extraction
        )
    elif provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")
        return ChatAnthropic(
            model=model,
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=0.0,
        )
    elif provider == "ollama":
        if ChatOllama is None:
            raise ValueError("langchain-ollama not installed. Install with: pip install langchain-ollama")
        return ChatOllama(
            model=model,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.0,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def get_llm_with_temperature(temperature: float = 0.7) -> BaseChatModel:
    """
    Get LLM with custom temperature (useful for creative tasks).
    
    Args:
        temperature: Temperature setting (0.0 = deterministic, 1.0 = creative)
    
    Returns:
        BaseChatModel: Configured LLM instance
    """
    provider = settings.LLM_PROVIDER.lower()
    model = settings.LLM_MODEL
    
    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment")
        return ChatOpenAI(
            model=model,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature,
        )
    elif provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")
        return ChatAnthropic(
            model=model,
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=temperature,
        )
    elif provider == "ollama":
        if ChatOllama is None:
            raise ValueError("langchain-ollama not installed. Install with: pip install langchain-ollama")
        return ChatOllama(
            model=model,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=temperature,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

