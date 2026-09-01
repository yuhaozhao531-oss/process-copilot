"""交椅山渣库早期预警场景的响应模型（camelCase，供前端直接消费）。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from process_copilot.leachate_early_warning import (
    EarlyWarningResult,
    LeachateScenarioResult,
    ScenarioSeries,
    VariableSpec,
)


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class VariableSpecResponse(_CamelModel):
    variable_id: str
    variable_name: str
    unit: str
    monitoring_point: str
    leading_indicator: bool

    @classmethod
    def from_domain(cls, spec: VariableSpec) -> "VariableSpecResponse":
        return cls(
            variable_id=spec.variable_id,
            variable_name=spec.variable_name,
            unit=spec.unit,
            monitoring_point=spec.monitoring_point,
            leading_indicator=spec.leading_indicator,
        )


class ScenarioSeriesResponse(_CamelModel):
    day_index: list[int]
    series: dict[str, list[float]]

    @classmethod
    def from_domain(cls, series: ScenarioSeries) -> "ScenarioSeriesResponse":
        return cls(day_index=series.day_index, series=series.series)


class EarlyWarningResponse(_CamelModel):
    triggered: bool
    warning_day: int | None
    warning_variable_id: str | None
    breach_day: int | None
    breach_variable_id: str
    lead_time_days: int | None
    summary: str

    @classmethod
    def from_domain(cls, result: EarlyWarningResult) -> "EarlyWarningResponse":
        return cls(
            triggered=result.triggered,
            warning_day=result.warning_day,
            warning_variable_id=result.warning_variable_id,
            breach_day=result.breach_day,
            breach_variable_id=result.breach_variable_id,
            lead_time_days=result.lead_time_days,
            summary=result.summary,
        )


class LeachateScenarioResponse(_CamelModel):
    series: ScenarioSeriesResponse
    early_warning: EarlyWarningResponse
    variables: list[VariableSpecResponse]
    citations: list[dict[str, str]]
    regulatory_limit_mg_l: float
    disclosure: str

    @classmethod
    def from_domain(cls, result: LeachateScenarioResult) -> "LeachateScenarioResponse":
        return cls(
            series=ScenarioSeriesResponse.from_domain(result.series),
            early_warning=EarlyWarningResponse.from_domain(result.early_warning),
            variables=[VariableSpecResponse.from_domain(v) for v in result.variables],
            citations=list(result.citations),
            regulatory_limit_mg_l=result.regulatory_limit_mg_l,
            disclosure=result.disclosure,
        )
