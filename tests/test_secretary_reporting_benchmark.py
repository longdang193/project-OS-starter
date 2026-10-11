from scripts.benchmark_secretary_reporting import run_benchmark


def test_reporting_benchmark_emits_sanitized_comparable_metrics() -> None:
    result = run_benchmark(phase="final", repetitions=1, history_sizes=[0, 5])

    assert result["schema_version"] == "secretary-reporting-benchmark-v1"
    assert result["workload"]["history_sizes"] == [0, 5]
    assert len(result["trials"]) == 2
    for trial in result["trials"]:
        assert trial["query_count"] >= 1
        assert trial["selected_rows"] == 2
        assert trial["validated_rows"] == 2
        assert trial["excluded_rows"] == 0
        assert trial["dispositions"] == ["observed_window"]
        assert set(trial["database_inspection"]["indexes"]) == {"requestDetails", "usageHistory"}
        assert trial["database_inspection"]["query_plan"]


def test_reporting_benchmark_rejects_invalid_controls() -> None:
    try:
        run_benchmark(phase="final", repetitions=0, history_sizes=[0])
    except ValueError as exc:
        assert "repetitions" in str(exc)
    else:
        raise AssertionError("invalid benchmark controls must be rejected")
