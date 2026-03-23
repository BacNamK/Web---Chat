from django.dispatch import receiver

from .models import *
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Prefetch,Count
from django.shortcuts import render,redirect,get_object_or_404
from notification.service import push_notification
from home.models import Report

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
            image = request.FILES.get("image"),
            video = request.FILES.get("video")
            )
            return redirect('homeapp:home')
    return render ("Blogs/createBlog.html")

def blog_detail(request,uuid):
    next_url = request.GET.get("from") 


    replies_queryset = comment.objects.select_related("key_user")

    root_comments_qs = comment.objects.filter(parent__isnull=True) \
    .select_related("key_user") \
    .annotate(reply_count=Count("replies"))

    blogs = blog.objects.prefetch_related(
        Prefetch("comments",queryset=root_comments_qs,
                to_attr="root_comments"),
        Prefetch("comments__replies",queryset=replies_queryset),
        Prefetch("comments__replies__replies",queryset=replies_queryset)
    ).get(uuid = uuid)
    is_liked = blogs.like.filter(id = request.user.id)
    context = {"blogD":blogs,"from":next_url,"is_liked":is_liked}

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
        
        if liked and blog_obj.key_user != user:
            push_notification(
                sender=user,
                receiver=blog_obj.key_user,
                type="like",
                content=f"{user.username} đã thích bài viết của bạn",
                url=f"/blog/{bloguuid}",
                obj=blog_obj
            )

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

            # Push notification
            if parent_id:
                # phản hồi
                parent_comment = comment.objects.get(id=parent_id)
                if parent_comment.key_user != user:
                    push_notification(
                        sender=user,
                        receiver=parent_comment.key_user,
                        type="reply",
                        content=f"{user.username} đã phản hồi bình luận của bạn",
                        url=f"/blog/{bloguuid}?from=reply-{new_comment.id}",
                        obj=new_comment
                    )
            else:
                # bình luận
                if blog_obj.key_user != user:
                    push_notification(
                        sender=user,
                        receiver=blog_obj.key_user,
                        type="comment",
                        content=f"{user.username} đã bình luận bài viết của bạn",
                        url=f"/blog/{bloguuid}?from=comment-{new_comment.id}",
                        obj=new_comment
                    )

            return JsonResponse({
                "username": new_comment.key_user.username,
                "avatar_user": new_comment.key_user.avatar.url if  new_comment.key_user.avatar else None,
                "content": new_comment.content,
                "image_url": new_comment.image.url if new_comment.image else None
            })
    return JsonResponse({"error": "Invalid request"}, status=400)

def like_comment(request,id):
    if request.method == 'POST' and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        print('a')
        cm = get_object_or_404(comment,id = id)
        user = request.user

        if cm.like.filter(id =user.id).exists():
            cm.like.remove(user)
            liked = False
        else:
            cm.like.add(user)
            liked = True

        if liked and cm.key_user != user:
            push_notification(
                sender=user,
                receiver=cm.key_user,
                type="like",
                content=f"{user.username} đã thích bình luận của bạn",
                url=f"/blog/{cm.key_blog.uuid}",
                obj=cm
            )
        
        return JsonResponse({
            "liked":liked,
            "count": cm.like.count()
        })
    return JsonResponse({"error": "Invalid request"}, status=400)

def delete_comment(request, id):
    if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        cm = get_object_or_404(comment, id=id)

        if cm.key_user == request.user or cm.key_blog.key_user == request.user:
            cm.delete()
            return JsonResponse({'status': 'success'}, status=200)

        return JsonResponse({'status': 'forbidden'}, status=403)

    return JsonResponse({'status': 'error'}, status=400)

def report_comment(request, id):
    if request.method == "POST":
        cm = get_object_or_404(comment, id=id)
        reason = (request.POST.get("reason") or "").strip()
        if not reason:
            reason = "Không có lý do"

        Report.objects.create(
            reporter=request.user,
            target_user=cm.key_user,
            target_id=str(cm.id),
            reason=reason,
        )

        return redirect("blog:blog_detail", uuid=cm.key_blog.uuid)

    return redirect("blog:blog_detail", uuid=cm.key_blog.uuid)

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

    push_notification(
            sender=request.user,
            receiver=blogs.key_user,
            type="system",
            content="Bài viết của bạn đã được duyệt",
        url=f"/blog/{bloguuid}",
            obj=blogs
        )
    return redirect("blog:censor_blog")

def delete_blog_censor(request,bloguuid):

    next_url = request.GET.get("from")

    blogs = blog.objects.get(uuid = bloguuid)
    blogs.delete()

    if next_url :
        print(next_url)
        return redirect("account:profile")
    return redirect("blog:censor_blog")

def delete_blog_user(request,bloguuid):
    blogs = blog.objects.get(uuid = bloguuid)
    blogs.delete()
    return redirect("homeapp:home")

def start_blog(request,uuid):
    blog_taget = get_object_or_404(blog,uuid = uuid)
    blog_taget.star = True
    blog_taget.save(update_fields=["star"])
    return render(request,"base.html")
