from django.shortcuts import render,get_object_or_404
from django.http import JsonResponse
from .models import Message, Room

# Create your views here.

def room(request, room_name="community"):
    messages = Message.objects.select_related("user").order_by("created_at")

    previous_user = None
    for m in messages:
        m.show_user = m.user != previous_user
        previous_user = m.user
    return render(request, "base.html"  , {
        "room_name": room_name,
        "messages": messages,
    })
