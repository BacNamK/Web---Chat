from django.shortcuts import render,redirect
from . import views
from .models import *

# Create your views here.
app_name = 'blog'

def get_blog(request):
    return render (request,"Blogs/blogDetail.html")
def create_blog(request):
    return render (request,"base.html")

def post_Blog(request):
    if request.method =="POST":
            blog.objects.create(
            key_user = request.user,
            title = request.POST.get("title"),
            content = request.POST.get("content"),
            image = request.FILES.get("image")
            )
            return redirect('homeapp:home')
    return render ("Blogs/createBlog.html")

def blog_detail(request,uuid):
     blogs = blog.objects.select_related("key_user").get(uuid = uuid)
     context = {"blogD":blogs}
     return render (request,"base.html",context)

