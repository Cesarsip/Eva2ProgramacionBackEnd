# =====================================================================
# ENRUTAMIENTO PRINCIPAL DEL PROYECTO (ACADEMIC_PROJECT / URLS.PY)
# Cumple Requerimiento 4: Sin interfaz de administración ('admin/'),
# rutas para cada plantilla web, endpoints DRF y redirección catch-all.
# Si se quita este módulo o sus rutas, Django deja de resolver esas páginas,
# documentación y servicios; el fallback también dejaría de redirigir URLs desconocidas.
# =====================================================================

from django.urls import path, include, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from academic.views import (
    CustomTokenObtainPairView,
    DocumentedTokenRefreshView,
    redirect_to_home,
    index_view,
    login_view,
    registro_view,
    carro_view,
    matriculas_view,
    dashboard_coordinador_view,
    areas_view,
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
    path('gestion/', dashboard_coordinador_view, name='dashboard-coordinador'),
    path('gestion/areas/', areas_view, name='gestion-areas'),

    # -----------------------------------------------------------------
    # AUTENTICACIÓN JWT (ACCESS Y REFRESH CON CLAIMS DE ROL)
    # -----------------------------------------------------------------
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', DocumentedTokenRefreshView.as_view(), name='token_refresh'),

    # -----------------------------------------------------------------
    # DOCUMENTACIÓN AGRUPADA SWAGGER / OPENAPI (/api/docs/)
    # -----------------------------------------------------------------
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-docs'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc-docs'),
    path('api/swagger.json', SpectacularAPIView.as_view(), name='schema-json'),

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
