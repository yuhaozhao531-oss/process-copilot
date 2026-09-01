from fastapi.testclient import TestClient

from process_copilot_api.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_simulate_within_cap() -> None:
    payload = {
        "lines": [
            {"id": "map_dap", "name": "磷肥支路", "requestedP2o5Tpd": 100.0},
            {"id": "ppa", "name": "净化磷酸支路", "requestedP2o5Tpd": 50.0},
        ],
        "gypsumCapTpd": 1000.0,
    }
    response = client.post("/api/v1/capacity-plan/simulate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["requestWithinCap"] is True
    assert len(body["options"]) == 1
    assert "调用方传入" in body["disclosure"]


def test_simulate_over_cap_returns_mitigation_options() -> None:
    payload = {
        "lines": [
            {"id": "map_dap", "name": "磷肥支路", "requestedP2o5Tpd": 100.0, "priority": 1},
            {"id": "ppa", "name": "净化磷酸支路", "requestedP2o5Tpd": 100.0, "priority": 5},
        ],
        "gypsumCapTpd": 400.0,
    }
    response = client.post("/api/v1/capacity-plan/simulate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["requestWithinCap"] is False
    assert [option["strategy"] for option in body["options"]] == [
        "proportional",
        "proportional",
        "priority_first",
        "equal_share",
    ]


def test_simulate_rejects_empty_lines() -> None:
    response = client.post(
        "/api/v1/capacity-plan/simulate",
        json={"lines": [], "gypsumCapTpd": 1000.0},
    )
    assert response.status_code == 422
