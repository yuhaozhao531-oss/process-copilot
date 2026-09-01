"""序安 Process Sentinel API。

只暴露只读查询/仿真接口，不存在任何向 DCS 或生产系统下发指令的路径。
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from process_copilot.capacity_planner import simulate

from .schemas import CapacityPlanRequest, CapacityPlanResponse

app = FastAPI(
    title="process-copilot API",
    description="只读预测/预警/仿真建议接口；不接管生产控制。",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
