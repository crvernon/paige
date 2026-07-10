"""Pydantic AI agent layer.

All LLM interactions run through Pydantic AI using an OpenAI-compatible
endpoint. The endpoint requires an explicit base URL (``OPENAI_BASE_URL``),
which replaces the previous Azure-hosted deployments.

Two flavours of generation are supported:

* :func:`generate_text` for free-form string responses.
* :func:`generate_structured` for typed structured outputs
  (:class:`~highlight.utils.ApproachPoints` / :class:`~highlight.utils.ImpactPoints`).

Both accept an optional per-request ``api_key`` / ``base_url`` / ``model`` so
users may supply their own OpenAI credentials in place of the ``.env`` defaults.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Type, TypeVar

from pydantic import BaseModel
from pydantic_ai import Agent

# Pydantic AI renamed ``OpenAIModel`` to ``OpenAIChatModel`` in newer releases.
# Import whichever is available so the backend works across versions.
try:  # newer pydantic-ai
    from pydantic_ai.models.openai import OpenAIChatModel as _OpenAIModel
except ImportError:  # older pydantic-ai
    from pydantic_ai.models.openai import OpenAIModel as _OpenAIModel

from pydantic_ai.providers.openai import OpenAIProvider

import highlight.prompts as prompts
from .config import get_settings

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class LLMConfig:
    """Resolved credentials for a single generation call."""

    api_key: str
    base_url: str
    model: str


def resolve_config(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMConfig:
    """Merge user-supplied overrides with the ``.env`` defaults."""
    settings = get_settings()
    return LLMConfig(
        api_key=api_key or settings.openai_api_key,
        base_url=base_url or settings.openai_base_url,
        model=model or settings.openai_model,
    )


def _build_model(config: LLMConfig):
    """Construct an OpenAI-compatible model bound to a custom base URL."""
    provider = OpenAIProvider(base_url=config.base_url, api_key=config.api_key)
    return _OpenAIModel(config.model, provider=provider)


def generate_text(
    user_prompt: str,
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    system_prompt: str = prompts.SYSTEM_SCOPE,
) -> str:
    """Generate a free-form text response for ``user_prompt``."""
    config = resolve_config(api_key, base_url, model)
    agent: Agent[None, str] = Agent(
        _build_model(config),
        system_prompt=system_prompt,
    )
    result = agent.run_sync(user_prompt)
    return str(result.output).strip()


def generate_structured(
    user_prompt: str,
    output_type: Type[T],
    *,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    system_prompt: str = prompts.SYSTEM_SCOPE,
) -> T:
    """Generate a typed structured response validated against ``output_type``."""
    config = resolve_config(api_key, base_url, model)
    agent: Agent[None, T] = Agent(
        _build_model(config),
        output_type=output_type,
        system_prompt=system_prompt,
    )
    result = agent.run_sync(user_prompt)
    return result.output


def verify_credentials(
    api_key: str,
    base_url: str,
    model: Optional[str] = None,
) -> bool:
    """Best-effort validation that a set of credentials can build a model.

    A network round-trip is intentionally avoided here; we simply ensure the
    provider/model can be constructed. Real failures surface on first use.
    """
    try:
        config = resolve_config(api_key, base_url, model)
        _build_model(config)
        return bool(config.api_key and config.base_url)
    except Exception:  # noqa: BLE001
        return False
