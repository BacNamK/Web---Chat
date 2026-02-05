from django.shortcuts import render,redirect
from blog.models import *


# Create your views here.
def home_Page(request):
    blogs = blog.objects.order_by("-create_at").select_related("key_user")
    context ={"blogs":blogs}
    return render(request,'base.html',context)
