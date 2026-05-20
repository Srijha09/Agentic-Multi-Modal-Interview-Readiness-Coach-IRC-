"""
LangSmith / LangChain tracing configuration.

Call configure_langsmith_tracing() as early as possible in app startup,
before importing LangChain or LangGraph modules.
"""
import logging
import os
from typing import Any, Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_configured = False


def configure_langsmith_tracing() -> bool:
    """
    Enable LangSmith tracing via LangChain environment variables.

    Returns True if tracing was enabled, False otherwise.
    Safe to call multiple times (idempotent).
    """
    global _configured
    if _configured:
        return is_langsmith_enabled()

    _configured = True

    if not settings.LANGSMITH_TRACING or not settings.LANGSMITH_API_KEY:
        logger.info(
            "LangSmith tracing disabled (set LANGSMITH_TRACING=true and LANGSMITH_API_KEY)"
        )
        return False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

    logger.info("LangSmith tracing enabled for project '%s'", settings.LANGSMITH_PROJECT)
    return True


def is_langsmith_enabled() -> bool:
    """Return whether LangSmith tracing is active."""
    return (
        settings.LANGSMITH_TRACING
        and bool(settings.LANGSMITH_API_KEY)
        and os.environ.get("LANGCHAIN_TRACING_V2") == "true"
    )


def build_run_config(
    run_name: str,
    *,
    user_id: Optional[int] = None,
    tags: Optional[list] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a LangGraph/LangChain invoke config for labeled traces in LangSmith.
    """
    run_tags = ["irc-coach", run_name]
    if user_id is not None:
        run_tags.append(f"user:{user_id}")
    if tags:
        run_tags.extend(tags)

    run_metadata: Dict[str, Any] = {"workflow": run_name}
    if user_id is not None:
        run_metadata["user_id"] = user_id
    if metadata:
        run_metadata.update(metadata)

    config: Dict[str, Any] = {
        "run_name": run_name,
        "tags": run_tags,
        "metadata": run_metadata,
    }

    if user_id is not None:
        config["configurable"] = {"thread_id": f"user-{user_id}"}

    return config
