from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


INITIAL_ACTIVITIES = deepcopy(app_module.activities)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(INITIAL_ACTIVITIES))
    return TestClient(app_module.app)


def signup(client, activity_name, email):
    encoded_activity = quote(activity_name, safe="")
    return client.post(
        f"/activities/{encoded_activity}/signup",
        params={"email": email},
    )


def test_successful_signup_adds_participant(client):
    email = "new-student@example.edu"

    response = signup(client, "Chess Club", email)

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in app_module.activities["Chess Club"]["participants"]


def test_duplicate_signup_is_rejected(client):
    email = "new-student@example.edu"
    signup(client, "Chess Club", email)

    response = signup(client, "Chess Club", email)

    assert response.status_code == 409
    assert response.json()["detail"] == "Already signed up for this activity"


def test_full_activity_signup_is_rejected(client):
    activity = app_module.activities["Chess Club"]
    activity["participants"] = [
        f"student{index}@example.edu" for index in range(activity["max_participants"])
    ]

    response = signup(client, "Chess Club", "new-student@example.edu")

    assert response.status_code == 409
    assert response.json()["detail"] == "Activity is full"


def test_blank_email_is_rejected(client):
    response = signup(client, "Chess Club", "   ")

    assert response.status_code == 422
    assert response.json()["detail"] == "Email must not be empty"


def test_unknown_activity_is_rejected(client):
    response = signup(client, "Unknown Club", "new-student@example.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_same_email_can_join_different_activities(client):
    email = "new-student@example.edu"

    chess_response = signup(client, "Chess Club", email)
    gym_response = signup(client, "Gym Class", email)

    assert chess_response.status_code == 200
    assert gym_response.status_code == 200
    assert email in app_module.activities["Chess Club"]["participants"]
    assert email in app_module.activities["Gym Class"]["participants"]