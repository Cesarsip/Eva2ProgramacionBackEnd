#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
# Este punto de entrada prepara el entorno y delega los comandos a Django;
# sin él no se podrían ejecutar tareas como runserver, migrate ni las pruebas.
import os
import sys


def main():
    """Run administrative tasks."""
    # Selecciona la configuración del proyecto; al quitarlo Django no sabría
    # qué aplicaciones, base de datos ni rutas debe cargar.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Explica el fallo de instalación con un mensaje accionable para quien
        # ejecuta el proyecto; sin esta traducción solo aparecería el error crudo.
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


# Permite importar este archivo sin lanzar un comando; al quitar la condición,
# cualquier importación accidental ejecutaría la CLI y sus efectos secundarios.
if __name__ == '__main__':
    main()
