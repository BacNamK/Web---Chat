from django.shortcuts import render,redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_GET
from blog.models import *
from notification.models import *
from .models import Report


# Create your views here.
def home_Page(request):
    if not request.user.is_authenticated:
        return redirect("account:register")

    blogs = blog.objects.filter(verify = True).order_by("-verify_at").select_related("key_user")
    not_verify = blog.objects.filter(verify = False).count()

    notifications = Notification.objects.filter(receiver = request.user.id)

    blogstar = blog.objects.filter(star = True).order_by("-verify_at")

    liked_blog_ids = set(
        blogs.filter(like=request.user).values_list("id", flat=True)
    )

    context ={
        "blogs":blogs,
        "not_verify":not_verify,
        "notifications":notifications,
        "blogStar":blogstar,
        "liked_blog_ids": liked_blog_ids,
    }
    
    return render(request,'base.html',context)

def report_page(request):
    if not request.user.is_authenticated:
        return redirect("account:register")
    if request.method == "POST":
        action = (request.POST.get("action") or "").strip()
        report_id = request.POST.get("report_id")

        if report_id:
            report = get_object_or_404(Report, id=report_id)
            if action == "delete_comment":
                if report.target_id:
                    comment.objects.filter(id=report.target_id).delete()
                report.delete()
            elif action == "dismiss":
                report.delete()

        return redirect("homeapp:reports")

    reports = (
        Report.objects.select_related("reporter", "target_user")
        .order_by("-created_at")
    )

    comment_ids = [r.target_id for r in reports if r.target_id]
    comments_map = {
        str(c.id): c
        for c in comment.objects.filter(id__in=comment_ids)
        .select_related("key_user", "key_blog")
    }

    report_items = []
    for r in reports:
        report_items.append(
            {
                "report": r,
                "comment": comments_map.get(str(r.target_id)),
            }
        )

    context = {
        "report_items": report_items,
        "report_count": len(report_items),
    }
    return render(request, "base.html", context)

@require_GET
def search(request):
    query = (request.GET.get("q") or "").strip()
    if not query:
        return JsonResponse({"users": [], "blogs": []})

    User = get_user_model()

    users_qs = (
        User.objects.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        )
        .order_by("username")[:8]
    )

    users = []
    for user in users_qs:
        avatar_url = ""
        if user.avatar:
            avatar_url = user.avatar.url
        users.append(
            {
                "id": user.id,
                "username": user.username,
                "avatar": avatar_url,
            }
        )

    blogs_qs = (
        blog.objects.filter(verify=True)
        .filter(Q(title__icontains=query) | Q(content__icontains=query))
        .select_related("key_user")
        .order_by("-verify_at")[:8]
    )

    blogs = []
    for item in blogs_qs:
        blogs.append(
            {
                "uuid": str(item.uuid),
                "title": item.title,
                "content": (item.content or "")[:180],
                "user": {
                    "id": item.key_user.id,
                    "username": item.key_user.username,
                },
            }
        )

    return JsonResponse({"users": users, "blogs": blogs})
