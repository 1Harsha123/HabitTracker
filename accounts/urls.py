from django.urls import path
from .views import signup_view, login_view, logout_view,forgot_password

urlpatterns = [
    path("", signup_view, name="signup"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("forgot_password/", forgot_password, name="forgot_password"),
]
