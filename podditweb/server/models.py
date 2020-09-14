from django.contrib.auth.models import User
from django.db import models


class PodditUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # custom fields for user
