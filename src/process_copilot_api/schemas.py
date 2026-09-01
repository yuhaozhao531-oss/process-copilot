"""capacity-plan 接口的请求/响应模型（camelCase，供前端直接消费）。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from process_copilot.capacity_planner import (
    DEFAULT_GYPSUM_RATIO_HIGH,
    DEFAULT_GYPSUM_RATIO_LOW,
    CapacityPlanOption,
    CapacityPlanResult,
    LineAllocation,
    ProductionLine,
)


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ProductionLineRequest(_CamelModel):
    id: str
    name: str
    requested_p2o5_tpd: float = Field(gt=0, alias="requestedP2o5Tpd")
    priority: int = 0

    def to_domain(self) -> ProductionLine:
        return ProductionLine(
            id=self.id, name=self.name, requested_p2o5_tpd=self.requested_p2o5_tpd, priority=self.priority
        )


class CapacityPlanRequest(_CamelModel):
    lines: list[ProductionLineRequest] = Field(min_length=1)
    gypsum_cap_tpd: float = Field(gt=0)
    gypsum_ratio_low: float = Field(default=DEFAULT_GYPSUM_RATIO_LOW, gt=0)
    gypsum_ratio_high: float = Field(default=DEFAULT_GYPSUM_RATIO_HIGH, gt=0)


class LineAllocationResponse(_CamelModel):
    id: str
    name: str
    requested_p2o5_tpd: float = Field(alias="requestedP2o5Tpd")
    allocated_p2o5_tpd: float = Field(alias="allocatedP2o5Tpd")
    load_pct_of_request: float

    @classmethod
    def from_domain(cls, line: LineAllocation) -> "LineAllocationResponse":
        return cls(
            id=line.id,
            name=line.name,
            requested_p2o5_tpd=line.requested_p2o5_tpd,
            allocated_p2o5_tpd=line.allocated_p2o5_tpd,
            load_pct_of_request=line.load_pct_of_request,
        )


class CapacityPlanOptionResponse(_CamelModel):
    strategy: str
    label: str
    lines: list[LineAllocationResponse]
    total_allocated_p2o5_tpd: float = Field(alias="totalAllocatedP2o5Tpd")
    gypsum_output_low_tpd: float
    gypsum_output_high_tpd: float
    within_cap: bool
    utilization_pct: float

    @classmethod
    def from_domain(cls, option: CapacityPlanOption) -> "CapacityPlanOptionResponse":
        return cls(
            strategy=option.strategy,
            label=option.label,
            lines=[LineAllocationResponse.from_domain(line) for line in option.lines],
            total_allocated_p2o5_tpd=option.total_allocated_p2o5_tpd,
            gypsum_output_low_tpd=option.gypsum_output_low_tpd,
            gypsum_output_high_tpd=option.gypsum_output_high_tpd,
            within_cap=option.within_cap,
            utilization_pct=option.utilization_pct,
        )


class CapacityPlanResponse(_CamelModel):
    gypsum_cap_tpd: float
    total_requested_p2o5_tpd: float = Field(alias="totalRequestedP2o5Tpd")
    requested_gypsum_output_low_tpd: float
    requested_gypsum_output_high_tpd: float
    request_within_cap: bool
    options: list[CapacityPlanOptionResponse]
    disclosure: str

    @classmethod
    def from_domain(cls, result: CapacityPlanResult) -> "CapacityPlanResponse":
        return cls(
            gypsum_cap_tpd=result.gypsum_cap_tpd,
            total_requested_p2o5_tpd=result.total_requested_p2o5_tpd,
            requested_gypsum_output_low_tpd=result.requested_gypsum_output_low_tpd,
            requested_gypsum_output_high_tpd=result.requested_gypsum_output_high_tpd,
            request_within_cap=result.request_within_cap,
            options=[CapacityPlanOptionResponse.from_domain(option) for option in result.options],
            disclosure=result.disclosure,
        )
