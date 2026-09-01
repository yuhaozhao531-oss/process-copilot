"""交椅山磷石膏渣库渗滤液早期预警（合成示意数据）。

业务逻辑链（对应报告 2.5 / 3.2 节"漏洞二"）：
    磷石膏堆场 -> HDPE防渗膜 + 雨污分流管网 -> 库底导渗盲沟集水池
        [正常] -> 回送厂区处理
        [异常] -> 防渗膜老化/破损 -> 渗滤液下渗 -> 岩溶通道运移 -> 泉点出露 -> 总磷超标

先导指标（防渗膜异常置信度、渗滤液电导率、边坡位移）在渗滤液进入岩溶通道之前
就可能反映异常；滞后指标（总磷浓度）只有等渗滤液运移到泉点才能测到——这个
"先漏、后测到"的因果顺序是 2017 年环保督查真实发生过的事件（渗漏经泉点出露
后才被发现），不是本模块编造的假设。

本模块生成的是**合成示意数据**，不是息烽园区真实传感器数据；用于演示"先导指标
持续偏离基线是否能比总磷超标更早触发预警"这一假设，具体提前量只对这组合成
数据成立，不代表息烽园区真实的预警提前量。
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

DISCLOSURE = "合成示意数据，依据报告引用的真实事件时间线设计漂移形态，不是息烽园区真实传感器数据。"

TOTAL_PHOSPHORUS_LIMIT_MG_L = 0.3  # 息烽河流域总磷特别排放限值（省级生态环境厅通告，报告3.2节）

DAYS = 180
BASELINE_DAYS = 120
DRIFT_START_DAY = 120
BREACH_RAMP_START_DAY = 158
SUSTAINED_DAYS_REQUIRED = 5
LEADING_SIGMA_THRESHOLD = 4.0


@dataclass(frozen=True)
class VariableSpec:
    variable_id: str
    variable_name: str
    unit: str
    monitoring_point: str
    leading_indicator: bool


VARIABLES: tuple[VariableSpec, ...] = (
    VariableSpec(
        "membrane_anomaly_score",
        "防渗膜异常置信度（机器视觉，对应HJ 1480-2026视频异常检测报警类型）",
        "score(0-1)",
        "交椅山渣库西侧边坡",
        leading_indicator=True,
    ),
    VariableSpec(
        "conductivity_us_cm", "渗滤液电导率", "uS/cm", "库底导渗盲沟集水池", leading_indicator=True
    ),
    VariableSpec(
        "slope_displacement_mm", "边坡累计位移", "mm", "交椅山渣库西侧边坡", leading_indicator=True
    ),
    VariableSpec(
        "leachate_level_m", "渗滤液集水池水位", "m", "库底导渗盲沟集水池", leading_indicator=False
    ),
    VariableSpec("ph", "渗滤液pH", "pH", "库底导渗盲沟集水池", leading_indicator=False),
    VariableSpec(
        "total_phosphorus_mg_l", "总磷浓度（泉点出露）", "mg/L", "桂花泉", leading_indicator=False
    ),
)

CITATIONS: tuple[dict[str, str], ...] = (
    {
        "label": "交椅山磷石膏库西侧边坡及三区东段覆土复绿项目环境影响报告书公众参与说明（贵阳开磷化肥有限公司，2025）",
        "detail": "防渗膜老化、排水沟渠淤堵渗漏、雨污未分流的现状描述，是本场景防渗膜异常与渗滤液早期漂移设定的依据。",
    },
    {
        "label": "息烽县磷煤化工生态工业基地总体规划环境影响评价报告书简本（息烽县人民政府，2022）第2.5节",
        "detail": "2017年环保督查发现渗漏经泉点出露、企业分五期治理、2020-2021年仍出现渗漏点的事实时间线。",
    },
    {
        "label": "HJ 1480-2026《排污单位自行监测视频监控系统建设与联网技术要求》（生态环境部，2026-07-22发布，2026-10-01实施）",
        "detail": "视频异常检测报警类型编码，是本场景“防渗膜异常置信度”变量对应的标准化数据来源设计依据。",
    },
)


@dataclass(frozen=True)
class ScenarioSeries:
    day_index: list[int]
    series: dict[str, list[float]]


@dataclass(frozen=True)
class EarlyWarningResult:
    triggered: bool
    warning_day: int | None
    warning_variable_id: str | None
    breach_day: int | None
    breach_variable_id: str
    lead_time_days: int | None
    summary: str


@dataclass(frozen=True)
class LeachateScenarioResult:
    series: ScenarioSeries
    early_warning: EarlyWarningResult
    variables: tuple[VariableSpec, ...] = VARIABLES
    citations: tuple[dict[str, str], ...] = CITATIONS
    regulatory_limit_mg_l: float = TOTAL_PHOSPHORUS_LIMIT_MG_L
    disclosure: str = DISCLOSURE


def _drift_ramp(day: int, start_day: int, span: int, power: float) -> float:
    ramp = max((day - start_day) / span, 0.0)
    return ramp**power


def _clamp(value: float, low: float, high: float | None = None) -> float:
    value = max(value, low)
    if high is not None:
        value = min(value, high)
    return value


def generate_series(seed: int = 42, days: int = DAYS) -> ScenarioSeries:
    rng = random.Random(seed)
    span = max(days - DRIFT_START_DAY, 1)
    breach_span = max(days - BREACH_RAMP_START_DAY, 1)

    membrane_anomaly_score: list[float] = []
    conductivity_us_cm: list[float] = []
    slope_displacement_mm: list[float] = []
    leachate_level_m: list[float] = []
    ph: list[float] = []
    total_phosphorus_mg_l: list[float] = []

    cumulative_slope = 0.0
    for day in range(days):
        membrane_drift = _drift_ramp(day, DRIFT_START_DAY, span, power=1.6)
        breach_drift = _drift_ramp(day, BREACH_RAMP_START_DAY, breach_span, power=2.2)

        membrane_anomaly_score.append(
            _clamp(rng.gauss(0.05, 0.01) + 0.85 * membrane_drift, 0.0, 1.0)
        )
        conductivity_us_cm.append(rng.gauss(950.0, 20.0) + 650.0 * membrane_drift)
        cumulative_slope += rng.gauss(0.02, 0.01) + 6.0 * membrane_drift / days
        slope_displacement_mm.append(cumulative_slope)
        leachate_level_m.append(rng.gauss(3.2, 0.05) + 0.4 * membrane_drift)
        ph.append(rng.gauss(7.6, 0.05) - 0.5 * membrane_drift)
        total_phosphorus_mg_l.append(_clamp(rng.gauss(0.08, 0.01) + 0.55 * breach_drift, 0.0))

    return ScenarioSeries(
        day_index=list(range(days)),
        series={
            "membrane_anomaly_score": membrane_anomaly_score,
            "conductivity_us_cm": conductivity_us_cm,
            "slope_displacement_mm": slope_displacement_mm,
            "leachate_level_m": leachate_level_m,
            "ph": ph,
            "total_phosphorus_mg_l": total_phosphorus_mg_l,
        },
    )


def _first_sustained_breach(values: list[float], threshold: float, sustained_days: int) -> int | None:
    run = 0
    for index, value in enumerate(values):
        run = run + 1 if value > threshold else 0
        if run >= sustained_days:
            return index - sustained_days + 1
    return None


def detect_early_warning(series: ScenarioSeries) -> EarlyWarningResult:
    total_phosphorus = series.series["total_phosphorus_mg_l"]
    breach_day = _first_sustained_breach(total_phosphorus, TOTAL_PHOSPHORUS_LIMIT_MG_L, sustained_days=1)
    breach_variable_id = "total_phosphorus_mg_l"

    best_warning_day: int | None = None
    best_variable_id: str | None = None
    for spec in VARIABLES:
        if not spec.leading_indicator:
            continue
        values = series.series[spec.variable_id]
        baseline = values[:BASELINE_DAYS]
        mean = sum(baseline) / len(baseline)
        variance = sum((v - mean) ** 2 for v in baseline) / len(baseline)
        std = max(variance**0.5, 1e-9)
        threshold = mean + LEADING_SIGMA_THRESHOLD * std
        warning_day = _first_sustained_breach(values, threshold, SUSTAINED_DAYS_REQUIRED)
        if warning_day is None:
            continue
        if best_warning_day is None or warning_day < best_warning_day:
            best_warning_day = warning_day
            best_variable_id = spec.variable_id

    triggered = best_warning_day is not None and breach_day is not None
    lead_time_days = (breach_day - best_warning_day) if triggered else None

    if triggered and lead_time_days is not None and lead_time_days > 0:
        variable_name = next(v.variable_name for v in VARIABLES if v.variable_id == best_variable_id)
        summary = (
            f"第 {best_warning_day} 天，{variable_name} 率先持续偏离基线 "
            f"{SUSTAINED_DAYS_REQUIRED} 天以上；总磷在第 {breach_day} 天于泉点突破 "
            f"{TOTAL_PHOSPHORUS_LIMIT_MG_L} mg/L 特别排放限值——提前 {lead_time_days} 天可发出预警，"
            "而不是等泉点超标后才发现（对应报告3.2节“漏洞二”）。"
        )
    else:
        summary = "本次生成序列未形成有效的提前预警窗口，请检查随机种子或漂移参数设置。"

    return EarlyWarningResult(
        triggered=triggered,
        warning_day=best_warning_day,
        warning_variable_id=best_variable_id,
        breach_day=breach_day,
        breach_variable_id=breach_variable_id,
        lead_time_days=lead_time_days,
        summary=summary,
    )


def build_scenario(seed: int = 42, days: int = DAYS) -> LeachateScenarioResult:
    series = generate_series(seed=seed, days=days)
    early_warning = detect_early_warning(series)
    return LeachateScenarioResult(series=series, early_warning=early_warning)
