from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from academic.views import (
    CustomTokenObtainPairView,
    redirect_to_home,
    index_view,
    login_view,
    registro_view,
    carro_view,
    matriculas_view
)

# =====================================================================
# CONFIGURACIÓN DE SWAGGER / OPENAPI (Criterio 5 y Pauta de Cotejo)
# Debe responder operativamente en /api/docs/
# =====================================================================
schema_view = get_schema_view(
    openapi.Info(
        title="Plataforma de Reservas de Cursos y Bootcamps (EdTech) API",
        default_version="v1",
        description=(
            "API REST para la gestión de matrículas, áreas de conocimiento, "
            "cursos con inventario atómico de cupos, carro persistente y autenticación JWT con roles RBAC."
        ),
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="cesar.aedo@edtech.cl"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Panel de administración Django
    path('admin/', admin.site.urls),

    # =====================================================================
    # VISTAS DIRECTAS DE PLANTILLAS HTML
    # =====================================================================
    path('', index_view, name='index'),
    path('login/', login_view, name='login'),
    path('registro/', registro_view, name='registro'),
    path('carro/', carro_view, name='carro'),
    path('mis-matriculas/', matriculas_view, name='mis-matriculas'),

    # =====================================================================
    # AUTENTICACIÓN JWT (ACCESS Y REFRESH CON CLAIMS DE ROL)
    # =====================================================================
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # =====================================================================
    # DOCUMENTACIÓN SWAGGER / OPENAPI (/api/docs/)
    # =====================================================================
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-docs'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc-docs'),
    path('api/swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),

    # Rutas y ViewSets de la aplicación académica
    path('', include('academic.urls')),

    # =====================================================================
    # RUTA RE_PATH COMODÍN (REQUERIMIENTO OBLIGATORIO)
    # Redirige cualquier URL desconocida a la portada evitando 404 de Django
    # =====================================================================
    re_path(r'^.*$', redirect_to_home, name='redirect_to_home'),
]

# Manejador global de error 404
handler404 = 'academic.views.redirect_to_home'
