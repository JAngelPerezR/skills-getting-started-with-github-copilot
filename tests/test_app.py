"""
Tests for the Mergington High School API
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


def test_root_redirect(client):
    """Test that root endpoint redirects to static index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    
    # Should return a dictionary of activities
    assert isinstance(data, dict)
    
    # Check that some expected activities exist
    assert "Chess Club" in data
    assert "Basketball Team" in data
    assert "Tennis Club" in data
    
    # Check structure of an activity
    chess_club = data["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)


def test_signup_for_activity_success(client):
    """Test successfully signing up for an activity"""
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "newstudent@mergington.edu" in data["message"]
    assert "Chess Club" in data["message"]
    
    # Verify participant was added
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_for_nonexistent_activity(client):
    """Test signing up for an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent Club/signup",
        params={"email": "student@mergington.edu"}
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_signup_already_registered(client):
    """Test signing up when already registered"""
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Already in Chess Club
    
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response.status_code == 400
    data = response.json()
    assert "already signed up" in data["detail"]


def test_unregister_success(client):
    """Test successfully unregistering from an activity"""
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    
    # Verify participant exists before unregister
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email in activities[activity_name]["participants"]
    
    # Unregister
    response = client.post(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    assert response.status_code == 200
    data = response.json()
    assert "Unregistered" in data["message"]
    assert email in data["message"]
    
    # Verify participant was removed
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert email not in activities[activity_name]["participants"]


def test_unregister_nonexistent_activity(client):
    """Test unregistering from an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent Club/unregister",
        params={"email": "student@mergington.edu"}
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_unregister_not_registered(client):
    """Test unregistering when not registered"""
    activity_name = "Chess Club"
    email = "notstudent@mergington.edu"  # Not in any activity
    
    response = client.post(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    assert response.status_code == 400
    data = response.json()
    assert "not signed up" in data["detail"]


def test_multiple_signups_and_unregisters(client):
    """Test multiple signup and unregister operations"""
    activity_name = "Drama Club"
    emails = ["test1@mergington.edu", "test2@mergington.edu", "test3@mergington.edu"]
    
    # Sign up multiple students
    for email in emails:
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
    
    # Verify all are registered
    activities_response = client.get("/activities")
    activities = activities_response.json()
    for email in emails:
        assert email in activities[activity_name]["participants"]
    
    # Unregister one student
    response = client.post(
        f"/activities/{activity_name}/unregister",
        params={"email": emails[0]}
    )
    assert response.status_code == 200
    
    # Verify only one was removed
    activities_response = client.get("/activities")
    activities = activities_response.json()
    assert emails[0] not in activities[activity_name]["participants"]
    assert emails[1] in activities[activity_name]["participants"]
    assert emails[2] in activities[activity_name]["participants"]
