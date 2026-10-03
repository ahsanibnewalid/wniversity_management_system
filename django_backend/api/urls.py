from django.urls import path
from .views import healthz,register,login,me,logout,logout_all,institutions,my_institutions,join_institution,profile
urlpatterns=[
 path("auth/register",register),path("auth/login",login),path("auth/me",me),path("auth/logout",logout),path("auth/logout-all",logout_all),
 path("institutions",institutions),path("institutions/<int:iid>/join",join_institution),path("my/institutions",my_institutions),path("profile",profile),
]
