"""
Tests for root and versioned health-check endpoints.
"""

from unittest.mock import patch
from django.test import SimpleTestCase
from rest_framework.test import APIClient


class HealthCheckEndpointTest(SimpleTestCase):
    """Test health check endpoint behavior for both root and versioned paths."""

    databases = '__all__'

    def setUp(self):
        self.client = APIClient()

    def test_health_check_payload_schema(self):
        """Verify the health check response conforms to the standard contract."""
        response = self.client.get('/health/')
        self.assertIn(response.status_code, [200, 503])
        data = response.json()

        self.assertIn('status', data)
        self.assertIn('service', data)
        self.assertEqual(data['service'], 'orqen-backend')
        self.assertIn('version', data)
        self.assertEqual(data['version'], 'v1')
        self.assertIn('timestamp', data)
        self.assertIn('database', data)
        self.assertIn('status', data['database'])

    def test_versioned_health_check_matches_root(self):
        """Ensure /api/v1/health/ routes to the health check endpoint."""
        response = self.client.get('/api/v1/health/')
        self.assertIn(response.status_code, [200, 503])
        data = response.json()
        self.assertEqual(data['version'], 'v1')

    @patch("config.views.connection.cursor")
    def test_healthy_status_when_database_available(self, mock_cursor):
        mock_cursor.return_value.__enter__.return_value.fetchone.return_value = (1,)

        response = self.client.get("/api/v1/health/")

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["database"]["status"], "ok")

    @patch("config.views.connection.cursor")
    def test_degraded_status_when_database_unusable(self, mock_cursor):
        """Ensure HTTP 503 when the database query fails."""

        mock_cursor.side_effect = Exception("Connection refused")

        response = self.client.get("/api/v1/health/")

        self.assertEqual(response.status_code, 503)

        data = response.json()

        self.assertEqual(data["status"], "degraded")
        self.assertEqual(data["database"]["status"], "error")
        self.assertIn("detail", data["database"])

