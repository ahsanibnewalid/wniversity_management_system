import pytest
from django.test import Client


@pytest.mark.django_db
def test_health_endpoint_reports_database_status():
    response = Client().get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_route_is_public():
    response = Client().get("/healthz")
    assert response.status_code in (200, 503)
