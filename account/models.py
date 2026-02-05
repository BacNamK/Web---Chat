from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    status = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatar/',blank=True,null= True)
    background = models.ImageField(upload_to='background_user/',blank=True,null=True)
