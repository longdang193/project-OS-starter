from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping


class EconomicsValidationError(ValueError):
    pass


NINE_ROUTER_PUBLISHED_RATE_CARD: dict[str, Any] = {
    "provider": "9router",
    "currency": "USD",
    "source": "published-rate-card",
    "source_url": "https://github.com/decolua/9router/blob/master/gitbook/content/en/providers/subscription.md",
    "effective_date": "2026-10-09",
    "display_semantics": "estimated reference cost",
    "models": {
        "glm/glm-4.7": {
            "input_usd_per_million": 0.60,
            "cache_read_usd_per_million": None,
            "cache_write_usd_per_million": None,
            "output_usd_per_million": 2.20,
        },
        "minimax/MiniMax-M2.1": {
            "input_usd_per_million": 0.20,
            "cache_read_usd_per_million": None,
            "cache_write_usd_per_million": None,
            "output_usd_per_million": 1.00,
        },
    },
}


def _decimal(value: Any, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise EconomicsValidationError(f"{label} must be non-negative number")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise EconomicsValidationError(f"{label} must be non-negative number") from exc
    if not result.is_finite() or result < 0:
        raise EconomicsValidationError(f"{label} must be non-negative number")
    return result


def _tokens(usage: Mapping[str, Any]) -> tuple[int, int, int]:
    values = {}
    for field in ("input_tokens", "output_tokens", "total_tokens"):
        value = usage.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise EconomicsValidationError(f"{field} must be non-negative integer")
        values[field] = value
    for field in ("cache_read_input_tokens", "cache_write_input_tokens"):
        value = usage.get(field, 0)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise EconomicsValidationError(f"{field} must be non-negative integer")
        values[field] = value
    if values["cache_read_input_tokens"] + values["cache_write_input_tokens"] > values["input_tokens"]:
        raise EconomicsValidationError("cached input tokens must not exceed input_tokens")
    if values["input_tokens"] + values["output_tokens"] != values["total_tokens"]:
        raise EconomicsValidationError("total_tokens must equal input_tokens + output_tokens")
    return values["input_tokens"], values["output_tokens"], values["total_tokens"]


def normalize_response_usage(value: object) -> object:
    if value == "unknown":
        return value
    if not isinstance(value, Mapping):
        raise EconomicsValidationError("token usage must be number, object, or unknown")
    if "source" in value or "confidence" in value:
        return dict(value)

    prompt_details = value.get("prompt_tokens_details")
    input_details = value.get("input_tokens_details")
    if not isinstance(prompt_details, Mapping):
        prompt_details = {}
    if not isinstance(input_details, Mapping):
        input_details = {}

    raw_fields = {
        "input_tokens": value.get("prompt_tokens", value.get("input_tokens")),
        "output_tokens": value.get("completion_tokens", value.get("output_tokens")),
        "total_tokens": value.get("total_tokens"),
        "cache_read_input_tokens": value.get(
            "cached_tokens",
            value.get(
                "cache_read_input_tokens",
                prompt_details.get("cached_tokens", input_details.get("cached_tokens")),
            ),
        ),
        "cache_write_input_tokens": value.get(
            "cache_creation_input_tokens",
            value.get("cache_write_input_tokens"),
        ),
    }
    if not any(
        field in value
        for field in (
            "prompt_tokens",
            "completion_tokens",
            "input_tokens",
            "output_tokens",
            "cached_tokens",
            "cache_creation_input_tokens",
            "input_tokens_details",
        )
    ):
        raise EconomicsValidationError("token usage must identify observed response usage")
    if raw_fields["total_tokens"] is None and all(
        isinstance(raw_fields[field], int) and not isinstance(raw_fields[field], bool)
        for field in ("input_tokens", "output_tokens")
    ):
        raw_fields["total_tokens"] = raw_fields["input_tokens"] + raw_fields["output_tokens"]
    normalized = {
        field: raw_fields[field]
        for field in ("input_tokens", "output_tokens", "total_tokens")
    }
    for field in ("cache_read_input_tokens", "cache_write_input_tokens"):
        if raw_fields[field] is not None:
            normalized[field] = raw_fields[field]
    normalized.update({"source": "response.usage", "confidence": "observed"})
    return normalized


def validate_token_usage(value: object) -> object:
    if value == "unknown":
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        if isinstance(value, float) and not Decimal(str(value)).is_finite():
            raise EconomicsValidationError("token usage must be finite")
        return value
    normalized = normalize_response_usage(value)
    if not isinstance(normalized, Mapping):
        raise EconomicsValidationError("token usage must be number, object, or unknown")
    input_tokens, output_tokens, total_tokens = _tokens(normalized)
    if normalized.get("source") != "response.usage" or normalized.get("confidence") != "observed":
        raise EconomicsValidationError("token usage must identify observed response usage")
    result = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "source": "response.usage",
        "confidence": "observed",
    }
    for field in ("cache_read_input_tokens", "cache_write_input_tokens"):
        if field in normalized:
            result[field] = normalized[field]
    return result


def validate_cost_estimate(value: object) -> object:
    if value == "unknown":
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        if isinstance(value, float) and not Decimal(str(value)).is_finite():
            raise EconomicsValidationError("cost must be finite")
        return value
    if not isinstance(value, Mapping):
        raise EconomicsValidationError("cost must be number, object, or unknown")
    numeric_value = value.get("value")
    if numeric_value == "unknown":
        reason = value.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise EconomicsValidationError("cost unknown reason must be non-empty text")
        return {"value": "unknown", "reason": reason.strip()}
    if isinstance(numeric_value, bool) or not isinstance(numeric_value, (int, float)) or numeric_value < 0:
        raise EconomicsValidationError("cost.value must be non-negative number")
    if isinstance(numeric_value, float) and not Decimal(str(numeric_value)).is_finite():
        raise EconomicsValidationError("cost.value must be finite")
    for field in ("currency", "pricing_source", "pricing_effective_date", "model"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise EconomicsValidationError(f"cost.{field} must be non-empty text")
    if value.get("kind") != "estimated":
        raise EconomicsValidationError("cost.kind must be estimated")
    if value.get("model_resolution") not in {"exact", "requested", "scenario"}:
        raise EconomicsValidationError("cost.model_resolution invalid")
    return {
        "value": numeric_value,
        "kind": "estimated",
        "currency": value["currency"],
        "pricing_source": value["pricing_source"],
        "pricing_effective_date": value["pricing_effective_date"],
        "model": value["model"],
        "model_resolution": value["model_resolution"],
    }


def estimate_published_cost(
    usage: Mapping[str, Any],
    *,
    model: str | None,
    pricing: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(usage, Mapping):
        raise EconomicsValidationError("token usage must be an object")
    validated_usage = validate_token_usage(usage)
    input_tokens, output_tokens, _ = _tokens(validated_usage)
    cache_read_tokens = validated_usage.get("cache_read_input_tokens", 0)
    cache_write_tokens = validated_usage.get("cache_write_input_tokens", 0)
    uncached_input_tokens = input_tokens - cache_read_tokens - cache_write_tokens
    currency = pricing.get("currency")
    source = pricing.get("source")
    effective_date = pricing.get("effective_date")
    if not all(isinstance(value, str) and value.strip() for value in (currency, source, effective_date)):
        raise EconomicsValidationError("pricing metadata must be non-empty text")
    models = pricing.get("models")
    rates = models.get(model) if isinstance(models, Mapping) and isinstance(model, str) else None
    result = {
        "kind": "estimated",
        "currency": currency,
        "pricing_source": source,
        "pricing_effective_date": effective_date,
        "model": model,
        "model_resolution": "exact" if rates is not None else "unknown",
    }
    if not isinstance(rates, Mapping):
        return {"value": "unknown", "reason": "model_rate_unavailable", **result}
    input_rate = _decimal(rates.get("input_usd_per_million"), "input_usd_per_million")
    cache_read_rate = rates.get("cache_read_usd_per_million")
    cache_write_rate = rates.get("cache_write_usd_per_million")
    if cache_read_tokens and cache_read_rate is None:
        return {"value": "unknown", "reason": "cache_read_rate_unavailable", **result}
    if cache_write_tokens and cache_write_rate is None:
        return {"value": "unknown", "reason": "cache_write_rate_unavailable", **result}
    cache_read_rate = _decimal(cache_read_rate, "cache_read_usd_per_million") if cache_read_rate is not None else Decimal(0)
    cache_write_rate = _decimal(cache_write_rate, "cache_write_usd_per_million") if cache_write_rate is not None else Decimal(0)
    output_rate = _decimal(rates.get("output_usd_per_million"), "output_usd_per_million")
    cost = (
        Decimal(uncached_input_tokens) * input_rate
        + Decimal(cache_read_tokens) * cache_read_rate
        + Decimal(cache_write_tokens) * cache_write_rate
        + Decimal(output_tokens) * output_rate
    ) / Decimal(1_000_000)
    return {"value": float(cost), **result}


__all__ = [
    "EconomicsValidationError",
    "NINE_ROUTER_PUBLISHED_RATE_CARD",
    "estimate_published_cost",
    "normalize_response_usage",
    "validate_cost_estimate",
    "validate_token_usage",
]
