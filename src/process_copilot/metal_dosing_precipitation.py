"""金属盐投加沉淀磷酸根的方法论验证（真实数据，非磷化工数据）。

业务逻辑链（对应报告2.3节磷酸铁沉淀、3.2节"漏洞一"在沉淀陈化工段的延伸）：
    净化磷酸(PPA) + FeSO4 -[pH/温度/投料流量控制]-> 沉淀反应
        H3PO4 + FeSO4 + 2H2O -> FePO4*2H2O(沉淀) + H2SO4 + H2O
    -> 陈化 -> 多级洗涤 -> 固液分离 -> 闪蒸干燥 -> 磷酸铁成品（粒度/纯度指标）

本模块验证的边界：药剂投加量、温度、流量等控制变量能否解释/预测沉淀反应
的残留浓度指标——跟报告场景③要做的"预测晶体粒度、成品纯度"是同一类问题
（控制变量 -> 反应完成度/产品质量指标），只是方向相反：Agtrup是"投加铁盐
把水里的磷酸根沉淀去除"（化学除磷），磷酸铁产品合成是"用磷酸+亚铁盐做
产品"，但沉淀化学机理同属 Fe + PO4 -> FePO4 沉淀 这一反应家族，都受
投加量/温度驱动。

数据来源：Mendeley Data "Wastewater Treatment Plant Data for Nutrient
Removal System" (DOI 10.17632/34rpmsxc4z.1)，CC BY-NC 3.0协议（非商业
使用需署名），真实丹麦Agtrup(BlueKolding)污水厂SCADA数据，2021-08至
2023-07共2年、2分钟采样。不是磷化工数据，更不是息烽园区数据。

诚实说明（务必保留，不要在后续修改中删掉）：METAL_Q（铁盐投加流量）是
标准化系数绝对值最大的特征，且是正相关。这很可能不是"投加量决定残留磷"
这个方向的独立预测能力，而是因为现代污水厂普遍用在线磷酸盐传感器做闭环
反馈投加——磷高的时候系统本身就会多投药。跟①浮选数据集"人工设定加药量"
的开环情形不同，这里的高R2（约0.68）里有一部分反映的是控制系统自身的
反馈耦合，不是纯粹从原始工艺物理规律里挖出来的因果关系。这个保留意见
必须原样保留在文档和API disclosure里，不能简化成"投药量预测了残留磷"。
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from process_copilot.ridge_regression import ChronoRidgeResult, fit_chronological_ridge

DISCLOSURE = (
    "结构相似的真实工业数据（丹麦Agtrup污水厂化学除磷SCADA，CC BY-NC 3.0，"
    "非商业使用需署名）；不是磷化工数据，不是息烽园区数据。METAL_Q（投药量）"
    "是最强相关特征，但该系统大概率是闭环反馈投加，高R2部分反映控制系统自身"
    "耦合，不是单向因果预测能力。"
)

DEFAULT_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "agtrup_hourly.csv"

FEATURE_COLUMNS = [
    "IN_METAL_Q",
    "T1_O2",
    "METAL_Q",
    "TEMPERATURE",
    "IN_Q",
    "MAX_CF",
    "PROCESSPHASE_INLET",
    "PROCESSPHASE_OUTLET",
    "T1_NH4",
]
TARGET_COLUMN = "T1_PO4"


@dataclass(frozen=True)
class MetalDosingDataset:
    hours: list[str]
    feature_names: list[str]
    features: np.ndarray  # shape (n, len(feature_names))
    target: np.ndarray  # shape (n,)


def load_dataset(csv_path: Path = DEFAULT_DATA_PATH) -> MetalDosingDataset:
    hours: list[str] = []
    rows: list[list[float]] = []
    targets: list[float] = []
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            hours.append(row["hour"])
            rows.append([float(row[col]) for col in FEATURE_COLUMNS])
            targets.append(float(row[TARGET_COLUMN]))
    return MetalDosingDataset(
        hours=hours,
        feature_names=list(FEATURE_COLUMNS),
        features=np.asarray(rows, dtype=np.float64),
        target=np.asarray(targets, dtype=np.float64),
    )


@dataclass(frozen=True)
class SoftSensorResult:
    feature_names: list[str]
    coefficients: list[float]
    intercept: float
    ridge_alpha: float
    train_size: int
    test_size: int
    test_mae: float
    test_r2: float
    naive_baseline_mae: float
    test_hours: list[str]
    test_actual: list[float]
    test_predicted: list[float]
    disclosure: str = DISCLOSURE

    @classmethod
    def _from_chrono_result(cls, result: ChronoRidgeResult) -> "SoftSensorResult":
        return cls(
            feature_names=result.feature_names,
            coefficients=result.coefficients,
            intercept=result.intercept,
            ridge_alpha=result.ridge_alpha,
            train_size=result.train_size,
            test_size=result.test_size,
            test_mae=result.test_mae,
            test_r2=result.test_r2,
            naive_baseline_mae=result.naive_baseline_mae,
            test_hours=result.test_index,
            test_actual=result.test_actual,
            test_predicted=result.test_predicted,
        )


def fit_soft_sensor(
    dataset: MetalDosingDataset | None = None, train_fraction: float = 0.8
) -> SoftSensorResult:
    if dataset is None:
        dataset = load_dataset()
    chrono_result = fit_chronological_ridge(
        feature_names=dataset.feature_names,
        index=dataset.hours,
        features=dataset.features,
        target=dataset.target,
        train_fraction=train_fraction,
    )
    return SoftSensorResult._from_chrono_result(chrono_result)
