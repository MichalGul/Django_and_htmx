from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.functions import Lower
# One can add whaterer want to basic user model
class User(AbstractUser):
    pass


class Film(models.Model):
    name = models.CharField(max_length=200, unique=True)
    users = models.ManyToManyField(User, related_name='films', through="UserFilms") # user.films.all()
    photo = models.ImageField(upload_to='film_photo/', null=True, blank=True)

    class Meta:
        ordering = [Lower('name')]

# Explicit junction table between films and users
class UserFilms(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['order']