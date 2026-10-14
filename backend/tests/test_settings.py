"""
Tests for Orqen backend configuration and settings loading.
"""

from django.test import SimpleTestCase
from django.conf import settings
from django.urls import resolve, reverse
import importlib


class SettingsConfigurationTest(SimpleTestCase):
    """Verify settings are properly configured for development and production."""

    def test_installed_apps_includes_core_and_local(self):
        """Ensure all required core, DRF, and Orqen domain apps are registered."""
        required_apps = [
            'rest_framework',
            'apps.accounts',
            'apps.ai',
            'apps.api_testing',
            'apps.workspaces',
            'apps.code_reviews',
            'apps.debugging',
            'apps.documentation',
            'apps.test_generation',
        ]
        for app in required_apps:
            self.assertIn(app, settings.INSTALLED_APPS, f"Missing required app: {app}")

    def test_rest_framework_settings_configured(self):
        """Ensure DRF configuration is properly structured."""
        self.assertTrue(hasattr(settings, 'REST_FRAMEWORK'))
        rf = settings.REST_FRAMEWORK
        self.assertIn('DEFAULT_PERMISSION_CLASSES', rf)
        self.assertIn('DEFAULT_AUTHENTICATION_CLASSES', rf)
        self.assertIn('DEFAULT_PAGINATION_CLASS', rf)
        self.assertIn('PAGE_SIZE', rf)

    def test_database_engine_is_configured(self):
        """Ensure the default database has an engine configured."""
        self.assertIn('default', settings.DATABASES)
        engine = settings.DATABASES['default']['ENGINE']
        self.assertTrue('postgresql' in engine or 'sqlite3' in engine)

    def test_development_defaults(self):
        """Verify development defaults for DEBUG and ALLOWED_HOSTS."""
        self.assertIsInstance(settings.DEBUG, bool)
        self.assertIsInstance(settings.ALLOWED_HOSTS, list)
        self.assertIn('localhost', settings.ALLOWED_HOSTS)
        self.assertIn('testserver', settings.ALLOWED_HOSTS)

    def test_production_settings_module(self):
        """Verify production module settings enforce security best practices."""
        prod_settings = importlib.import_module('config.settings.production')
        self.assertFalse(prod_settings.DEBUG)
        self.assertTrue(prod_settings.SECURE_BROWSER_XSS_FILTER)
        self.assertTrue(prod_settings.SECURE_CONTENT_TYPE_NOSNIFF)
        self.assertTrue(prod_settings.SESSION_COOKIE_SECURE)
        self.assertTrue(prod_settings.CSRF_COOKIE_SECURE)
        self.assertEqual(prod_settings.X_FRAME_OPTIONS, 'DENY')

    def test_url_routing_resolves(self):
        """Verify root and versioned health routes resolve correctly."""
        root_resolver = resolve('/health/')
        self.assertEqual(root_resolver.view_name, 'root-health-check')

        v1_resolver = resolve('/api/v1/health/')
        self.assertEqual(v1_resolver.view_name, 'v1-health-check')
