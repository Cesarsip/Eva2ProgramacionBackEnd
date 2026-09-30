from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# =====================================================================
# ENRUTADOR DRF PARA VIEWSETS (CATÁLOGO, ÁREAS Y MATRÍCULAS)
# =====================================================================
router = DefaultRouter()
router.register(r'areas', views.AreaViewSet, basename='area')
router.register(r'cursos', views.CursoViewSet, basename='curso')
router.register(r'matriculas', views.MatriculaViewSet, basename='matricula')

urlpatterns = [
    # =====================================================================
    # VISTAS DE INTERFAZ WEB HTML (PÁGINAS FRONTEND CON FOOTER Y JAVASCRIPT)
    # =====================================================================
    path('', views.index_view, name='index'),
    path('catalogo/', views.cursos_view, name='catalogo_web'),
    path('cursos/', views.cursos_view, name='cursos_web'),
    path('login/', views.login_view, name='login_web'),
    path('registro/', views.registro_view, name='registro_web'),
    path('carro/', views.carro_view, name='carro_web'),
    path('mis-matriculas/', views.matriculas_view, name='matriculas_web'),

    # =====================================================================
    # ENDPOINTS API REST (MATRIZ DE ROLES Y PERMISOS)
    # =====================================================================
    # Registro de usuarios con selección de rol (Estudiante / Coordinador)
    path('api/registro/', views.RegistroAPIView.as_view(), name='api-registro'),

    # 1. Carro de Matrícula Persistente (Estudiante): GET/POST/DELETE
    path('api/carro-matricula/', views.CarroMatriculaAPIView.as_view(), name='api-carro-matricula'),

    # 2. Confirmación / Checkout de Matrícula (Estudiante): POST
    path('api/matriculas/confirmar/', views.ConfirmarMatriculaAPIView.as_view(), name='api-matriculas-confirmar'),

    # 3. Historial de Matrículas del Estudiante: GET
    path('api/mis-matriculas/', views.MisMatriculasAPIView.as_view(), name='api-mis-matriculas'),

    # 4. Modificación de Estado de Matrícula (Coordinador): PATCH
    path('api/matriculas/<int:pk>/estado/', views.CambiarEstadoMatriculaAPIView.as_view(), name='api-matricula-cambiar-estado'),

    # 5. Catálogo, Áreas y ViewSets de la API:
    #    - Público: GET /api/cursos/, GET /api/areas/
    #    - Coordinador: POST/PUT/DELETE /api/cursos/, POST/PUT/DELETE /api/areas/, GET /api/matriculas/
    path('api/', include(router.urls)),
]
