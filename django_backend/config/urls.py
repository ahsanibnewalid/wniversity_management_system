from django.urls import include, path
from django_backend.api.views import healthz
urlpatterns = [
    path("healthz", healthz),
    path("api/v1/", include("django_backend.api.urls")),
]
