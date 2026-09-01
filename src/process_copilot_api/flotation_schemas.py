"""浮选滞后预测方法论验证场景的响应模型（camelCase，供前端直接消费）。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from process_copilot.flotation_lag_prediction import SoftSensorResult


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class SoftSensorResponse(_CamelModel):
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
    disclosure: str

    @classmethod
    def from_domain(cls, result: SoftSensorResult) -> "SoftSensorResponse":
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
            test_hours=result.test_hours,
            test_actual=result.test_actual,
            test_predicted=result.test_predicted,
            disclosure=result.disclosure,
        )
