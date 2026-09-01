from process_copilot.metal_dosing_precipitation import (
    FEATURE_COLUMNS,
    fit_soft_sensor,
    load_dataset,
)
from process_copilot.ridge_regression import RIDGE_ALPHA_CANDIDATES


def test_load_dataset_shape() -> None:
    dataset = load_dataset()
    assert len(dataset.hours) > 15000  # 2年、每小时一行
    assert dataset.features.shape == (len(dataset.hours), len(FEATURE_COLUMNS))
    assert dataset.target.shape == (len(dataset.hours),)


def test_fit_soft_sensor_chronological_split() -> None:
    dataset = load_dataset()
    result = fit_soft_sensor(dataset, train_fraction=0.8)

    assert result.train_size + result.test_size == len(dataset.hours)
    assert result.test_hours == dataset.hours[result.train_size :]
    assert result.test_hours[0] > dataset.hours[result.train_size - 1]


def test_ridge_alpha_selected_from_candidates_via_train_only_cv() -> None:
    result = fit_soft_sensor(train_fraction=0.8)
    assert result.ridge_alpha in RIDGE_ALPHA_CANDIDATES


def test_fit_soft_sensor_beats_naive_baseline_substantially() -> None:
    """跟①不同，这份数据上的结果是真实的强正向结果（R2约0.68），不是勉强打平——
    但这条测试只锁住"明显更强"这个方向性结论，不锁死具体数值，避免过度拟合测试。"""
    result = fit_soft_sensor(train_fraction=0.8)
    assert result.test_mae < result.naive_baseline_mae * 0.7
    assert result.test_r2 > 0.4


def test_metal_dosing_is_a_top_feature_but_disclosure_flags_feedback_caveat() -> None:
    """METAL_Q预计是最强特征之一，但disclosure必须保留"可能是闭环反馈耦合、
    不是单向因果"这个保留意见，不能被后续修改悄悄删掉。"""
    result = fit_soft_sensor()
    top_feature = max(
        zip(result.feature_names, result.coefficients), key=lambda item: abs(item[1])
    )
    assert top_feature[0] in {"METAL_Q", "T1_NH4"}
    assert "闭环反馈" in result.disclosure


def test_disclosure_present() -> None:
    result = fit_soft_sensor()
    assert "不是磷化工数据" in result.disclosure
    assert "CC BY-NC" in result.disclosure
