import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Reset the dev database, run migrations, and create a default superuser in the admin group."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin")
        parser.add_argument("--email", default="admin@example.com")
        parser.add_argument("--password", default="admin")

    def handle(self, *args, **options):
        # 1. Delete the SQLite database
        db_path = settings.DATABASES["default"]["NAME"]
        if os.path.exists(db_path):
            os.remove(db_path)
            self.stdout.write(self.style.WARNING(f"Deleted {db_path}"))

        # 2. Run migrations
        self.stdout.write("Running migrations...")
        call_command("migrate", verbosity=1)

        # 3. Create superuser
        User = get_user_model()
        username = options["username"]
        email = options["email"]
        password = options["password"]

        user = User.objects.create_superuser(username, email, password)
        user.groups.add(Group.objects.get(name="admin"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Superuser created: {username} / {password}"
        ))
        self.stdout.write("Login at /accounts/login/")
