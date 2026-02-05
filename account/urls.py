from django.urls import path,include
from . import views
from django.contrib.auth import views as logout
app_name = "account"

urlpatterns = [
    path("register",views.register,name="register"),
    path("login",views.login_view,name="login"),
    path("profile",views.profile,name="profile"),
    path("updateuser/<int:id>",views.update_user,name="updateuser"),
    path("logout/",logout.LogoutView.as_view(),name="logout")
]

