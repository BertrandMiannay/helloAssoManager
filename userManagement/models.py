import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.functional import cached_property


class CustomUser(AbstractUser):
    invite_token = models.UUIDField(null=True, blank=True, unique=True)
    invite_url = models.TextField(null=True, blank=True)

    @cached_property
    def is_administrator(self):
        return self.groups.filter(name='admin').exists()
