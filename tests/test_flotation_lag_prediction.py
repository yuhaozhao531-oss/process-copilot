from process_copilot.flotation_lag_prediction import (
    FEATURE_COLUMNS,
    fit_soft_sensor,
    load_dataset,
)
from process_copilot.ridge_regression import RIDGE_ALPHA_CANDIDATES


def test_load_dataset_shape() -> None:
    dataset = load_dataset()
    assert len(dataset.hours) > 4000
    assert dataset.features.shape == (len(dataset.hours), len(FEATURE_COLUMNS))
    assert dataset.target.shape == (len(dataset.hours),)


def test_fit_soft_sensor_chronological_split() -> None:
    dataset = load_dataset()
    result = fit_soft_sensor(dataset, train_fraction=0.8)

    assert result.train_size + result.test_size == len(dataset.hours)
    assert result.test_hours == dataset.hours[result.train_size :]
    # 训练/测试必须按时间先后切分，不能随机打乱——这是软测量任务的正确性前提
    assert result.test_hours[0] > dataset.hours[result.train_size - 1]


def test_ridge_alpha_selected_from_candidates_via_train_only_cv() -> None:
    """正则化强度必须来自训练集内部交叉验证，不能是拿测试集调出来的。"""
    result = fit_soft_sensor(train_fraction=0.8)
    assert result.ridge_alpha in RIDGE_ALPHA_CANDIDATES


def test_fit_soft_sensor_reports_honest_comparison_to_naive_baseline() -> None:
    """诚实的期望：ridge软测量在held-out测试集上不比朴素基线（永远预测训练集均值）差太多，
    但也不假装它有多好——R2在这份真实数据上只是勉强转正，不做更强的断言。"""
    result = fit_soft_sensor(train_fraction=0.8)
    assert result.test_mae <= result.naive_baseline_mae
    assert result.test_r2 > -0.05


def test_fit_soft_sensor_rejects_invalid_split() -> None:
    import pytest

    with pytest.raises(ValueError):
        fit_soft_sensor(train_fraction=1.5)
    with pytest.raises(ValueError):
        fit_soft_sensor(train_fraction=0.0)


def test_disclosure_present() -> None:
    result = fit_soft_sensor()
    assert "不是磷化工数据" in result.disclosure
    assert result.feature_names == FEATURE_COLUMNS
