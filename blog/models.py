import uuid
from django.db import models
from django.conf import settings

# Create your models here.
class blog(models.Model):
    key_user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete = models.CASCADE,related_name='blog')
    uuid = models.UUIDField(default=uuid.uuid4,editable=False,unique=True)
    title = models.CharField(max_length=150)
    content = models.TextField(blank=True,null=True)
    image = models.ImageField(upload_to='blog_image/',blank=True,null=True)
    video = models.FileField(upload_to='blog_video/',blank=True,null=True)
    like = models.ManyToManyField(settings.AUTH_USER_MODEL,related_name="like_blog",blank=True)
    create_at = models.DateTimeField(auto_now_add=True)
    verify = models.BooleanField(default=False)
    verify_at = models.DateTimeField(null=True, blank=True, db_index=True)

    def __str__(self):
        return self.title
    
class comment(models.Model):
    key_blog = models.ForeignKey(blog,on_delete=models.CASCADE,related_name='comments')
    key_user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="comments")
    parent = models.ForeignKey('self',on_delete=models.CASCADE, blank=True, null=True ,related_name="replies")
    content = models.TextField(blank=False,null=True)
    like = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="like_comments",blank=True )
    image = models.ImageField(upload_to='img_comments',blank=True,null=True)
    date_up = models.DateTimeField(auto_now_add=True)