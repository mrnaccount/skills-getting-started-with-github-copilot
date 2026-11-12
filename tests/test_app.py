from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


ACTIVITY_NAME = "Chess Club"
ACTIVITY_URL = f"/activities/{quote(ACTIVITY_NAME, safe='')}"
REGISTERED_EMAIL = "registered@mergington.edu"

TEST_ACTIVITIES = {
    ACTIVITY_NAME: {
        "description": "Test activity",
        "schedule": "Fridays",
        "max_participants": 2,
        "participants": [REGISTERED_EMAIL],
    }
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(TEST_ACTIVITIES))
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == TEST_ACTIVITIES


def test_signup_adds_participant(client):
    email = "newstudent@mergington.edu"

    response = client.post(
        f"{ACTIVITY_URL}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {ACTIVITY_NAME}"}
    assert email in client.get("/activities").json()[ACTIVITY_NAME]["participants"]


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        f"{ACTIVITY_URL}/signup",
        params={"email": REGISTERED_EMAIL},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown/signup",
        params={"email": "newstudent@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_full_activity(client):
    first_signup = client.post(
        f"{ACTIVITY_URL}/signup",
        params={"email": "secondstudent@mergington.edu"},
    )
    full_signup = client.post(
        f"{ACTIVITY_URL}/signup",
        params={"email": "thirdstudent@mergington.edu"},
    )

    assert first_signup.status_code == 200
    assert full_signup.status_code == 400
    assert full_signup.json()["detail"] == "Activity is full"


def test_unregister_removes_participant(client):
    response = client.delete(
        f"{ACTIVITY_URL}/signup",
        params={"email": REGISTERED_EMAIL},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {REGISTERED_EMAIL} from {ACTIVITY_NAME}"
    }
    assert REGISTERED_EMAIL not in client.get("/activities").json()[ACTIVITY_NAME]["participants"]


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown/signup",
        params={"email": REGISTERED_EMAIL},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_unregistered_participant(client):
    response = client.delete(
        f"{ACTIVITY_URL}/signup",
        params={"email": "unknown@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
