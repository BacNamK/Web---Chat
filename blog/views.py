from django.shortcuts import render,redirect,get_object_or_404
from . import views
from .models import *
from django.http import JsonResponse
from django.utils import timezone

# Create your views here.
app_name = 'blog'


# Defautl 
 
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

#Action

def like_blog(request, bloguuid):
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        blog_obj = get_object_or_404(blog, uuid=bloguuid)
        user = request.user

        if blog_obj.like.filter(id=user.id).exists():
            blog_obj.like.remove(user)
            liked = False
        else:
            blog_obj.like.add(user)
            liked = True

        return JsonResponse({
            "liked": liked,
            "count": blog_obj.like.count()
        })

    return JsonResponse({"error": "Invalid request"}, status=400)

def comment_blog(request,bloguuid):
    if request.method == 'POST' and request.headers.get("x-requested-with") == "XMLHttpRequest":
        blog_obj = get_object_or_404(blog, uuid = bloguuid)
        user = request.user

        content = request.POST.get('content')
        image = request.FILES.get('image')
        parent_id = request.POST.get('parent_id')

        if content or image:
            new_comment = comment.objects.create(
                content = content,
                image = image,
                key_user = user,
                key_blog = blog_obj,
                parent_id = parent_id if parent_id else None
            )
            return JsonResponse({
                "username": new_comment.key_user.username,
                "content": new_comment.content,
                "image_url": new_comment.image.url if new_comment.image else None
            })
    return JsonResponse({"error": "Invalid request"}, status=400)

# Censor Blog

def censor_blog(request):
    blogs = blog.objects.filter(verify = False).select_related("key_user").order_by("-create_at")
    not_verify = blog.objects.filter(verify = False).count()
    context ={"blogs":blogs,"not_verify":not_verify}
    return render (request,"base.html",context)

def approve_blog(request,bloguuid):
    blogs = blog.objects.get(uuid = bloguuid)
    blogs.verify = True
    blogs.verify_at = timezone.now()
    blogs.save(update_fields=["verify","verify_at"])
    return redirect("blog:censor_blog")

def delete_blog(request,bloguuid):
    blogs = blog.objects.get(uuid = bloguuid)
    blogs.delete()
    return redirect("blog:censor_blog")