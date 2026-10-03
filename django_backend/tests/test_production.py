import os

import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_health_endpoint_reports_database_status():
    response = Client().get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_production_settings_are_safe(monkeypatch):
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("ALLOWED_HOSTS", "example.com")
    from importlib import reload
    from django_backend.config import settings
    reload(settings)
    assert settings.DEBUG is False
    assert settings.ALLOWED_HOSTS == ["example.com"]
    assert settings.SECURE_SSL_REDIRECT is True
    assert settings.SESSION_COOKIE_SECURE is True
    assert settings.CSRF_COOKIE_SECURE is True


def test_health_route_is_public():
    response = Client().get("/healthz")
    assert response.status_code in (200, 503)
