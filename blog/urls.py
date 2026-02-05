from django.urls import path,include
from . import views
from django.contrib.auth import views as logout
app_name = "blog"

urlpatterns = [
    path('',views.get_blog,name='blog'),
    path('create_blog',views.create_blog,name='create_blog'),
    path("post_blog",views.post_Blog,name="post_blog"),
    path("<uuid:uuid>",views.blog_detail,name="blog_detail")
]