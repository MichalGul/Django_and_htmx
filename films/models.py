from django.db import models
from django.contrib.auth.models import AbstractUser

# One can add whaterer want to basic user model
class User(AbstractUser):
    pass


class Film(models.Model):
    name = models.CharField(max_length=200, unique=True)
    users = models.ManyToManyField(User, related_name='films') # user.films.all()

