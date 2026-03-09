from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """Custom user model — extend here for future fields."""
    pass
