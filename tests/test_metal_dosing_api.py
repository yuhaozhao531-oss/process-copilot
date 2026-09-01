from fastapi.testclient import TestClient

from process_copilot_api.main import app

client = TestClient(app)


def test_metal_dosing_scenario_default() -> None:
    response = client.get("/api/v1/scenarios/metal-dosing-precipitation")
    assert response.status_code == 200
    body = response.json()

    assert body["trainSize"] > 14000
    assert body["testSize"] > 3000
    assert len(body["testHours"]) == body["testSize"]
    assert len(body["featureNames"]) == 9
    assert "不是磷化工数据" in body["disclosure"]
    assert "闭环反馈" in body["disclosure"]
    # 这份数据的真实结果是明显跑赢基线，不只是勉强打平（跟①不同）
    assert body["testMae"] < body["naiveBaselineMae"] * 0.7
    assert body["testR2"] > 0.4
