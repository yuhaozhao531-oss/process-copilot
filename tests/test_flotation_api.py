from fastapi.testclient import TestClient

from process_copilot_api.main import app

client = TestClient(app)


def test_flotation_scenario_default() -> None:
    response = client.get("/api/v1/scenarios/flotation-lag-prediction")
    assert response.status_code == 200
    body = response.json()

    assert body["trainSize"] > 3000
    assert body["testSize"] > 500
    assert len(body["testHours"]) == body["testSize"]
    assert len(body["testActual"]) == body["testSize"]
    assert len(body["testPredicted"]) == body["testSize"]
    assert len(body["featureNames"]) == 21
    assert len(body["coefficients"]) == 21
    assert "不是磷化工数据" in body["disclosure"]
    # 诚实指标：不吹嘘拟合优度，但必须给出跟朴素基线的对比，让人自己判断
    assert body["testMae"] <= body["naiveBaselineMae"]


def test_flotation_scenario_custom_train_fraction() -> None:
    default_body = client.get("/api/v1/scenarios/flotation-lag-prediction").json()
    smaller_train_body = client.get(
        "/api/v1/scenarios/flotation-lag-prediction?train_fraction=0.7"
    ).json()
    assert smaller_train_body["testSize"] > default_body["testSize"]
