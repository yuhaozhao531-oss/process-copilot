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
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

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


RIDGE_ALPHA_CANDIDATES = (1.0, 10.0, 50.0, 100.0, 300.0, 1000.0, 3000.0, 10000.0)
CV_FOLDS = 5


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


def _r2_score(actual: np.ndarray, predicted: np.ndarray) -> float:
    residual_ss = float(np.sum((actual - predicted) ** 2))
    total_ss = float(np.sum((actual - actual.mean()) ** 2))
    if total_ss == 0:
        return 0.0
    return 1.0 - residual_ss / total_ss


def _fit_ridge(x: np.ndarray, y: np.ndarray, alpha: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = x.mean(axis=0)
    std = x.std(axis=0)
    std[std == 0] = 1.0  # 避免除零；该特征在这份训练数据内是常数，标准化后恒为0，不影响回归
    design = np.hstack([np.ones((len(y), 1)), (x - mean) / std])
    penalty = alpha * np.eye(design.shape[1])
    penalty[0, 0] = 0.0  # 截距项不做正则化
    coefficients = np.linalg.solve(design.T @ design + penalty, design.T @ y)
    return coefficients, mean, std


def _predict_ridge(coefficients: np.ndarray, mean: np.ndarray, std: np.ndarray, x: np.ndarray) -> np.ndarray:
    design = np.hstack([np.ones((len(x), 1)), (x - mean) / std])
    return design @ coefficients


def _select_ridge_alpha(x_train: np.ndarray, y_train: np.ndarray) -> float:
    """在训练集内部做扩展窗口交叉验证选正则化强度——不能用测试集选超参，否则是用未来数据调参。"""
    fold_size = len(y_train) // (CV_FOLDS + 1)
    mean_scores: dict[float, float] = {}
    for alpha in RIDGE_ALPHA_CANDIDATES:
        fold_scores = []
        for fold in range(1, CV_FOLDS + 1):
            train_end = fold_size * fold
            valid_end = fold_size * (fold + 1)
            coefficients, mean, std = _fit_ridge(x_train[:train_end], y_train[:train_end], alpha)
            predicted = _predict_ridge(coefficients, mean, std, x_train[train_end:valid_end])
            fold_scores.append(_r2_score(y_train[train_end:valid_end], predicted))
        mean_scores[alpha] = float(np.mean(fold_scores))
    return max(RIDGE_ALPHA_CANDIDATES, key=lambda a: mean_scores[a])


def fit_soft_sensor(
    dataset: FlotationDataset | None = None, train_fraction: float = 0.8
) -> SoftSensorResult:
    """按时间顺序切分训练/测试集（不能随机打乱——软测量预测的是未来，随机切分会泄漏未来信息）。

    21个实时变量之间存在明显共线性（同一浮选柱的风量/液位彼此相关），普通最小二乘在训练集上
    拟合得很好、但在按时间顺序切出的测试集上反而输给"永远预测训练集均值"这个朴素基线
    （R²为负）。改用ridge正则化能缓解，但正则化强度必须在训练集内部用扩展窗口交叉验证选出，
    不能直接在测试集上调——那样等于用未来数据挑参数，会得到虚高的、不可信的分数。

    诚实说明：即便这样处理，held-out测试集上的R²也只是勉强转正（约0.01量级），不是"AI证明
    有效"的结果——这本身就是有价值的发现：简单线性模型在这类真实浮选数据上的滞后预测能力
    很有限，不能因为想要一个好看的数字就回避这一点。
    """
    if dataset is None:
        dataset = load_dataset()
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be between 0 and 1")

    n = len(dataset.target)
    split = int(n * train_fraction)
    if split < 2 or n - split < 2:
        raise ValueError("dataset too small for the requested train/test split")

    x_train, x_test = dataset.features[:split], dataset.features[split:]
    y_train, y_test = dataset.target[:split], dataset.target[split:]

    alpha = _select_ridge_alpha(x_train, y_train)
    coefficients_with_intercept, mean, std = _fit_ridge(x_train, y_train, alpha)
    predicted = _predict_ridge(coefficients_with_intercept, mean, std, x_test)

    naive_baseline_mae = float(np.mean(np.abs(y_test - y_train.mean())))

    return SoftSensorResult(
        feature_names=dataset.feature_names,
        coefficients=[float(c) for c in coefficients_with_intercept[1:]],
        intercept=float(coefficients_with_intercept[0]),
        ridge_alpha=alpha,
        train_size=split,
        test_size=n - split,
        test_mae=float(np.mean(np.abs(y_test - predicted))),
        test_r2=_r2_score(y_test, predicted),
        naive_baseline_mae=naive_baseline_mae,
        test_hours=dataset.hours[split:],
        test_actual=[float(v) for v in y_test],
        test_predicted=[float(v) for v in predicted],
    )
