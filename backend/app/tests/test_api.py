from __future__ import annotations

import os
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


TEST_DB_PATH = Path(tempfile.gettempdir()) / f"aivoa_test_{uuid4().hex}.db"

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["SEED_ON_STARTUP"] = "true"
os.environ["GROQ_API_KEY"] = ""

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_bootstrap_returns_seeded_reference_data(client: TestClient):
    response = client.post("/api/bootstrap", json={})
    assert response.status_code == 200
    payload = response.json()

    assert payload["session_id"]
    assert payload["draft"]["interaction_type"] == "Meeting"
    assert len(payload["hcps"]) >= 5
    assert len(payload["materials"]) >= 5
    assert payload["messages"][0]["role"] == "assistant"


def test_api_root_returns_endpoint_index(client: TestClient):
    response = client.get("/api")
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "running"
    assert payload["endpoints"]["bootstrap_get"] == "/api/bootstrap"
    assert payload["endpoints"]["chat"] == "/api/sessions/{session_id}/chat"


def test_log_and_edit_flow_only_updates_requested_fields(client: TestClient):
    bootstrap = client.post("/api/bootstrap", json={}).json()
    session_id = bootstrap["session_id"]

    log_response = client.post(
        f"/api/sessions/{session_id}/chat",
        json={
            "message": (
                "Met Dr. Anita Sharma today at 19:36, discussed Product X efficacy, "
                "positive sentiment, shared brochure and sample kit, agreed to review the data."
            )
        },
    )
    assert log_response.status_code == 200
    logged = log_response.json()

    assert logged["draft"]["hcp_name"] == "Dr. Anita Sharma"
    assert logged["draft"]["interaction_time"] == "19:36"
    assert logged["draft"]["sentiment"] == "positive"
    assert "Product X efficacy brochure" in logged["draft"]["materials_shared"]
    assert "Starter sample kit" in logged["draft"]["samples_distributed"]

    edit_response = client.post(
        f"/api/sessions/{session_id}/chat",
        json={"message": "Update the sentiment to neutral and change the time to 20:10."},
    )
    assert edit_response.status_code == 200
    edited = edit_response.json()

    assert edited["draft"]["hcp_name"] == "Dr. Anita Sharma"
    assert edited["draft"]["interaction_time"] == "20:10"
    assert edited["draft"]["sentiment"] == "neutral"
    assert edited["draft"]["interaction_type"] == "Meeting"


def test_save_interaction_persists_to_database(client: TestClient):
    bootstrap = client.post("/api/bootstrap", json={}).json()
    session_id = bootstrap["session_id"]

    client.post(
        f"/api/sessions/{session_id}/chat",
        json={
            "message": (
                "Met Dr. Rajiv Menon on 22-04-2026 at 10:30, discussed dosing guide, "
                "positive sentiment, shared brochure, outcome was that he requested a follow-up next week."
            )
        },
    )

    save_response = client.post(
        f"/api/sessions/{session_id}/chat",
        json={"message": "Save the interaction."},
    )
    assert save_response.status_code == 200
    payload = save_response.json()

    assert payload["last_saved_interaction_id"] is not None
    assert payload["validation"]["is_valid"] is True

    interactions = client.get("/api/interactions")
    assert interactions.status_code == 200
    assert any(item["id"] == payload["last_saved_interaction_id"] for item in interactions.json()["items"])
