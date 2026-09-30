"""
WSGI config for academic_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

# Expone la aplicación WSGI que servidores tradicionales usan para atender
# solicitudes; quitar esta configuración impediría desplegar el proyecto por WSGI.
import os

from django.core.wsgi import get_wsgi_application

# Selecciona los ajustes del proyecto al iniciar el servidor; sin esta variable
# Django no podría conocer su configuración.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_project.settings')

# Callable de entrada esperado por servidores WSGI; sin él no habría aplicación
# que el servidor pudiera invocar.
application = get_wsgi_application()
