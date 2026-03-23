from django.db import models
from django.conf import settings

# Create your models here.
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    status = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatar/',default='avatar/user.png',blank=True,null= True)
    background = models.ImageField(upload_to='background_user/',blank=True,null=True)
    last_seen = models.DateTimeField(blank=True, null=True)
