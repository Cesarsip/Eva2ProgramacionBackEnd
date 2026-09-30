import uuid
from decimal import Decimal
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    Usuario,
    Area,
    Curso,
    CarroMatricula,
    ItemCarroMatricula,
    Matricula,
    DetalleMatricula
)
from .serializers import (
    CustomTokenObtainPairSerializer,
    UsuarioSerializer,
    AreaSerializer,
    CursoSerializer,
    CarroMatriculaSerializer,
    ItemCarroMatriculaSerializer,
    AgregarItemCarroSerializer,
    MatriculaSerializer,
    CambiarEstadoMatriculaSerializer
)
from .filters import CursoFilter, AreaFilter, MatriculaFilter
from .permissions import IsEstudiante, IsCoordinador, IsCoordinadorOrReadOnly

# =====================================================================
# BLOQUE 1: VISTAS DE AUTENTICACIÓN JWT PERSONALIZADA
# =====================================================================
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Endpoint POST /api/token/
    Emite tokens JWT de acceso y refresco con claims de rol inyectados.
    """
    serializer_class = CustomTokenObtainPairSerializer


# =====================================================================
# BLOQUE 2: VISTAS DEL CATÁLOGO Y OFERTA ACADÉMICA (PÚBLICO Y COORDINADOR)
# Cumple la Matriz de Permisos:
# - PÚBLICO: GET /api/cursos/, GET /api/areas/
# - COORDINADOR: POST/PUT/DELETE /api/cursos/, POST/PUT/DELETE /api/areas/
# =====================================================================
class AreaViewSet(viewsets.ModelViewSet):
    """
    Endpoint /api/areas/
    - GET: Acceso público a la lista de áreas de conocimiento.
    - POST, PUT, PATCH, DELETE: Restringido exclusivamente al Coordinador.
    """
    queryset = Area.objects.all().order_by('nombre')
    serializer_class = AreaSerializer
    permission_classes = [IsCoordinadorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AreaFilter


class CursoViewSet(viewsets.ModelViewSet):
    """
    Endpoint /api/cursos/
    - GET: Acceso público para consultar el catálogo de cursos y bootcamps disponibles.
    - POST, PUT, PATCH, DELETE: Restringido exclusivamente a Coordinadores Académicos.
    - Filtros con django-filter: ?area=1, ?precio_max=50000, ?con_cupo=true, ?titulo=python
    """
    queryset = Curso.objects.select_related('area').all().order_by('fecha_inicio', 'id')
    serializer_class = CursoSerializer
    permission_classes = [IsCoordinadorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CursoFilter


# =====================================================================
# BLOQUE 3: CARRO DE MATRÍCULA PERSISTENTE (ESTUDIANTE)
# Cumple Especificación C: Relación 1 a 1 en BD y persistencia post-logout
# Endpoints: GET /api/carro-matricula/, POST /api/carro-matricula/, DELETE /api/carro-matricula/
# =====================================================================
class CarroMatriculaAPIView(APIView):
    """
    Endpoint /api/carro-matricula/
    Acceso exclusivo para rol ESTUDIANTE autenticado mediante token JWT Bearer.
    
    - GET: Consulta el carro activo y todos sus cursos agregados.
    - POST: Agrega un curso al carro, validando que no se duplique en el mismo carro.
    - DELETE: Vacía el carro de compras o elimina un curso específico si se pasa ?curso_id=X o ?item_id=X.
    
    Los ítems quedan persistidos en PostgreSQL vinculados al ID del usuario,
    por lo que no se pierden al hacer logout ni al cambiar de navegador.
    """
    permission_classes = [permissions.IsAuthenticated, IsEstudiante]

    def get_carro(self, user):
        carro, _ = CarroMatricula.objects.get_or_create(usuario=user)
        return carro

    def get(self, request):
        carro = self.get_carro(request.user)
        serializer = CarroMatriculaSerializer(carro)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        carro = self.get_carro(request.user)
        curso_id = request.data.get('curso_id') or request.data.get('curso')

        if not curso_id:
            return Response(
                {"error": "Debe proporcionar el 'curso_id' a agregar."},
                status=status.HTTP_400_BAD_REQUEST
            )

        curso = get_object_or_404(Curso, id=curso_id, activo=True)

        # Validación estricta: No permitir duplicar el mismo curso en el mismo carro activo
        if ItemCarroMatricula.objects.filter(carro=carro, curso=curso).exists():
            return Response(
                {"error": f"El curso '{curso.titulo}' ya se encuentra en su carro de matrícula activo."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # NOTA: Los cupos NO se descuentan al agregar al carro; se validan al PAGAR (checkout)
        item = ItemCarroMatricula.objects.create(carro=carro, curso=curso)
        serializer = ItemCarroMatriculaSerializer(item)
        return Response({
            "mensaje": f"Curso '{curso.titulo}' agregado exitosamente al carro de matrícula.",
            "item": serializer.data,
            "total_items": carro.items.count(),
            "total_carro": str(carro.total)
        }, status=status.HTTP_201_CREATED)

    def delete(self, request):
        carro = self.get_carro(request.user)
        item_id = request.query_params.get('item_id') or request.data.get('item_id')
        curso_id = request.query_params.get('curso_id') or request.data.get('curso_id')

        if item_id:
            item = get_object_or_404(ItemCarroMatricula, id=item_id, carro=carro)
            titulo = item.curso.titulo
            item.delete()
            return Response({"mensaje": f"Curso '{titulo}' eliminado del carro."}, status=status.HTTP_200_OK)

        if curso_id:
            item = get_object_or_404(ItemCarroMatricula, curso_id=curso_id, carro=carro)
            titulo = item.curso.titulo
            item.delete()
            return Response({"mensaje": f"Curso '{titulo}' eliminado del carro."}, status=status.HTTP_200_OK)

        # Si no se especifica item_id ni curso_id, vacía completamente el carro
        carro.items.all().delete()
        return Response({"mensaje": "Carro de matrícula vaciado correctamente."}, status=status.HTTP_200_OK)


# =====================================================================
# BLOQUE 4: CHECKOUT TRANSACCIONAL Y DESCUENTO ATÓMICO DE CUPOS
# Endpoint: POST /api/matriculas/confirmar/ (ESTUDIANTE)
# Cumple Especificación D: Validación de cupos, orden histórica y emisión UUID
# =====================================================================
class ConfirmarMatriculaAPIView(APIView):
    """
    Endpoint POST /api/matriculas/confirmar/
    Ejecuta el proceso atómico de Checkout:
    1. Verifica que el carro contenga ítems.
    2. Bloquea las filas de los cursos en la base de datos con select_for_update() para evitar race conditions.
    3. Valida que cada curso disponga de al menos 1 cupo libre (cupos_disponibles >= 1).
    4. Si hay cupos insuficientes, aborta la transacción y retorna HTTP 400.
    5. Si todos tienen cupo:
       - Descuenta atómicamente 1 cupo por cada curso del catálogo.
       - Genera el registro histórico de la Matrícula en estado PAGADO con código UUID.
       - Emite las inscripciones oficiales (DetalleMatricula) con tickets UUID únicos.
       - Vacía el carro persistente del estudiante.
    """
    permission_classes = [permissions.IsAuthenticated, IsEstudiante]

    def post(self, request):
        carro, _ = CarroMatricula.objects.get_or_create(usuario=request.user)

        with transaction.atomic():
            items = list(carro.items.select_related('curso').all())

            if not items:
                return Response(
                    {"error": "El carro de matrícula está vacío. Agregue cursos antes de confirmar la compra."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Bloqueo select_for_update() para garantizar concurrencia segura
            curso_ids = [item.curso.id for item in items]
            cursos_bloqueados = {
                c.id: c for c in Curso.objects.select_for_update().filter(id__in=curso_ids)
            }

            # Validación de disponibilidad de cupos
            cursos_sin_cupo = []
            for item in items:
                curso = cursos_bloqueados.get(item.curso.id)
                if not curso or curso.cupos_disponibles < 1:
                    cursos_sin_cupo.append(item.curso.titulo)

            if cursos_sin_cupo:
                return Response({
                    "error": "No es posible procesar la matrícula debido a falta de cupos disponibles.",
                    "cursos_agotados": cursos_sin_cupo
                }, status=status.HTTP_400_BAD_REQUEST)

            # Descuento atómico de inventario/cupos en el momento exacto del pago
            total_orden = Decimal('0.00')
            for item in items:
                curso = cursos_bloqueados[item.curso.id]
                curso.cupos_disponibles -= 1
                curso.save(update_fields=['cupos_disponibles'])
                total_orden += curso.costo_matricula

            # Generación de la Matrícula en estado PAGADO con UUID de transacción
            matricula = Matricula.objects.create(
                estudiante=request.user,
                total=total_orden,
                estado=Matricula.EstadoMatriculaChoices.PAGADO
            )

            # Emisión de inscripciones y tickets únicos con UUID
            detalles = [
                DetalleMatricula(
                    matricula=matricula,
                    curso=cursos_bloqueados[item.curso.id],
                    precio_unitario=cursos_bloqueados[item.curso.id].costo_matricula,
                    codigo_ticket=uuid.uuid4()
                )
                for item in items
            ]
            DetalleMatricula.objects.bulk_create(detalles)

            # Vaciado del carro persistente
            carro.items.all().delete()

        serializer = MatriculaSerializer(matricula)
        return Response({
            "mensaje": "¡Matrícula confirmada exitosamente! El pago ha sido procesado y los cupos han sido reservados.",
            "matricula": serializer.data
        }, status=status.HTTP_201_CREATED)


# =====================================================================
# BLOQUE 5: HISTORIAL DE MATRÍCULAS (ESTUDIANTE)
# Endpoint: GET /api/mis-matriculas/
# =====================================================================
class MisMatriculasAPIView(APIView):
    """
    Endpoint GET /api/mis-matriculas/
    Permite al estudiante autenticado consultar el historial de sus matrículas
    realizadas, tickets únicos emitidos y el estado de sus inscripciones.
    """
    permission_classes = [permissions.IsAuthenticated, IsEstudiante]

    def get(self, request):
        matriculas = Matricula.objects.filter(
            estudiante=request.user
        ).prefetch_related('detalles__curso__area').order_by('-fecha_creacion')
        serializer = MatriculaSerializer(matriculas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# =====================================================================
# BLOQUE 6: GESTIÓN DE MATRÍCULAS Y CAMBIO DE ESTADOS (COORDINADOR)
# Endpoints: GET /api/matriculas/, PATCH /api/matriculas/{id}/estado/
# Cumple Requerimiento: Si la orden se CANCELA, el cupo se repone automáticamente.
# =====================================================================
class MatriculaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint /api/matriculas/
    Acceso exclusivo para Coordinadores Académicos para supervisar todas
    las transacciones realizadas en la institución y aplicar filtros avanzados.
    """
    queryset = Matricula.objects.select_related('estudiante').prefetch_related('detalles__curso').all().order_by('-fecha_creacion')
    serializer_class = MatriculaSerializer
    permission_classes = [permissions.IsAuthenticated, IsCoordinador]
    filter_backends = [DjangoFilterBackend]
    filterset_class = MatriculaFilter


class CambiarEstadoMatriculaAPIView(APIView):
    """
    Endpoint PATCH /api/matriculas/{id}/estado/
    Exclusivo para Coordinador Académico.
    Permite transicionar el estado de la matrícula (PENDIENTE, PAGADO, COMPLETADO, CANCELADO).
    
    LÓGICA CRÍTICA DE STOCK:
    Si la orden se actualiza a CANCELADO y su estado previo era PAGADO o COMPLETADO,
    el sistema repone automáticamente los cupos descontados de vuelta al catálogo
    mediante un bloque transaccional atómico seguro.
    """
    permission_classes = [permissions.IsAuthenticated, IsCoordinador]

    def patch(self, request, pk):
        matricula = get_object_or_404(Matricula, id=pk)
        serializer = CambiarEstadoMatriculaSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        nuevo_estado = serializer.validated_data['estado']
        estado_anterior = matricula.estado

        if nuevo_estado == estado_anterior:
            return Response({"mensaje": f"La matrícula ya se encuentra en estado {nuevo_estado}."}, status=status.HTTP_200_OK)

        with transaction.atomic():
            matricula_bloqueada = Matricula.objects.select_for_update().get(id=pk)

            # Reposición de stock/cupos si se cancela una matrícula previamente pagada
            if nuevo_estado == Matricula.EstadoMatriculaChoices.CANCELADO and estado_anterior in [
                Matricula.EstadoMatriculaChoices.PAGADO,
                Matricula.EstadoMatriculaChoices.COMPLETADO
            ]:
                for detalle in matricula_bloqueada.detalles.select_related('curso').all():
                    curso = Curso.objects.select_for_update().get(id=detalle.curso_id)
                    curso.cupos_disponibles = min(curso.cupos_totales, curso.cupos_disponibles + 1)
                    curso.save(update_fields=['cupos_disponibles'])

            matricula_bloqueada.estado = nuevo_estado
            matricula_bloqueada.save(update_fields=['estado', 'fecha_actualizacion'])

        return Response({
            "mensaje": f"Estado de la matrícula {matricula.codigo_transaccion} actualizado a {nuevo_estado}.",
            "estado_anterior": estado_anterior,
            "nuevo_estado": nuevo_estado,
            "cupos_repuestos": (nuevo_estado == Matricula.EstadoMatriculaChoices.CANCELADO)
        }, status=status.HTTP_200_OK)


# =====================================================================
# BLOQUE 7: REGISTRO DE USUARIOS CON ASIGNACIÓN DE ROL
# Endpoint: POST /api/registro/
# =====================================================================
class RegistroAPIView(APIView):
    """
    Endpoint público POST /api/registro/
    Permite el registro de nuevos usuarios en la plataforma, asignando su rol
    (Estudiante o Coordinador Académico), encriptando la contraseña y
    emitiendo automáticamente tokens JWT con los claims correspondientes.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UsuarioSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Emisión inmediata de tokens JWT para inicio de sesión directo
            refresh = CustomTokenObtainPairSerializer.get_token(user)

            return Response({
                "mensaje": f"Usuario '{user.username}' registrado exitosamente con rol {user.get_rol_display()}.",
                "usuario": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "nombre_completo": f"{user.first_name} {user.last_name}".strip() or user.username,
                    "rol": user.rol,
                    "telefono": user.telefono,
                },
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================================================
# BLOQUE 8: VISTAS HTML WEB (INTERFAZ DE USUARIO + FOOTER DEL ALUMNO)
# Cumple Especificación: Funcionalidad completa sin exponer pantallas crudas de Django.
# Redirección de cualquier ruta inválida al inicio mediante redirect_to_home.
# =====================================================================
def index_view(request):
    """
    Vista principal de la Plataforma EdTech (Catálogo interactivo con filtros).
    Renderiza la portada profesional con la oferta académica, filtros y panel superior.
    """
    return render(request, 'academic/index.html')


def cursos_view(request):
    """Vista de Catálogo de Cursos y Bootcamps."""
    return render(request, 'academic/index.html')


def carro_view(request):
    """Vista del Carro de Matrícula Persistente."""
    return render(request, 'academic/carro.html')


def matriculas_view(request):
    """Vista de Historial de Matrículas e Inscripciones Oficiales."""
    return render(request, 'academic/matriculas.html')


def login_view(request):
    """Vista del Formulario de Inicio de Sesión JWT estilo profesional."""
    return render(request, 'academic/login.html')


def registro_view(request):
    """Vista del Formulario de Registro con Roles estilo profesional."""
    return render(request, 'academic/registro.html')


def redirect_to_home(request, path=''):
    """
    Manejador Fallback / Comodín:
    Redirige cualquier ruta no contemplada directamente a la portada ('/'),
    evitando pantallas 404 por defecto de Django según lo requerido por el usuario.
    """
    return redirect('index')


fallback_view = redirect_to_home
custom_404_view = redirect_to_home
