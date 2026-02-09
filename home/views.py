from django.shortcuts import render,redirect
from blog.models import *


# Create your views here.
def home_Page(request):
    blogs = blog.objects.filter(verify = True).order_by("-verify_at").select_related("key_user")
    not_verify = blog.objects.filter(verify = False).count()
    context ={"blogs":blogs,"not_verify":not_verify}
    return render(request,'base.html',context)
