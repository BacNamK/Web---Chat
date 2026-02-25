from django.shortcuts import render,redirect
from blog.models import *


# Create your views here.
def home_Page(request):
    blogD = blog.objects.get()
    blogs = blog.objects.filter(verify = True).order_by("-verify_at").select_related("key_user")
    not_verify = blog.objects.filter(verify = False).count()
    is_liked = blogD.like.filter(id = request.user.id)
    context ={"blogs":blogs,"not_verify":not_verify,"is_liked":is_liked}
    return render(request,'base.html',context)
