"""以渣定产：磷石膏消纳能力约束下的园区物料平衡仿真。

业务逻辑链（对应报告 2.1 / 2.5 / 3.2 节）：
    开阳磷矿 -> 破碎/磨矿/浮选 -> 磷精矿浆 + H2SO4
    -> 反应槽：Ca5F(PO4)3 + 5H2SO4 + 10H2O -> 3H3PO4 + 5CaSO4*2H2O + HF
    -> 真空过滤三相分离
         液相（粗磷酸，不外销）-> 磷肥支路 / 净化磷酸支路（怎么分配磷酸互不影响磷石膏产出）
         固相（磷石膏，4-5 吨/吨 P2O5）-> 交椅山渣库堆存 / 分解制酸联产胶凝材料

磷石膏只随全园区磷酸总处理量产出，与下游支路如何分配磷酸无关；因此
"以渣定产"（黔府发〔2024〕5号）约束的是总处理量，不是单条产线负荷——
这一点决定了本模块的仿真对象是"总量 -> 磷石膏产出是否超限"，分配逻辑
只是在给定总量约束下，如何在各条产线之间分摊可用产能。

纯规则计算，不训练/调用任何模型，不缓存任何状态。磷石膏产出系数
4-5 吨/吨 P2O5 的默认区间引用报告 2.1 节；消纳能力上限、各支路请求
处理量均由调用方传入，不是核实过的息烽园区真实产能数字。
"""

from __future__ import annotations

from dataclasses import dataclass

DISCLOSURE = (
    "报告 2.1 节引用的磷石膏产出系数（4-5 吨/吨 P2O5）驱动的示意性物料平衡计算；"
    "消纳能力上限与各支路处理量均由调用方传入，不是核实过的息烽园区真实产能数字。"
)

DEFAULT_GYPSUM_RATIO_LOW = 4.0
DEFAULT_GYPSUM_RATIO_HIGH = 5.0


@dataclass(frozen=True)
class ProductionLine:
    id: str
    name: str
    requested_p2o5_tpd: float
    priority: int = 0


@dataclass(frozen=True)
class LineAllocation:
    id: str
    name: str
    requested_p2o5_tpd: float
    allocated_p2o5_tpd: float

    @property
    def load_pct_of_request(self) -> float:
        if self.requested_p2o5_tpd <= 0:
            return 0.0
        return self.allocated_p2o5_tpd / self.requested_p2o5_tpd * 100.0


@dataclass(frozen=True)
class CapacityPlanOption:
    strategy: str
    label: str
    lines: tuple[LineAllocation, ...]
    gypsum_ratio_low: float
    gypsum_ratio_high: float
    gypsum_cap_tpd: float

    @property
    def total_allocated_p2o5_tpd(self) -> float:
        return sum(line.allocated_p2o5_tpd for line in self.lines)

    @property
    def gypsum_output_low_tpd(self) -> float:
        return self.total_allocated_p2o5_tpd * self.gypsum_ratio_low

    @property
    def gypsum_output_high_tpd(self) -> float:
        return self.total_allocated_p2o5_tpd * self.gypsum_ratio_high

    @property
    def within_cap(self) -> bool:
        return self.gypsum_output_high_tpd <= self.gypsum_cap_tpd + 1e-9

    @property
    def utilization_pct(self) -> float:
        if self.gypsum_cap_tpd <= 0:
            return 0.0
        return self.gypsum_output_high_tpd / self.gypsum_cap_tpd * 100.0


@dataclass(frozen=True)
class CapacityPlanResult:
    gypsum_cap_tpd: float
    total_requested_p2o5_tpd: float
    requested_gypsum_output_low_tpd: float
    requested_gypsum_output_high_tpd: float
    request_within_cap: bool
    options: tuple[CapacityPlanOption, ...]
    disclosure: str = DISCLOSURE


def _allocate(lines: list[ProductionLine], scale_by_line: dict[str, float]) -> tuple[LineAllocation, ...]:
    return tuple(
        LineAllocation(
            id=line.id,
            name=line.name,
            requested_p2o5_tpd=line.requested_p2o5_tpd,
            allocated_p2o5_tpd=line.requested_p2o5_tpd * scale_by_line.get(line.id, 0.0),
        )
        for line in lines
    )


def _proportional_scale(
    lines: list[ProductionLine], budget_tpd: float, requested_total: float
) -> dict[str, float]:
    if requested_total <= 0:
        return {line.id: 0.0 for line in lines}
    scale = min(max(budget_tpd, 0.0) / requested_total, 1.0)
    return {line.id: scale for line in lines}


def _priority_first_scale(lines: list[ProductionLine], budget_tpd: float) -> dict[str, float]:
    ordered = sorted(lines, key=lambda line: (-line.priority, line.id))
    remaining = max(budget_tpd, 0.0)
    scales: dict[str, float] = {}
    for line in ordered:
        if line.requested_p2o5_tpd <= 0:
            scales[line.id] = 0.0
            continue
        take = min(line.requested_p2o5_tpd, remaining)
        scales[line.id] = take / line.requested_p2o5_tpd
        remaining -= take
    return scales


def _equal_share_scale(lines: list[ProductionLine], budget_tpd: float) -> dict[str, float]:
    if not lines:
        return {}
    share = max(budget_tpd, 0.0) / len(lines)
    return {
        line.id: (min(1.0, share / line.requested_p2o5_tpd) if line.requested_p2o5_tpd > 0 else 0.0)
        for line in lines
    }


def simulate(
    lines: list[ProductionLine],
    gypsum_cap_tpd: float,
    gypsum_ratio_low: float = DEFAULT_GYPSUM_RATIO_LOW,
    gypsum_ratio_high: float = DEFAULT_GYPSUM_RATIO_HIGH,
) -> CapacityPlanResult:
    ratio_low, ratio_high = sorted((gypsum_ratio_low, gypsum_ratio_high))
    total_requested = sum(line.requested_p2o5_tpd for line in lines)
    requested_low = total_requested * ratio_low
    requested_high = total_requested * ratio_high
    request_within_cap = requested_high <= gypsum_cap_tpd + 1e-9

    def _option(strategy: str, label: str, scale_by_line: dict[str, float]) -> CapacityPlanOption:
        return CapacityPlanOption(
            strategy=strategy,
            label=label,
            lines=_allocate(lines, scale_by_line),
            gypsum_ratio_low=ratio_low,
            gypsum_ratio_high=ratio_high,
            gypsum_cap_tpd=gypsum_cap_tpd,
        )

    options = [_option("proportional", "按请求全量运行（未受消纳能力约束）", {line.id: 1.0 for line in lines})]

    if not request_within_cap:
        conservative_budget = gypsum_cap_tpd / ratio_high if ratio_high > 0 else 0.0
        options.append(
            _option(
                "proportional",
                "按比例统一压减至消纳能力上限内",
                _proportional_scale(lines, conservative_budget, total_requested),
            )
        )
        options.append(
            _option(
                "priority_first",
                "优先保供高优先级装置，压减其余装置",
                _priority_first_scale(lines, conservative_budget),
            )
        )
        options.append(
            _option(
                "equal_share",
                "各装置按消纳额度平均分摊",
                _equal_share_scale(lines, conservative_budget),
            )
        )

    return CapacityPlanResult(
        gypsum_cap_tpd=gypsum_cap_tpd,
        total_requested_p2o5_tpd=total_requested,
        requested_gypsum_output_low_tpd=requested_low,
        requested_gypsum_output_high_tpd=requested_high,
        request_within_cap=request_within_cap,
        options=tuple(options),
    )
