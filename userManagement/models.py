import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    invite_token = models.UUIDField(null=True, blank=True, unique=True)
    invite_url = models.TextField(null=True, blank=True)
