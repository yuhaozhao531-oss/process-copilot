from fastapi.testclient import TestClient

from process_copilot_api.main import app

client = TestClient(app)


def test_leachate_scenario_default() -> None:
    response = client.get("/api/v1/environmental-scenarios/jiaoyishan-leachate")
    assert response.status_code == 200
    body = response.json()

    assert len(body["series"]["dayIndex"]) == 180
    assert set(body["series"]["series"].keys()) == {
        "membrane_anomaly_score",
        "conductivity_us_cm",
        "slope_displacement_mm",
        "leachate_level_m",
        "ph",
        "total_phosphorus_mg_l",
    }
    assert body["earlyWarning"]["triggered"] is True
    assert body["earlyWarning"]["leadTimeDays"] > 0
    assert "合成示意数据" in body["disclosure"]
    assert len(body["citations"]) == 3
    assert len(body["variables"]) == 6


def test_leachate_scenario_seed_changes_result() -> None:
    default = client.get("/api/v1/environmental-scenarios/jiaoyishan-leachate").json()
    other = client.get("/api/v1/environmental-scenarios/jiaoyishan-leachate?seed=7").json()
    assert default["series"]["series"]["total_phosphorus_mg_l"] != other["series"]["series"]["total_phosphorus_mg_l"]


def test_leachate_scenario_same_seed_is_deterministic() -> None:
    first = client.get("/api/v1/environmental-scenarios/jiaoyishan-leachate?seed=99").json()
    second = client.get("/api/v1/environmental-scenarios/jiaoyishan-leachate?seed=99").json()
    assert first == second
