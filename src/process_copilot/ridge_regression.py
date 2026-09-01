"""通用岭回归 + 训练集内交叉验证，供各场景的软测量/方法论验证模块复用。

统一纪律，避免每个场景各写一遍、后续容易改漏：
1. 按时间顺序切分训练/测试集，不随机打乱——预测的是未来，随机切分会泄漏未来信息。
2. 正则化强度必须在训练集内部用扩展窗口交叉验证选出，不能拿测试集调参，
   否则等于用未来数据挑参数，分数会虚高、不可信。
3. 结果里始终带上朴素基线（永远预测训练集均值）的MAE，方便判断模型是否
   真的有意义，不能只看一个孤立的R²。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

RIDGE_ALPHA_CANDIDATES = (1.0, 10.0, 50.0, 100.0, 300.0, 1000.0, 3000.0, 10000.0)
CV_FOLDS = 5


def r2_score(actual: np.ndarray, predicted: np.ndarray) -> float:
    residual_ss = float(np.sum((actual - predicted) ** 2))
    total_ss = float(np.sum((actual - actual.mean()) ** 2))
    if total_ss == 0:
        return 0.0
    return 1.0 - residual_ss / total_ss


def fit_ridge(x: np.ndarray, y: np.ndarray, alpha: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = x.mean(axis=0)
    std = x.std(axis=0)
    std[std == 0] = 1.0  # 避免除零；该特征在这份训练数据内是常数，标准化后恒为0，不影响回归
    design = np.hstack([np.ones((len(y), 1)), (x - mean) / std])
    penalty = alpha * np.eye(design.shape[1])
    penalty[0, 0] = 0.0  # 截距项不做正则化
    coefficients = np.linalg.solve(design.T @ design + penalty, design.T @ y)
    return coefficients, mean, std


def predict_ridge(coefficients: np.ndarray, mean: np.ndarray, std: np.ndarray, x: np.ndarray) -> np.ndarray:
    design = np.hstack([np.ones((len(x), 1)), (x - mean) / std])
    return design @ coefficients


def select_ridge_alpha(
    x_train: np.ndarray,
    y_train: np.ndarray,
    candidates: tuple[float, ...] = RIDGE_ALPHA_CANDIDATES,
    folds: int = CV_FOLDS,
) -> float:
    fold_size = len(y_train) // (folds + 1)
    mean_scores: dict[float, float] = {}
    for alpha in candidates:
        fold_scores = []
        for fold in range(1, folds + 1):
            train_end = fold_size * fold
            valid_end = fold_size * (fold + 1)
            coefficients, mean, std = fit_ridge(x_train[:train_end], y_train[:train_end], alpha)
            predicted = predict_ridge(coefficients, mean, std, x_train[train_end:valid_end])
            fold_scores.append(r2_score(y_train[train_end:valid_end], predicted))
        mean_scores[alpha] = float(np.mean(fold_scores))
    return max(candidates, key=lambda a: mean_scores[a])


@dataclass(frozen=True)
class ChronoRidgeResult:
    feature_names: list[str]
    coefficients: list[float]
    intercept: float
    ridge_alpha: float
    train_size: int
    test_size: int
    test_mae: float
    test_r2: float
    naive_baseline_mae: float
    test_index: list[str]
    test_actual: list[float]
    test_predicted: list[float]


def fit_chronological_ridge(
    feature_names: list[str],
    index: list[str],
    features: np.ndarray,
    target: np.ndarray,
    train_fraction: float = 0.8,
) -> ChronoRidgeResult:
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be between 0 and 1")

    n = len(target)
    split = int(n * train_fraction)
    if split < 2 or n - split < 2:
        raise ValueError("dataset too small for the requested train/test split")

    x_train, x_test = features[:split], features[split:]
    y_train, y_test = target[:split], target[split:]

    alpha = select_ridge_alpha(x_train, y_train)
    coefficients_with_intercept, mean, std = fit_ridge(x_train, y_train, alpha)
    predicted = predict_ridge(coefficients_with_intercept, mean, std, x_test)

    return ChronoRidgeResult(
        feature_names=feature_names,
        coefficients=[float(c) for c in coefficients_with_intercept[1:]],
        intercept=float(coefficients_with_intercept[0]),
        ridge_alpha=alpha,
        train_size=split,
        test_size=n - split,
        test_mae=float(np.mean(np.abs(y_test - predicted))),
        test_r2=r2_score(y_test, predicted),
        naive_baseline_mae=float(np.mean(np.abs(y_test - y_train.mean()))),
        test_index=index[split:],
        test_actual=[float(v) for v in y_test],
        test_predicted=[float(v) for v in predicted],
    )
