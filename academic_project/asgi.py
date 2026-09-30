"""
ASGI config for academic_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

# Expone la aplicación ASGI que servidores asíncronos usan para atender
# solicitudes; quitar esta configuración impediría desplegar el proyecto por ASGI.
import os

from django.core.asgi import get_asgi_application

# Indica dónde cargar la configuración del proyecto; sin ello Django no podría
# resolver aplicaciones, middleware ni demás ajustes al inicializarse.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_project.settings')

# Objeto de entrada reconocido por servidores ASGI; sin él no tendrían callable
# de aplicación que ejecutar.
application = get_asgi_application()
