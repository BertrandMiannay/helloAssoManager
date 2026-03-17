from django.apps import AppConfig


class HelloassoimporterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'helloAssoImporter'

    def ready(self):
        from common.api.helloAssoApi import init_hello_asso_api
        init_hello_asso_api()
