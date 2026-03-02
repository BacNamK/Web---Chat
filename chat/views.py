from django.shortcuts import render

# Create your views here.

def room(request, room_name="community"):
    return render(request, "base.html"  , {
        "room_name": room_name
    })