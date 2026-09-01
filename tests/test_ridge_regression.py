import numpy as np
import pytest

from process_copilot.ridge_regression import (
    RIDGE_ALPHA_CANDIDATES,
    fit_chronological_ridge,
    r2_score,
)


def test_r2_score_perfect_prediction_is_one() -> None:
    actual = np.array([1.0, 2.0, 3.0, 4.0])
    assert r2_score(actual, actual) == pytest.approx(1.0)


def test_r2_score_constant_prediction_at_mean_is_zero() -> None:
    actual = np.array([1.0, 2.0, 3.0, 4.0])
    predicted = np.full_like(actual, actual.mean())
    assert r2_score(actual, predicted) == pytest.approx(0.0)


def test_fit_chronological_ridge_recovers_linear_signal() -> None:
    """在一段有真实线性关系、加了小噪声的合成数据上，模型应该明显跑赢朴素基线——
    这条测试验证的是回归工具本身的正确性，不是任何一个业务场景的真实效果。"""
    rng = np.random.default_rng(0)
    n = 400
    x = rng.normal(size=(n, 3))
    true_coef = np.array([2.0, -1.0, 0.5])
    y = x @ true_coef + rng.normal(scale=0.05, size=n)
    index = [str(i) for i in range(n)]

    result = fit_chronological_ridge(
        feature_names=["a", "b", "c"], index=index, features=x, target=y, train_fraction=0.8
    )

    assert result.test_r2 > 0.9
    assert result.test_mae < result.naive_baseline_mae
    assert result.ridge_alpha in RIDGE_ALPHA_CANDIDATES


def test_fit_chronological_ridge_rejects_invalid_train_fraction() -> None:
    x = np.zeros((10, 2))
    y = np.zeros(10)
    with pytest.raises(ValueError):
        fit_chronological_ridge(["a", "b"], [str(i) for i in range(10)], x, y, train_fraction=0.0)
    with pytest.raises(ValueError):
        fit_chronological_ridge(["a", "b"], [str(i) for i in range(10)], x, y, train_fraction=1.0)


def test_fit_chronological_ridge_rejects_too_small_dataset() -> None:
    x = np.zeros((3, 2))
    y = np.zeros(3)
    with pytest.raises(ValueError):
        fit_chronological_ridge(["a", "b"], [str(i) for i in range(3)], x, y, train_fraction=0.9)
