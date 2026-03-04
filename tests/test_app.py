"""
Tests for the Mergington High School Activities API.
Uses pytest with AAA (Arrange-Act-Assert) pattern.
"""

import pytest
from copy import deepcopy
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Fixture to reset activities state before and after each test.
    This ensures test isolation.
    """
    # Store original state
    original_activities = deepcopy(activities)
    
    yield  # Run the test
    
    # Restore original state
    activities.clear()
    activities.update(original_activities)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_200(self, client):
        """Arrange-Act-Assert: Verify activities endpoint returns 200."""
        # Arrange: client is ready
        
        # Act: fetch activities
        response = client.get("/activities")
        
        # Assert: response is successful
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_activities(self, client):
        """Arrange-Act-Assert: Verify known activities are returned."""
        # Arrange: activities should have Chess Club, Programming Class, etc.
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Act: fetch activities
        response = client.get("/activities")
        data = response.json()
        
        # Assert: expected activities are in response
        for activity in expected_activities:
            assert activity in data

    def test_get_activities_has_required_fields(self, client):
        """Arrange-Act-Assert: Verify each activity has required fields."""
        # Arrange: we expect certain structure
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act: fetch activities
        response = client.get("/activities")
        data = response.json()
        
        # Assert: each activity has required fields
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data, dict)
            for field in required_fields:
                assert field in activity_data


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_student_success(self, client):
        """Arrange-Act-Assert: Successfully sign up a new student."""
        # Arrange: prepare new email
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        # Act: sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert: signup successful
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        
        # Verify participant was added
        assert email in activities[activity]["participants"]

    def test_signup_duplicate_student_returns_400(self, client):
        """Arrange-Act-Assert: Verify duplicate signup returns 400."""
        # Arrange: use an existing participant
        activity = "Chess Club"
        email = activities[activity]["participants"][0]
        
        # Act: attempt to sign up existing student
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert: returns 400 Bad Request
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Arrange-Act-Assert: Verify signup to nonexistent activity returns 404."""
        # Arrange: activity that does not exist
        fake_activity = "Fake Activity That Does Not Exist"
        email = "student@mergington.edu"
        
        # Act: attempt to sign up
        response = client.post(f"/activities/{fake_activity}/signup?email={email}")
        
        # Assert: returns 404 Not Found
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_updates_participant_list(self, client):
        """Arrange-Act-Assert: Verify signup adds to participants list."""
        # Arrange: known activity and new email
        activity = "Tennis Club"
        email = "newtennis@mergington.edu"
        initial_count = len(activities[activity]["participants"])
        
        # Act: sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert: participant count increased
        assert response.status_code == 200
        assert len(activities[activity]["participants"]) == initial_count + 1
        assert email in activities[activity]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/signup endpoint."""

    def test_remove_participant_success(self, client):
        """Arrange-Act-Assert: Successfully remove a participant."""
        # Arrange: use an existing participant
        activity = "Basketball Team"
        email = activities[activity]["participants"][0]
        
        # Act: remove participant
        response = client.delete(f"/activities/{activity}/signup?email={email}")
        
        # Assert: removal successful
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify participant was removed
        assert email not in activities[activity]["participants"]

    def test_remove_nonexistent_participant_returns_404(self, client):
        """Arrange-Act-Assert: Verify removing nonexistent participant returns 404."""
        # Arrange: email not in participants
        activity = "Art Studio"
        fake_email = "nonexistent@mergington.edu"
        
        # Act: attempt to remove
        response = client.delete(f"/activities/{activity}/signup?email={fake_email}")
        
        # Assert: returns 404
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_remove_from_nonexistent_activity_returns_404(self, client):
        """Arrange-Act-Assert: Verify removing from nonexistent activity returns 404."""
        # Arrange: activity that does not exist
        fake_activity = "Imaginary Club"
        email = "student@mergington.edu"
        
        # Act: attempt to remove
        response = client.delete(f"/activities/{fake_activity}/signup?email={email}")
        
        # Assert: returns 404
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_remove_decreases_participant_count(self, client):
        """Arrange-Act-Assert: Verify participant count decreases after removal."""
        # Arrange: known activity with participants
        activity = "Drama Club"
        email = activities[activity]["participants"][0]
        initial_count = len(activities[activity]["participants"])
        
        # Act: remove participant
        response = client.delete(f"/activities/{activity}/signup?email={email}")
        
        # Assert: participant count decreased
        assert response.status_code == 200
        assert len(activities[activity]["participants"]) == initial_count - 1


class TestRootRedirect:
    """Tests for root endpoint."""

    def test_root_redirects_to_static(self, client):
        """Arrange-Act-Assert: Verify root endpoint redirects to static index."""
        # Arrange: client is ready
        
        # Act: access root without following redirects
        response = client.get("/", follow_redirects=False)
        
        # Assert: returns redirect status
        assert response.status_code in (301, 302, 303, 307, 308)


class TestIntegrationSignupAndRemove:
    """Integration tests combining signup and removal."""

    def test_signup_then_remove_integration(self, client):
        """Arrange-Act-Assert: Sign up a student then remove them."""
        # Arrange: prepare activity and email
        activity = "Robotics Club"
        email = "robotfan@mergington.edu"
        initial_count = len(activities[activity]["participants"])
        
        # Act: signup
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        assert len(activities[activity]["participants"]) == initial_count + 1
        
        # Act: remove
        remove_response = client.delete(f"/activities/{activity}/signup?email={email}")
        
        # Assert: back to original count
        assert remove_response.status_code == 200
        assert len(activities[activity]["participants"]) == initial_count
        assert email not in activities[activity]["participants"]

    def test_multiple_signups_and_removals(self, client):
        """Arrange-Act-Assert: Handle multiple signup/removal operations."""
        # Arrange: prepare emails and activity
        activity = "Debate Team"
        emails = ["debater1@mergington.edu", "debater2@mergington.edu", "debater3@mergington.edu"]
        initial_count = len(activities[activity]["participants"])
        
        # Act: sign up multiple students
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Assert: all signed up
        assert len(activities[activity]["participants"]) == initial_count + 3
        
        # Act: remove first and last
        client.delete(f"/activities/{activity}/signup?email={emails[0]}")
        client.delete(f"/activities/{activity}/signup?email={emails[2]}")
        
        # Assert: correct count, middle one still there
        assert len(activities[activity]["participants"]) == initial_count + 1
        assert emails[0] not in activities[activity]["participants"]
        assert emails[1] in activities[activity]["participants"]
        assert emails[2] not in activities[activity]["participants"]
