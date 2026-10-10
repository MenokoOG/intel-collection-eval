"""The one place that talks to the Claude API. Everything else calls this."""

from __future__ import annotations

import os
from typing import TypeVar

from pydantic import BaseModel

MODEL_ENV = "ICE_MODEL"
DEFAULT_MODEL = "claude-opus-5"
MAX_TOKENS = 16000

Parsed = TypeVar("Parsed", bound=BaseModel)
Message = dict[str, str]


class LlmError(Exception):
    """The model call failed, was declined, or came back unusable."""


def model_name(override_env: str) -> str:
    """Model for one role. A role variable wins over ICE_MODEL, which wins over the default."""
    return os.environ.get(override_env) or os.environ.get(MODEL_ENV) or DEFAULT_MODEL


def _client() -> object:
    try:
        import anthropic
    except ImportError as exc:
        raise LlmError('the "llm" extra is not installed: pip install ".[llm]"') from exc
    return anthropic.Anthropic()


def _guard(call: object) -> object:
    """Run a zero-argument SDK call and turn SDK failures into LlmError."""
    import anthropic

    try:
        return call()  # type: ignore[operator]
    except anthropic.AuthenticationError as exc:
        raise LlmError("no valid Claude API credential found") from exc
    except anthropic.RateLimitError as exc:
        raise LlmError("rate limited after retries") from exc
    except anthropic.APIStatusError as exc:
        raise LlmError(f"API error {exc.status_code}: {exc.message}") from exc
    except anthropic.APIConnectionError as exc:
        raise LlmError("could not reach the Claude API") from exc


def _check_stop(response: object) -> None:
    reason = getattr(response, "stop_reason", None)
    if reason == "refusal":
        raise LlmError("the model declined this request")
    if reason == "max_tokens":
        raise LlmError("the model ran out of output tokens")


def complete(model: str, system: str, messages: list[Message]) -> str:
    """One text completion. Raises LlmError on any failure, including a decline."""
    client = _client()
    response = _guard(
        lambda: client.messages.create(  # type: ignore[attr-defined]
            model=model,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=messages,
        )
    )
    _check_stop(response)
    text = "".join(
        block.text
        for block in response.content  # type: ignore[attr-defined]
        if block.type == "text"
    )
    if not text.strip():
        raise LlmError("the model returned no text")
    return text


def parse(model: str, system: str, user: str, shape: type[Parsed]) -> Parsed:
    """One completion validated against a pydantic shape."""
    client = _client()
    response = _guard(
        lambda: client.messages.parse(  # type: ignore[attr-defined]
            model=model,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_format=shape,
        )
    )
    _check_stop(response)
    parsed = getattr(response, "parsed_output", None)
    if not isinstance(parsed, shape):
        raise LlmError("the model reply did not match the expected shape")
    return parsed
