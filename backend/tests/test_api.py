"""Smoke tests for the FastAPI endpoints."""
import json
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

BASIC_PROJECT = {
    "name": "Test Enclosure",
    "parameters": [
        {"name": "L",    "value": 100},
        {"name": "W",    "value": 60},
        {"name": "H",    "value": 40},
        {"name": "wall", "value": 2},
    ],
    "features": [
        {
            "type": "enclosure",
            "id": "body",
            "length": "L",
            "width":  "W",
            "height": "H",
            "wall":   "wall",
            "cutouts": [],
            "bosses": [],
            "screw_holes": [],
        }
    ],
}


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_validate_ok(client):
    r = client.post("/api/validate", json=BASIC_PROJECT)
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is True
    assert data["errors"] == []


def test_validate_bad_wall(client):
    proj = dict(BASIC_PROJECT)
    proj["features"] = [dict(BASIC_PROJECT["features"][0], wall=60)]
    r = client.post("/api/validate", json=proj)
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is False
    assert any("wall" in e for e in data["errors"])


def test_preview_returns_bytes(client):
    r = client.post("/api/preview", json=BASIC_PROJECT)
    assert r.status_code == 200
    assert len(r.content) > 0


def test_export_step(client):
    r = client.post("/api/export/step", json=BASIC_PROJECT)
    assert r.status_code == 200
    assert b"ISO-10303" in r.content


def test_export_stl(client):
    r = client.post("/api/export/stl", json=BASIC_PROJECT)
    assert r.status_code == 200
    assert len(r.content) > 0


def test_export_glb(client):
    r = client.post("/api/export/glb", json=BASIC_PROJECT)
    assert r.status_code in (200, 501)
    if r.status_code == 200:
        assert len(r.content) > 0


def test_export_3mf_not_faked(client):
    r = client.post("/api/export/3mf", json=BASIC_PROJECT)
    assert r.status_code in (400, 404, 405, 422)


def test_export_bad_format(client):
    r = client.post("/api/export/obj", json=BASIC_PROJECT)
    assert r.status_code in (400, 404, 405, 422)


def test_preview_invalid_project_rejected(client):
    bad = dict(BASIC_PROJECT)
    bad["features"] = [dict(BASIC_PROJECT["features"][0], wall=60)]
    r = client.post("/api/preview", json=bad)
    assert r.status_code == 422


def test_example_json_validates(client):
    example_path = os.path.join(
        os.path.dirname(__file__), "../../examples/enclosure_basic.json"
    )
    with open(example_path) as f:
        proj = json.load(f)
    r = client.post("/api/validate", json=proj)
    assert r.status_code == 200
    assert r.json()["valid"] is True
