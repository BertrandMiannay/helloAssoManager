from django.apps import AppConfig


class HelloassoimporterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'helloAssoImporter'

    def ready(self):
        from common.api.helloAssoApi import init_hello_asso_api
        try:
            init_hello_asso_api()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"HelloAsso API non initialisée : {e}")
