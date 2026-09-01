"""浮选投料控制的滞后化验软测量方法论验证（真实数据，非磷化工数据）。

业务逻辑链（对应报告2.1节矿石预处理环节、3.2节"漏洞一"）：
    开阳磷矿（品位波动）-> 破碎/磨矿/浮选 -> 磷精矿浆（品位仍波动）
        [本模块验证的边界就在这一步：实时传感器（加药量、矿浆性质）
         能否预测滞后1小时才出的化验结果]
    -> 传导至反应槽 -> 影响萃取率、磷石膏残磷（报告漏洞一原文描述的后果，
       本模块不覆盖这一段——没有真实息烽反应槽数据）

数据来源：Kaggle "Quality Prediction in a Mining Process"
(edumagalhaes/quality-prediction-in-a-mining-process)，CC0协议，真实
巴西某铁矿浮选厂2017年3-9月数据，非合成、非模拟。加药量（Starch Flow
淀粉抑制剂、Amina Flow胺类捕收剂）、矿浆流量/pH/密度、7组浮选柱风量与
液位，每20秒采样；杂质指标（% Silica Concentrate，浮选精矿中的二氧化硅
残留）每小时化验一次——这正是报告漏洞一描述的"实时传感器 vs 滞后化验"
问题结构，跟磷矿浮选是同一类单元操作（加药剂矿浆浮选），只是目标矿物
不同（铁矿 vs 磷矿）。

能验证的边界：只到"浮选投料控制"这一段的方法论——实时多变量能否有效
预测滞后化验指标本身是否可行。不能延伸到磷化工反应槽萃取段，那一段
报告和本项目都没有真实数据覆盖。

诚实说明：普通最小二乘在21个存在共线性的实时变量上过拟合，按时间顺序切出
的测试集上反而输给"永远预测训练集均值"这个朴素基线（R²为负）。改用ridge
正则化、且强度必须来自训练集内部交叉验证（不能拿测试集调参）之后，held-out
测试集R²也只是勉强转正（约0.01量级）——这是这份真实数据给出的诚实结果，
不是"AI证明有效"的展示，参见 ridge_regression.py 顶部注释里的统一纪律。
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from process_copilot.ridge_regression import ChronoRidgeResult, fit_chronological_ridge

DISCLOSURE = (
    "结构相似的真实工业数据（巴西铁矿浮选厂，CC0协议），验证的是"
    "“实时传感器预测滞后化验指标”这一方法论本身是否有效；"
    "不是磷化工数据，不能代表湿法磷酸反应槽萃取段的表现。"
)

DEFAULT_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "flotation_hourly.csv"

FEATURE_COLUMNS = [
    "% Iron Feed",
    "% Silica Feed",
    "Starch Flow",
    "Amina Flow",
    "Ore Pulp Flow",
    "Ore Pulp pH",
    "Ore Pulp Density",
    "Flotation Column 01 Air Flow",
    "Flotation Column 02 Air Flow",
    "Flotation Column 03 Air Flow",
    "Flotation Column 04 Air Flow",
    "Flotation Column 05 Air Flow",
    "Flotation Column 06 Air Flow",
    "Flotation Column 07 Air Flow",
    "Flotation Column 01 Level",
    "Flotation Column 02 Level",
    "Flotation Column 03 Level",
    "Flotation Column 04 Level",
    "Flotation Column 05 Level",
    "Flotation Column 06 Level",
    "Flotation Column 07 Level",
]
TARGET_COLUMN = "% Silica Concentrate"


@dataclass(frozen=True)
class FlotationDataset:
    hours: list[str]
    feature_names: list[str]
    features: np.ndarray  # shape (n, len(feature_names))
    target: np.ndarray  # shape (n,)


def load_dataset(csv_path: Path = DEFAULT_DATA_PATH) -> FlotationDataset:
    hours: list[str] = []
    rows: list[list[float]] = []
    targets: list[float] = []
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            hours.append(row["hour"])
            rows.append([float(row[col]) for col in FEATURE_COLUMNS])
            targets.append(float(row[TARGET_COLUMN]))
    return FlotationDataset(
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
    dataset: FlotationDataset | None = None, train_fraction: float = 0.8
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
