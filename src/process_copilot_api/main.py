"""序安 Process Sentinel API。

只暴露只读查询/仿真接口，不存在任何向 DCS 或生产系统下发指令的路径。
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from process_copilot.capacity_planner import simulate
from process_copilot.flotation_lag_prediction import fit_soft_sensor as fit_flotation_soft_sensor
from process_copilot.leachate_early_warning import DAYS, build_scenario
from process_copilot.metal_dosing_precipitation import (
    fit_soft_sensor as fit_metal_dosing_soft_sensor,
)

from .environmental_schemas import LeachateScenarioResponse
from .flotation_schemas import SoftSensorResponse
from .metal_dosing_schemas import MetalDosingSoftSensorResponse
from .schemas import CapacityPlanRequest, CapacityPlanResponse

app = FastAPI(
    title="process-copilot API",
    description="只读预测/预警/仿真建议接口；不接管生产控制。",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/capacity-plan/simulate", response_model=CapacityPlanResponse)
def simulate_capacity_plan(request: CapacityPlanRequest) -> CapacityPlanResponse:
    result = simulate(
        lines=[line.to_domain() for line in request.lines],
        gypsum_cap_tpd=request.gypsum_cap_tpd,
        gypsum_ratio_low=request.gypsum_ratio_low,
        gypsum_ratio_high=request.gypsum_ratio_high,
    )
    return CapacityPlanResponse.from_domain(result)


@app.get(
    "/api/v1/environmental-scenarios/jiaoyishan-leachate",
    response_model=LeachateScenarioResponse,
)
def jiaoyishan_leachate_scenario(seed: int = 42, days: int = DAYS) -> LeachateScenarioResponse:
    """合成示意数据；不是息烽园区真实传感器数据，见响应中的 disclosure 字段。"""
    result = build_scenario(seed=seed, days=days)
    return LeachateScenarioResponse.from_domain(result)


@app.get(
    "/api/v1/scenarios/flotation-lag-prediction",
    response_model=SoftSensorResponse,
)
def flotation_lag_prediction_scenario(train_fraction: float = 0.8) -> SoftSensorResponse:
    """真实铁矿浮选数据（CC0）；结构相似的方法论验证，不是磷化工数据，见 disclosure 字段。"""
    result = fit_flotation_soft_sensor(train_fraction=train_fraction)
    return SoftSensorResponse.from_domain(result)


@app.get(
    "/api/v1/scenarios/metal-dosing-precipitation",
    response_model=MetalDosingSoftSensorResponse,
)
def metal_dosing_precipitation_scenario(
    train_fraction: float = 0.8,
) -> MetalDosingSoftSensorResponse:
    """真实污水厂化学除磷SCADA数据（CC BY-NC 3.0）；结构相似的方法论验证，不是磷化工数据，见 disclosure 字段。"""
    result = fit_metal_dosing_soft_sensor(train_fraction=train_fraction)
    return MetalDosingSoftSensorResponse.from_domain(result)
