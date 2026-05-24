"""Offline-first AI advisory bridge for Phase 3."""

from __future__ import annotations

import json
from pathlib import Path

import keyring

from datawraith.core.exceptions import AIBridgeError
from datawraith.core.types import AISuggestion, ScenarioResult
from datawraith.engine.migration_analysis import migration_suggestions_for_result

SERVICE_NAME = "datawraith"
SUPPORTED_PROVIDERS = {"openai", "anthropic", "google"}


def store_api_key(provider: str, api_key: str) -> None:
    """Store a provider API key in the OS keyring."""
    normalized = _normalize_provider(provider)
    if not api_key.strip():
        raise AIBridgeError("API key cannot be empty")
    try:
        keyring.set_password(SERVICE_NAME, normalized, api_key)
    except Exception as exc:  # pragma: no cover - backend-specific
        raise AIBridgeError(f"Could not store API key in keyring: {exc}") from exc


def has_api_key(provider: str) -> bool:
    """Return whether a provider key exists in the OS keyring."""
    normalized = _normalize_provider(provider)
    try:
        return keyring.get_password(SERVICE_NAME, normalized) is not None
    except Exception:
        return False


def analyze_report(path: Path, provider: str | None = None) -> list[AISuggestion]:
    """Analyze a report with local rules and optional BYOK metadata.

    Phase 3 keeps AI advisory offline-first. The provider flag verifies BYOK
    readiness but does not make network calls yet; rule-based suggestions remain
    the deterministic baseline and are never auto-applied.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        result = ScenarioResult.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise AIBridgeError(f"Could not analyze report {path}: {exc}") from exc

    suggestions = migration_suggestions_for_result(result)
    if provider is None:
        return suggestions

    normalized = _normalize_provider(provider)
    provider_configured = has_api_key(normalized)
    prefix = (
        f"{normalized} key is configured; network AI enrichment is intentionally "
        "deferred in this local Phase 3 slice. "
        if provider_configured
        else f"{normalized} key is not configured; returning offline rule-based advice. "
    )
    return [
        suggestion.model_copy(
            update={
                "provider": normalized if provider_configured else suggestion.provider,
                "reasoning": prefix + suggestion.reasoning,
            }
        )
        for suggestion in suggestions
    ]


def _normalize_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized not in SUPPORTED_PROVIDERS:
        available = ", ".join(sorted(SUPPORTED_PROVIDERS))
        raise AIBridgeError(f"Unsupported AI provider '{provider}'. Available: {available}")
    return normalized
