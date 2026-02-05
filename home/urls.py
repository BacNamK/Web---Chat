from django.urls import path,include
from . import views

app_name = "homeapp"

urlpatterns = [
    path("",views.home_Page,name="home"),
    path("create_blog",views.home_Page,name="create_blog")
]