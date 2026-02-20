from django.shortcuts import render,redirect
from django.contrib.auth import get_user_model,authenticate,login as auth_login

User = get_user_model()

# Create your views here.
def register(request):
    if request.method == "POST":
        User.objects.create_user(
            username = request.POST.get("username"),
            password = request.POST.get("password"),
            email = request.POST.get("email"),
            status = True
        )

        return redirect("account:login")
    
    return render(request,"Account/register.html")

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

def profile(request):
    return render(request,"Account/profile.html")

def update_user(request,id):

    new_name = request.POST.get("username")
    user =  User.objects.get(id = id)
    if new_name and new_name != user.username:
        user.username = new_name
    if request.FILES :
        user.avatar = request.FILES.get("image")
    user.save()
    return redirect("account:profile")