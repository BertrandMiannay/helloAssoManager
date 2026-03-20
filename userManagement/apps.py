from django.apps import AppConfig


class UsermanagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'userManagement'

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(_create_default_groups, sender=self)


def _create_default_groups(sender, **kwargs):
    from django.contrib.auth.models import Group
    for name in ['member', 'instructor', 'dive_director', 'admin']:
        Group.objects.get_or_create(name=name)
