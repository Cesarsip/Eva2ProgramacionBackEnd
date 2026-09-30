from django.apps import AppConfig  # Importa la configuración base de aplicaciones Django; sin ella no se define AcademicConfig.


class AcademicConfig(AppConfig):
    name = 'academic'  # Indica el paquete de la aplicación; al quitarlo Django no sabría qué aplicación registrar.
