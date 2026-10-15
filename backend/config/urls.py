"""
URL configuration for Orqen backend.
"""

from django.contrib import admin
from django.urls import path, include
from config.views import HealthCheckView

urlpatterns = [
    # Administration
    path('admin/', admin.site.urls),

    # Root health-check endpoint (for load balancers, container probes, and monitors)
    path('health/', HealthCheckView.as_view(), name='root-health-check'),

    # Versioned API routes
    path('api/v1/', include([
        path('health/', HealthCheckView.as_view(), name='v1-health-check'),
        path('', include('apps.accounts.urls'))
    ])),
]
