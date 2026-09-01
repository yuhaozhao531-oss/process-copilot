from process_copilot.leachate_early_warning import (
    BASELINE_DAYS,
    TOTAL_PHOSPHORUS_LIMIT_MG_L,
    build_scenario,
    detect_early_warning,
    generate_series,
)


def test_generation_is_deterministic_given_same_seed() -> None:
    a = generate_series(seed=42)
    b = generate_series(seed=42)
    assert a.series == b.series


def test_different_seeds_produce_different_series() -> None:
    a = generate_series(seed=42)
    b = generate_series(seed=7)
    assert a.series["total_phosphorus_mg_l"] != b.series["total_phosphorus_mg_l"]


def test_baseline_period_stays_below_regulatory_limit() -> None:
    series = generate_series(seed=42)
    baseline_phosphorus = series.series["total_phosphorus_mg_l"][:BASELINE_DAYS]
    assert all(value < TOTAL_PHOSPHORUS_LIMIT_MG_L for value in baseline_phosphorus)


def test_default_seed_triggers_warning_before_breach() -> None:
    """核心假设：先导指标能在总磷泉点超标之前触发预警（报告3.2节"漏洞二"）。"""
    result = build_scenario(seed=42)
    assert result.early_warning.triggered is True
    assert result.early_warning.lead_time_days is not None
    assert result.early_warning.lead_time_days > 0
    assert result.early_warning.warning_variable_id in {
        "membrane_anomaly_score",
        "conductivity_us_cm",
        "slope_displacement_mm",
    }


def test_breach_day_is_first_day_exceeding_limit() -> None:
    series = generate_series(seed=42)
    warning = detect_early_warning(series)
    breach_day = warning.breach_day
    assert breach_day is not None
    phosphorus = series.series["total_phosphorus_mg_l"]
    assert phosphorus[breach_day] > TOTAL_PHOSPHORUS_LIMIT_MG_L
    assert all(value <= TOTAL_PHOSPHORUS_LIMIT_MG_L for value in phosphorus[:breach_day])


def test_flat_series_never_triggers_warning() -> None:
    """没有漂移的平稳序列不应该产生假预警（阈值基于基线自身波动，不是固定常数）。"""
    flat_days = 130
    series = generate_series(seed=1, days=flat_days)
    # 截断到漂移开始之前，构造一段没有漂移注入的纯噪声序列
    from process_copilot.leachate_early_warning import ScenarioSeries

    truncated = ScenarioSeries(
        day_index=list(range(BASELINE_DAYS)),
        series={key: values[:BASELINE_DAYS] for key, values in series.series.items()},
    )
    warning = detect_early_warning(truncated)
    assert warning.triggered is False


def test_disclosure_present_on_scenario_result() -> None:
    result = build_scenario(seed=42)
    assert "合成示意数据" in result.disclosure
    assert len(result.citations) == 3
