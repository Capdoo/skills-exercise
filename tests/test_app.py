"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


client = TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Arrange: Client ready
        Act: GET /activities
        Assert: Response status is 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict_with_activities(self):
        """Arrange: Client ready
        Act: GET /activities
        Assert: Response contains activities dictionary with expected keys"""
        response = client.get("/activities")
        activities = response.json()

        assert isinstance(activities, dict)
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert all("description" in details and
                   "schedule" in details and
                   "max_participants" in details and
                   "participants" in details
                   for details in activities.values())


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_returns_200(self):
        """Arrange: Client ready and new email
        Act: POST signup for Chess Club
        Assert: Response status is 200 and success message returned"""
        email = "newstudent@mergington.edu"
        response = client.post(
            f"/activities/Chess Club/signup?email={email}",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "Signed up" in result["message"]
        assert email in result["message"]

    def test_signup_duplicate_participant_returns_400(self):
        """Arrange: Already signed up participant
        Act: POST signup with duplicate email
        Assert: Response status is 400 and error detail provided"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(
            f"/activities/Chess Club/signup?email={email}",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "already signed up" in result["detail"].lower()

    def test_signup_nonexistent_activity_returns_404(self):
        """Arrange: Client ready and non-existent activity
        Act: POST signup for invalid activity
        Assert: Response status is 404"""
        email = "test@mergington.edu"
        response = client.post(
            f"/activities/Nonexistent Activity/signup?email={email}",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""

    def test_remove_existing_participant_returns_200(self):
        """Arrange: Client ready and existing participant
        Act: DELETE participant from activity
        Assert: Response status is 200 and removal confirmed"""
        # First, add a participant
        email = "removetest@mergington.edu"
        client.post(
            f"/activities/Soccer Team/signup?email={email}",
            headers={"Content-Type": "application/json"}
        )

        # Then remove them
        response = client.delete(
            f"/activities/Soccer Team/participants?email={email}"
        )

        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "Removed" in result["message"]
        assert email in result["message"]

    def test_remove_nonexistent_participant_returns_404(self):
        """Arrange: Client ready with non-existent participant email
        Act: DELETE participant not in activity
        Assert: Response status is 404"""
        email = "notinactivity@mergington.edu"
        response = client.delete(
            f"/activities/Soccer Team/participants?email={email}"
        )

        assert response.status_code == 404
        result = response.json()
        assert "Participant not found" in result["detail"]

    def test_remove_from_nonexistent_activity_returns_404(self):
        """Arrange: Client ready with invalid activity
        Act: DELETE participant from non-existent activity
        Assert: Response status is 404"""
        email = "test@mergington.edu"
        response = client.delete(
            f"/activities/Invalid Activity/participants?email={email}"
        )

        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]


class TestIntegrationFlow:
    """Integration tests for signup and removal flow"""

    def test_signup_then_remove_updates_participants_list(self):
        """Arrange: Client ready
        Act: Sign up, get activities, remove, get activities again
        Assert: Participant count changes accordingly"""
        email = "integrationtest@mergington.edu"
        activity = "Art Club"

        # Get initial state
        initial_response = client.get("/activities")
        initial_participants = len(initial_response.json()[activity]["participants"])

        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}",
            headers={"Content-Type": "application/json"}
        )
        assert signup_response.status_code == 200

        # Check participant count increased
        after_signup = client.get("/activities")
        after_signup_count = len(after_signup.json()[activity]["participants"])
        assert after_signup_count == initial_participants + 1

        # Remove participant
        remove_response = client.delete(
            f"/activities/{activity}/participants?email={email}"
        )
        assert remove_response.status_code == 200

        # Check participant count decreased back
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity]["participants"])
        assert final_count == initial_participants
