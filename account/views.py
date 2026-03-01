from django.shortcuts import render,redirect
from django.contrib.auth import get_user_model,authenticate,login as auth_login
from blog.models import *
from .forms import *
from django.http import JsonResponse

User = get_user_model()

# Create your views here.
def register(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            User = form.save(commit=False)
            User.set_password(form.cleaned_data["password"])
            User.save()
            return redirect("account:login")
    else:
        form = UserForm()
    
    return render(request,"Account/register.html",{"form":form})

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user =  authenticate(request,username = username, password = password)
        print(user)
        if user is not None:
            auth_login(request,user)
            return redirect('home:home')
        else:
            print("thất bại")
    return render(request,"Account/login.html")

def profile(request,id):
    user = User.objects.get(id = id)
    blogs = blog.objects.filter(key_user_id = id, verify = True).order_by("-verify_at")
    context ={"blogs":blogs,"users":user }
    return render(request,"base.html",context)

def update_user(request,id):
    if request.method =="POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        user =  User.objects.get(id = id)
        fields =[]

        new_name = request.POST.get("username")
        if new_name and new_name != user.username:
            user.username = new_name
            fields.append("username")
        avatar = request.FILES.get("avatar")
        if avatar :
            user.avatar = avatar
            fields.append("avatar")
        background = request.FILES.get("background")    
        if background:
            user.background = background
            fields.append("background")
        if fields:
            user.save(update_fields = fields )
            return JsonResponse({"message":"Sửa đổi thành công"},status = 200)
    return JsonResponse({"message":"Sửa đổi không thành công"},status = 400)