import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="session")
def client():
    return TestClient(app)


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
