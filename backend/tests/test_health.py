
import unittest

from app import create_app


class HealthCheckTestCase(unittest.TestCase):
    """
    Test cases for Flask Health Check API.
    """

    def setUp(self):
        # Create a Flask application for testing
        self.app = create_app()

        # Enable Flask testing mode
        self.app.config["TESTING"] = True

        # Create a test HTTP client
        self.client = self.app.test_client()

    def test_health_endpoint_returns_200(self):
        # Act
        response = self.client.get("/api/health")

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_health_endpoint_returns_expected_json(self):
        # Act
        response = self.client.get("/api/health")

        # Assert
        expected_data = {
            "status": "ok",
            "message": (
                "Student Management System API is running"
            ),
        }

        self.assertEqual(
            response.get_json(),
            expected_data
        )

    def test_health_endpoint_rejects_post(self):
        # Act
        response = self.client.post("/api/health")

        # Assert
        self.assertEqual(response.status_code, 405)


if __name__ == "__main__":
    unittest.main()
