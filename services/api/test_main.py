"""Unit tests for the analytics ingest API."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_aggregate_counts_and_sums_events():
    payload = {"events": [{"kind": "click", "value": 1.5}, {"kind": "view", "value": 2.5}]}
    resp = client.post("/aggregate", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    assert body["sum"] == 4.0
    assert "received_at" in body


def test_stats_computes_min_max_mean_stddev():
    resp = client.post("/stats", json={"values": [2.0, 4.0, 6.0]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 3
    assert body["min"] == 2.0
    assert body["max"] == 6.0
    assert body["mean"] == 4.0
    # population stddev of [2,4,6] = sqrt(8/3) ≈ 1.632993
    assert abs(body["stddev"] - 1.632993) < 1e-5


def test_stats_single_value_has_zero_stddev():
    resp = client.post("/stats", json={"values": [5.0]})
    assert resp.status_code == 200
    assert resp.json()["stddev"] == 0.0


def test_stats_rejects_empty():
    resp = client.post("/stats", json={"values": []})
    assert resp.status_code == 400
