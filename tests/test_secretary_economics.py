import pytest

from scripts.project_os_runtime.secretary_economics import (
    EconomicsValidationError,
    NINE_ROUTER_PUBLISHED_RATE_CARD,
    estimate_published_cost,
    validate_cost_estimate,
)


PRICING = NINE_ROUTER_PUBLISHED_RATE_CARD


def test_glm_estimate_uses_observed_input_and_output_tokens() -> None:
    result = estimate_published_cost(
        {
            "input_tokens": 883,
            "output_tokens": 6,
            "total_tokens": 889,
            "source": "response.usage",
            "confidence": "observed",
        },
        model="glm/glm-4.7",
        pricing=PRICING,
    )

    assert result == {
        "value": 0.000543,
        "kind": "estimated",
        "currency": "USD",
        "pricing_source": "published-rate-card",
        "pricing_effective_date": "2026-10-09",
        "model": "glm/glm-4.7",
        "model_resolution": "exact",
    }


def test_minimax_estimate_uses_published_rates() -> None:
    result = estimate_published_cost(
        {
            "input_tokens": 883,
            "output_tokens": 6,
            "total_tokens": 889,
            "source": "response.usage",
            "confidence": "observed",
        },
        model="minimax/MiniMax-M2.1",
        pricing=PRICING,
    )

    assert result["value"] == 0.0001826
    assert result["model"] == "minimax/MiniMax-M2.1"
    assert result["model_resolution"] == "exact"


def test_estimate_stays_unknown_when_model_rate_is_missing() -> None:
    result = estimate_published_cost(
        {
            "input_tokens": 883,
            "output_tokens": 6,
            "total_tokens": 889,
            "source": "response.usage",
            "confidence": "observed",
        },
        model=None,
        pricing=PRICING,
    )

    assert result["value"] == "unknown"
    assert result["reason"] == "model_rate_unavailable"


def test_combo_model_stays_unknown_without_downstream_attribution() -> None:
    result = estimate_published_cost(
        {
            "input_tokens": 883,
            "output_tokens": 6,
            "total_tokens": 889,
            "source": "response.usage",
            "confidence": "observed",
        },
        model="combo-normal",
        pricing=PRICING,
    )

    assert result["value"] == "unknown"
    assert result["reason"] == "model_rate_unavailable"


def test_unknown_estimate_remains_valid_without_model_attribution() -> None:
    result = estimate_published_cost(
        {
            "input_tokens": 883,
            "output_tokens": 6,
            "total_tokens": 889,
            "source": "response.usage",
            "confidence": "observed",
        },
        model=None,
        pricing=PRICING,
    )

    assert validate_cost_estimate(result)["value"] == "unknown"


def test_estimate_rejects_inconsistent_token_total() -> None:
    with pytest.raises(EconomicsValidationError, match="total_tokens"):
        estimate_published_cost(
            {
                "input_tokens": 883,
                "output_tokens": 6,
                "total_tokens": 900,
                "source": "response.usage",
                "confidence": "observed",
            },
            model="glm/glm-4.7",
            pricing=PRICING,
        )


def test_estimate_rejects_non_finite_rates() -> None:
    pricing = {**PRICING, "models": {"glm/glm-4.7": {
        "input_usd_per_million": "NaN",
        "output_usd_per_million": 2.0,
    }}}

    with pytest.raises(EconomicsValidationError, match="input_usd_per_million"):
        estimate_published_cost(
            {
                "input_tokens": 883,
                "output_tokens": 6,
                "total_tokens": 889,
                "source": "response.usage",
                "confidence": "observed",
            },
            model="glm/glm-4.7",
            pricing=pricing,
        )


def test_cached_tokens_require_explicit_cache_rate() -> None:
    result = estimate_published_cost(
        {
            "input_tokens": 1_000,
            "output_tokens": 100,
            "total_tokens": 1_100,
            "cache_read_input_tokens": 800,
            "source": "response.usage",
            "confidence": "observed",
        },
        model="glm/glm-4.7",
        pricing=PRICING,
    )

    assert result["value"] == "unknown"
    assert result["reason"] == "cache_read_rate_unavailable"


def test_cached_tokens_use_separate_rates_when_published() -> None:
    pricing = {
        **PRICING,
        "models": {
            "glm/glm-4.7": {
                "input_usd_per_million": 1.0,
                "cache_read_usd_per_million": 0.1,
                "cache_write_usd_per_million": 0.5,
                "output_usd_per_million": 2.0,
            }
        },
    }
    result = estimate_published_cost(
        {
            "input_tokens": 1_000,
            "output_tokens": 100,
            "total_tokens": 1_100,
            "cache_read_input_tokens": 800,
            "cache_write_input_tokens": 100,
            "source": "response.usage",
            "confidence": "observed",
        },
        model="glm/glm-4.7",
        pricing=pricing,
    )

    assert result["value"] == 0.00043
