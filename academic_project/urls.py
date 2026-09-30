# =====================================================================
# ENRUTAMIENTO PRINCIPAL DEL PROYECTO (ACADEMIC_PROJECT / URLS.PY)
# Cumple Requerimiento 4: Sin interfaz de administración ('admin/'),
# rutas para cada plantilla web, endpoints DRF y redirección catch-all.
# Si se quita este módulo o sus rutas, Django deja de resolver esas páginas,
# documentación y servicios; el fallback también dejaría de redirigir URLs desconocidas.
# =====================================================================

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
# BLOQUE 1: ESQUEMA OPENAPI Y DOCUMENTACIÓN SWAGGER EN /API/DOCS/
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

# =====================================================================
# BLOQUE 2: RUTAS WEB Y ENDPOINTS DE LA API (SIN INTERFAZ ADMIN)
# NOTA: Se excluye intencionalmente 'admin/' para cumplir la directriz de evaluación.
# =====================================================================
urlpatterns = [
    # -----------------------------------------------------------------
    # VISTAS DIRECTAS DE PLANTILLAS HTML
    # -----------------------------------------------------------------
    path('', index_view, name='index'),
    path('login/', login_view, name='login'),
    path('registro/', registro_view, name='registro'),
    path('carro/', carro_view, name='carro'),
    path('mis-matriculas/', matriculas_view, name='mis-matriculas'),

    # -----------------------------------------------------------------
    # AUTENTICACIÓN JWT (ACCESS Y REFRESH CON CLAIMS DE ROL)
    # -----------------------------------------------------------------
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # -----------------------------------------------------------------
    # DOCUMENTACIÓN INTERACTIVA SWAGGER / OPENAPI (/api/docs/)
    # -----------------------------------------------------------------
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-docs'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc-docs'),
    path('api/swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),

    # -----------------------------------------------------------------
    # ENDPOINTS REST API DE LA APLICACIÓN ACADÉMICA (VIEWSETS Y APIS)
    # -----------------------------------------------------------------
    path('', include('academic.urls')),

    # -----------------------------------------------------------------
    # REDIRECCIÓN CATCH-ALL RE_PATH (REQUERIMIENTO OBLIGATORIO)
    # Captura /admin, /admin/ o cualquier ruta no definida y redirige
    # automáticamente a la portada principal sin mostrar pantallas 404.
    # -----------------------------------------------------------------
    re_path(r'^.*$', redirect_to_home, name='redirect_to_home'),
]

# Conserva la redirección también ante errores 404 procesados por Django; sin
# este manejador las solicitudes 404 ya no usarían esa respuesta personalizada.
handler404 = 'academic.views.redirect_to_home'
