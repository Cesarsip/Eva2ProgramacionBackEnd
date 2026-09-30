# UUID identifica transacciones y tickets; Decimal calcula importes sin redondeo binario.
import uuid
from decimal import Decimal
# Proporciona bloques atómicos y bloqueos de filas para operaciones de matrícula.
from django.db import transaction
# Renderiza las páginas HTML, redirige el fallback y resuelve objetos o responde 404.
from django.shortcuts import render, redirect, get_object_or_404
# Habilita los filtros declarados en los viewsets del catálogo y de matrículas.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
# Aporta permisos, códigos HTTP y viewsets REST genéricos.
from rest_framework import permissions, status, viewsets
# Construye las respuestas HTTP de la API a partir de datos o errores.
from rest_framework.response import Response
# Base para endpoints REST definidos explícitamente mediante métodos HTTP.
from rest_framework.views import APIView
# Vista JWT que emite el par de tokens usando el serializador personalizado.
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)

# Modelos consultados y persistidos por las vistas; sin ellos no habría acceso al dominio académico.
from .models import (
    Usuario,
    Area,
    Curso,
    CarroMatricula,
    ItemCarroMatricula,
    Matricula,
    DetalleMatricula
)
# Serializadores de entrada/salida y validación; quitarlos impediría validar o representar esos recursos.
from .serializers import (
    CustomTokenObtainPairSerializer,
    UsuarioSerializer,
    AreaSerializer,
    CursoSerializer,
    CarroMatriculaSerializer,
    ItemCarroMatriculaSerializer,
    AgregarItemCarroSerializer,
    MatriculaSerializer,
    CambiarEstadoMatriculaSerializer,
    ConfirmarMatriculaResponseSerializer,
)
# Filtros de parámetros para áreas, cursos y matrículas; sin ellos no se aplicarían sus búsquedas.
from .filters import CursoFilter, AreaFilter, MatriculaFilter
# Permisos por rol: restringen el catálogo de escritura y las operaciones de estudiante/coordinador.
from .permissions import IsEstudiante, IsCoordinador, IsCoordinadorOrReadOnly

# =====================================================================
# BLOQUE 1: VISTAS DE AUTENTICACIÓN JWT PERSONALIZADA
# =====================================================================
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Endpoint POST /api/token/
    Emite tokens JWT de acceso y refresco con claims de rol inyectados.
    """
    # Usa el serializador que incorpora los claims personalizados de rol al par de tokens.
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        tags=['Autenticación'],
        summary='Iniciar sesión',
        description='Valida usuario y contraseña y devuelve access/refresh junto con el perfil y rol.',
        request=OpenApiTypes.OBJECT,
        examples=[
            OpenApiExample(
                'Credenciales de acceso',
                value={'username': 'estudiante', 'password': 'contraseña-segura'},
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(description='Credenciales válidas; devuelve tokens y perfil del usuario.'),
            401: OpenApiResponse(description='Usuario o contraseña incorrectos.'),
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DocumentedTokenRefreshView(TokenRefreshView):
    """Expone la renovación JWT con documentación de operación y contrato de entrada."""

    @extend_schema(
        tags=['Autenticación'],
        summary='Renovar access token',
        description='Público con refresh válido: emite un nuevo access token sin volver a enviar credenciales.',
        request=OpenApiTypes.OBJECT,
        examples=[OpenApiExample('Token de renovación', value={'refresh': '<refresh-token>'}, request_only=True)],
        responses={200: OpenApiResponse(description='Access token renovado.'),
                   401: OpenApiResponse(description='Refresh inválido, vencido o no aceptado.')},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


# =====================================================================
# BLOQUE 2: VISTAS DEL CATÁLOGO Y OFERTA ACADÉMICA (PÚBLICO Y COORDINADOR)
# Cumple la Matriz de Permisos:
# - PÚBLICO: GET /api/cursos/, GET /api/areas/
# - COORDINADOR: POST/PUT/DELETE /api/cursos/, POST/PUT/DELETE /api/areas/
# =====================================================================
@extend_schema_view(
    list=extend_schema(
        tags=['Áreas'], summary='Listar áreas',
        description='Público: lista áreas activas; coordinación autenticada también puede consultar áreas desactivadas.',
        parameters=[OpenApiParameter('nombre', OpenApiTypes.STR, description='Búsqueda parcial por nombre.'),
                    OpenApiParameter('activo', OpenApiTypes.BOOL, description='Filtra por estado activo.')],
        auth=[],
        responses={200: AreaSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=['Áreas'], summary='Ver área', description='Público: obtiene el detalle de un área activa.',
        auth=[], responses={200: AreaSerializer, 404: OpenApiResponse(description='El área no existe o está inactiva.')},
    ),
    create=extend_schema(
        tags=['Áreas'], summary='Crear área', description='Coordinador: crea un área de conocimiento.',
        examples=[OpenApiExample('Área nueva', value={'nombre': 'Ciberseguridad', 'descripcion': 'Seguridad digital',
                     'icono': 'bi-shield-lock', 'activo': True}, request_only=True)],
        responses={201: AreaSerializer, 400: OpenApiResponse(description='Datos de área no válidos.'),
                   403: OpenApiResponse(description='Solo coordinación puede crear áreas.')},
    ),
    update=extend_schema(
        tags=['Áreas'], summary='Reemplazar área', description='Coordinador: reemplaza los datos editables del área.',
        responses={200: AreaSerializer, 400: OpenApiResponse(description='Datos inválidos.'), 403: OpenApiResponse(description='Solo coordinación.'), 404: OpenApiResponse(description='Área inexistente.')},
    ),
    partial_update=extend_schema(
        tags=['Áreas'], summary='Editar área', description='Coordinador: actualiza parcialmente nombre, descripción o ícono.',
        responses={200: AreaSerializer, 400: OpenApiResponse(description='Datos inválidos.'), 403: OpenApiResponse(description='Solo coordinación.'), 404: OpenApiResponse(description='Área inexistente.')},
    ),
    destroy=extend_schema(
        tags=['Áreas'], summary='Desactivar área', description='Coordinador: realiza una baja lógica; conserva cursos e historial.',
        responses={204: OpenApiResponse(description='Área desactivada.'), 403: OpenApiResponse(description='Permiso de coordinación requerido.')},
    ),
)
class AreaViewSet(viewsets.ModelViewSet):
    """
    Endpoint /api/areas/
    - GET: Acceso público a la lista de áreas de conocimiento.
    - POST, PUT, PATCH, DELETE: Restringido exclusivamente al Coordinador.
    """
    # Expone áreas ordenadas; quitar el queryset impediría listar/recuperar y limitaría las escrituras del viewset.
    queryset = Area.objects.all().order_by('nombre')
    # Define el contrato JSON y la validación de campos del área.
    serializer_class = AreaSerializer
    # Deja GET público, pero exige coordinación para mutaciones.
    permission_classes = [IsCoordinadorOrReadOnly]
    # Activa el backend de filtros sobre el conjunto declarado.
    filter_backends = [DjangoFilterBackend]
    # Traduce parámetros compatibles al filtrado de áreas.
    filterset_class = AreaFilter

    def get_queryset(self):
        # Lectura pública solo expone áreas activas; coordinación puede administrar todo el catálogo.
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and (user.is_coordinador):
            return queryset
        return queryset.filter(activo=True)

    def destroy(self, request, *args, **kwargs):
        # Conserva las áreas y sus relaciones históricas, marcándolas como inactivas en vez de borrarlas.
        area = self.get_object()
        area.activo = False
        area.save(update_fields=['activo'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=['Áreas'], summary='Reactivar área', description='Coordinador: vuelve a publicar un área desactivada.',
        responses={200: AreaSerializer, 403: OpenApiResponse(description='Permiso de coordinación requerido.'),
                   404: OpenApiResponse(description='El área no existe.')},
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsCoordinador])
    def reactivar(self, request, pk=None):
        area = self.get_object()
        area.activo = True
        area.save(update_fields=['activo'])
        return Response(self.get_serializer(area).data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        tags=['Cursos'], summary='Listar cursos y aplicar filtros',
        description='Público: consulta cursos activos. Coordinación autenticada también puede ver los desactivados.',
        parameters=[
            OpenApiParameter('titulo', OpenApiTypes.STR, description='Búsqueda parcial por título.'),
            OpenApiParameter('area', OpenApiTypes.INT, description='ID del área.'),
            OpenApiParameter('area_nombre', OpenApiTypes.STR, description='Búsqueda parcial por nombre de área.'),
            OpenApiParameter('modalidad', OpenApiTypes.STR, description='BOOTCAMP, CURSO o TALLER.'),
            OpenApiParameter('precio_min', OpenApiTypes.NUMBER, description='Precio mínimo, inclusivo.'),
            OpenApiParameter('precio_max', OpenApiTypes.NUMBER, description='Precio máximo, inclusivo.'),
            OpenApiParameter('con_cupo', OpenApiTypes.BOOL, description='true devuelve solo cursos con cupos.'),
            OpenApiParameter('agotado', OpenApiTypes.BOOL, description='true devuelve solo cursos sin cupos disponibles.'),
        ],
        auth=[],
        responses={200: CursoSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=['Cursos'], summary='Ver curso', description='Público: consulta un curso publicado; coordinación también consulta desactivados.',
        auth=[], responses={200: CursoSerializer, 404: OpenApiResponse(description='Curso inexistente o no publicado.')},
    ),
    create=extend_schema(
        tags=['Cursos'], summary='Crear curso', description='Coordinador: publica un curso o bootcamp en una cohorte.',
        examples=[OpenApiExample('Curso nuevo', value={
            'titulo': 'Python para Backend', 'descripcion': 'API y persistencia con Python.',
            'area': 1, 'modalidad': 'CURSO', 'costo_matricula': '85000.00',
            'fecha_inicio': '2026-11-01', 'fecha_termino': '2026-12-01',
            'cupos_totales': 20, 'cupos_disponibles': 20, 'activo': True,
        }, request_only=True)],
        responses={201: CursoSerializer, 400: OpenApiResponse(description='Datos inválidos, fechas o cupos incoherentes.'),
                   403: OpenApiResponse(description='Solo coordinación puede crear cursos.')},
    ),
    update=extend_schema(
        tags=['Cursos'], summary='Reemplazar curso', description='Coordinador: reemplaza los datos editables del curso.',
        responses={200: CursoSerializer, 400: OpenApiResponse(description='Datos, fechas o cupos inválidos.'), 403: OpenApiResponse(description='Solo coordinación.'), 404: OpenApiResponse(description='Curso inexistente.')},
    ),
    partial_update=extend_schema(
        tags=['Cursos'], summary='Editar curso', description='Coordinador: actualiza parcialmente los datos de un curso.',
        responses={200: CursoSerializer, 400: OpenApiResponse(description='Datos, fechas o cupos inválidos.'), 403: OpenApiResponse(description='Solo coordinación.'), 404: OpenApiResponse(description='Curso inexistente.')},
    ),
    destroy=extend_schema(
        tags=['Cursos'], summary='Desactivar curso', description='Coordinador: realiza una baja lógica y conserva inscripciones históricas.',
        responses={204: OpenApiResponse(description='Curso desactivado.'), 403: OpenApiResponse(description='Permiso de coordinación requerido.')},
    ),
)
class CursoViewSet(viewsets.ModelViewSet):
    """
    Endpoint /api/cursos/
    - GET: Acceso público para consultar el catálogo de cursos y bootcamps disponibles.
    - POST, PUT, PATCH, DELETE: Restringido exclusivamente a Coordinadores Académicos.
    - Filtros con django-filter: ?area=1, ?precio_max=50000, ?con_cupo=true, ?titulo=python
    """
    # Ordena el catálogo y carga el área relacionada en la consulta para evitar consultas repetidas.
    queryset = Curso.objects.select_related('area').all().order_by('fecha_inicio', 'id')
    # Serializa cursos y valida los datos de creación/edición.
    serializer_class = CursoSerializer
    # Mantiene lectura abierta y reserva la edición del catálogo a coordinadores.
    permission_classes = [IsCoordinadorOrReadOnly]
    # Conecta el endpoint con el filtrado por query parameters.
    filter_backends = [DjangoFilterBackend]
    # Define los filtros admitidos para la oferta académica.
    filterset_class = CursoFilter

    def get_queryset(self):
        # La oferta pública solo incluye cursos activos; coordinación puede administrar los desactivados.
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.is_coordinador:
            return queryset
        return queryset.filter(activo=True, area__activo=True)

    def destroy(self, request, *args, **kwargs):
        # La baja lógica evita perder referencias y tickets de matrículas ya confirmadas.
        curso = self.get_object()
        curso.activo = False
        curso.save(update_fields=['activo'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=['Cursos'], summary='Reactivar curso', description='Coordinador: vuelve a publicar un curso activo en el catálogo.',
        responses={200: CursoSerializer, 400: OpenApiResponse(description='El área asociada debe estar activa.'),
                   403: OpenApiResponse(description='Permiso de coordinación requerido.'), 404: OpenApiResponse(description='El curso no existe.')},
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsCoordinador])
    def reactivar(self, request, pk=None):
        curso = self.get_object()
        if not curso.area.activo:
            return Response(
                {'error': 'No se puede reactivar el curso mientras su área esté desactivada.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        curso.activo = True
        curso.save(update_fields=['activo'])
        return Response(self.get_serializer(curso).data, status=status.HTTP_200_OK)


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
    # Exige sesión válida y rol estudiante para impedir acceso a carros ajenos.
    permission_classes = [permissions.IsAuthenticated, IsEstudiante]

    def get_carro(self, user):
        # Reutiliza el carro único del usuario o lo crea si aún no existe.
        carro, _ = CarroMatricula.objects.get_or_create(usuario=user)
        return carro

    @extend_schema(
        tags=['Carro de matrícula'], summary='Consultar mi carro',
        description='Estudiante autenticado: consulta el carro persistente y sus cursos.',
        responses={200: CarroMatriculaSerializer, 401: OpenApiResponse(description='Autenticación requerida.'),
                   403: OpenApiResponse(description='Solo estudiantes pueden consultar el carro.')},
    )
    def get(self, request):
        # Consulta el carro del estudiante; sin ello no habría datos de carro que devolver.
        carro = self.get_carro(request.user)
        # Representa los campos del carro; sin serializar, la respuesta no tendría el formato API.
        serializer = CarroMatriculaSerializer(carro)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=['Carro de matrícula'], summary='Agregar cursos al carro',
        description='Estudiante autenticado: agrega un curso o sincroniza una lista. Rechaza duplicados y matrículas activas existentes.',
        request=OpenApiTypes.OBJECT,
        examples=[
            OpenApiExample('Un curso', value={'curso_id': 3}, request_only=True),
            OpenApiExample('Sincronizar lista', value={'cursos_ids': [3, 4]}, request_only=True),
        ],
        responses={200: OpenApiResponse(description='Sincronización por lote completada.'),
                   201: OpenApiResponse(description='Curso agregado y representación del ítem devuelta.'),
                   400: OpenApiResponse(description='Curso inexistente/inactivo, duplicado o ya matriculado.'),
                   401: OpenApiResponse(description='Autenticación requerida.'), 403: OpenApiResponse(description='Solo estudiantes.')},
    )
    def post(self, request):
        # Todas las altas se vinculan al carro del solicitante, no a uno indicado por el cliente.
        carro = self.get_carro(request.user)
        # Acepta listas JSON y, más abajo, listas de formularios con la misma clave.
        cursos_ids = request.data.get('cursos_ids')
        # DRF puede exponer claves repetidas mediante getlist(); conservarlas permite sincronizar todos los cursos.
        if hasattr(request.data, 'getlist') and not isinstance(cursos_ids, list):
            lista = request.data.getlist('cursos_ids')
            if lista:
                cursos_ids = lista

        # Soporte para sincronización atómica por lotes (merge desde carro anónimo en localStorage)
        if cursos_ids and isinstance(cursos_ids, (list, tuple)):
            # Valida todo el lote antes de escribir para que un duplicado no deje una sincronización parcial.
            cursos_a_agregar = []
            ids_vistos = set()
            for curso_id_lote in cursos_ids:
                validacion = AgregarItemCarroSerializer(
                    data={'curso_id': curso_id_lote},
                    context={'request': request, 'carro': carro}
                )
                if not validacion.is_valid():
                    return Response(
                        {"error": str(validacion.errors.get('curso_id', ['Curso inválido.'])[0])},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                curso_validado = validacion.validated_data['curso_id']
                if curso_validado.id in ids_vistos:
                    return Response(
                        {"error": f"El curso '{curso_validado.titulo}' aparece más de una vez en la solicitud."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                ids_vistos.add(curso_validado.id)
                cursos_a_agregar.append(curso_validado)

            # Persiste el lote completo solo después de validar todas las entradas.
            with transaction.atomic():
                ItemCarroMatricula.objects.bulk_create([
                    ItemCarroMatricula(carro=carro, curso=curso)
                    for curso in cursos_a_agregar
                ])
            # Informa el resultado del lote y los totales actuales del carro.
            return Response({
                "mensaje": f"Sincronización completada. Se añadieron {len(cursos_a_agregar)} curso(s) al carro persistente.",
                "agregados": [curso.titulo for curso in cursos_a_agregar],
                "total_items": carro.items.count(),
                "total_carro": str(carro.total)
            }, status=status.HTTP_200_OK)

        # Mantiene compatibilidad con los dos nombres admitidos para un alta individual.
        curso_id = request.data.get('curso_id') or request.data.get('curso')

        # Rechaza solicitudes individuales sin identificador en vez de intentar una búsqueda ambigua.
        if not curso_id:
            return Response(
                {"error": "Debe proporcionar el 'curso_id' o 'cursos_ids' a agregar."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verifica curso activo, duplicidad en el carro y matrícula ya vigente antes de insertar.
        serializer = AgregarItemCarroSerializer(
            data={'curso_id': curso_id},
            context={'request': request, 'carro': carro}
        )
        if not serializer.is_valid():
            return Response(
                {"error": str(serializer.errors.get('curso_id', ['Curso inválido.'])[0])},
                status=status.HTTP_400_BAD_REQUEST
            )
        curso = serializer.validated_data['curso_id']

        # NOTA: Los cupos NO se descuentan al agregar al carro; se validan al PAGAR (checkout)
        # Persiste el ítem sin reservar cupo y devuelve el ítem serializado con el total actualizado.
        item = ItemCarroMatricula.objects.create(carro=carro, curso=curso)
        serializer = ItemCarroMatriculaSerializer(item)
        return Response({
            "mensaje": f"Curso '{curso.titulo}' agregado exitosamente al carro de matrícula.",
            "item": serializer.data,
            "total_items": carro.items.count(),
            "total_carro": str(carro.total)
        }, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=['Carro de matrícula'], summary='Eliminar cursos del carro',
        description='Estudiante autenticado: elimina un ítem con curso_id/item_id o vacía el carro completo.',
        parameters=[OpenApiParameter('curso_id', OpenApiTypes.INT, OpenApiParameter.QUERY, description='ID del curso que se elimina.'),
                    OpenApiParameter('item_id', OpenApiTypes.INT, OpenApiParameter.QUERY, description='ID del ítem que se elimina.')],
        responses={200: OpenApiResponse(description='Ítem eliminado o carro vaciado.'),
                   401: OpenApiResponse(description='Autenticación requerida.'), 403: OpenApiResponse(description='Solo estudiantes.')},
    )
    def delete(self, request):
        # El alcance se limita siempre al carro del usuario autenticado.
        carro = self.get_carro(request.user)
        # Acepta selectores tanto en query string como en el cuerpo de la solicitud.
        item_id = request.query_params.get('item_id') or request.data.get('item_id')
        curso_id = request.query_params.get('curso_id') or request.data.get('curso_id')

        if item_id:
            # El ID debe pertenecer al carro actual para impedir borrar ítems de otra persona.
            item = get_object_or_404(ItemCarroMatricula, id=item_id, carro=carro)
            titulo = item.curso.titulo
            item.delete()
            # Confirma al cliente la eliminación individual.
            return Response({"mensaje": f"Curso '{titulo}' eliminado del carro."}, status=status.HTTP_200_OK)

        if curso_id:
            # Alternativa de borrado por curso, también restringida al carro del solicitante.
            item = get_object_or_404(ItemCarroMatricula, curso_id=curso_id, carro=carro)
            titulo = item.curso.titulo
            item.delete()
            # Confirma la eliminación por curso sin modificar los demás ítems.
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
    # Solo estudiantes autenticados pueden confirmar sus propias compras.
    permission_classes = [permissions.IsAuthenticated, IsEstudiante]

    @extend_schema(
        tags=['Matrículas'],
        summary='Confirmar matrícula desde el carro',
        description=(
            'Estudiante autenticado: valida todos los cupos dentro de una transacción, '
            'crea una matrícula PAGADO con tickets UUID, descuenta los cupos y vacía el carro. '
            'El checkout simula el pago; no integra una pasarela bancaria.'
        ),
        request=None,
        responses={
            201: OpenApiResponse(response=ConfirmarMatriculaResponseSerializer, description='Matrícula creada con sus inscripciones oficiales.'),
            400: OpenApiResponse(description='Carro vacío, curso duplicado o sin cupos disponibles.'),
            401: OpenApiResponse(description='Autenticación requerida.'),
            403: OpenApiResponse(description='Solo estudiantes pueden confirmar matrículas.'),
        },
    )
    def post(self, request):
        # Obtiene o crea el carro persistente del alumno; al quitarlo no habría carro que procesar.
        carro, _ = CarroMatricula.objects.get_or_create(usuario=request.user)

        # Agrupa los cambios de stock, orden y detalles como una sola operación; al quitarlo podrían quedar escrituras parciales.
        with transaction.atomic():
            # Precarga los cursos del carro reduciendo consultas repetidas; al quitarlo se podrían hacer consultas por cada ítem.
            items = list(carro.items.select_related('curso').all())

            # Impide confirmar un carro vacío; al quitarlo se podrían crear órdenes sin cursos.
            if not items:
                return Response(
                    {"error": "El carro de matrícula está vacío. Agregue cursos antes de confirmar la compra."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Bloqueo select_for_update() para garantizar concurrencia segura
            # Reúne los identificadores de los cursos que se deben reservar; al quitarlo no se sabría qué filas bloquear.
            curso_ids = [item.curso.id for item in items]
            # Bloquea filas mientras dure la transacción; al quitar el bloqueo habría riesgo de vender el mismo último cupo dos veces.
            cursos_bloqueados = {
                c.id: c for c in Curso.objects.select_for_update().filter(id__in=curso_ids)
            }

            # Revalida matrículas vigentes dentro del bloqueo de cursos para impedir
            # compras repetidas, incluso si el curso llevaba tiempo en el carro.
            cursos_ya_matriculados = list(
                DetalleMatricula.objects.filter(
                    matricula__estudiante=request.user,
                    matricula__estado__in=[
                        Matricula.EstadoMatriculaChoices.PAGADO,
                        Matricula.EstadoMatriculaChoices.COMPLETADO
                    ],
                    curso_id__in=curso_ids
                ).values_list('curso__titulo', flat=True)
            )
            if cursos_ya_matriculados:
                return Response({
                    "error": "No se puede confirmar la matrícula porque ya tienes inscripciones activas en algunos cursos.",
                    "cursos_ya_matriculados": cursos_ya_matriculados
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validación de disponibilidad de cupos
            # Acumula los cursos faltantes para informar todos en una respuesta; al quitarlo se perdería la validación de inventario.
            cursos_sin_cupo = []
            # Comprueba cada ítem contra la copia bloqueada de su curso; al quitar el ciclo se podría continuar sin revisar algún curso.
            for item in items:
                # Obtiene el curso bloqueado asociado al ítem; al quitarlo no se consultaría su disponibilidad actual.
                curso = cursos_bloqueados.get(item.curso.id)
                # Marca como agotado un curso ausente o sin cupos; al quitar la condición se aceptarían matrículas inválidas.
                if not curso or curso.cupos_disponibles < 1:
                    # Guarda el título para explicarle al cliente qué curso agotó sus cupos; al quitarlo el mensaje perdería ese detalle.
                    cursos_sin_cupo.append(item.curso.titulo)

            # Aborta antes de escribir si uno o más cursos están agotados; al quitarlo el flujo intentaría reservarlos igualmente.
            if cursos_sin_cupo:
                return Response({
                    "error": "No es posible procesar la matrícula debido a falta de cupos disponibles.",
                    "cursos_agotados": cursos_sin_cupo
                }, status=status.HTTP_400_BAD_REQUEST)

            # Descuento atómico de inventario/cupos en el momento exacto del pago
            # Inicia el total como Decimal para mantener precisión monetaria; al quitarlo el total no tendría acumulador.
            total_orden = Decimal('0.00')
            # Recorre los cursos ya validados; al quitarlo no se descontarían los cupos ni se sumarían sus precios.
            for item in items:
                # Reutiliza la fila bloqueada; al quitarlo se perdería la referencia al curso validado.
                curso = cursos_bloqueados[item.curso.id]
                # Reserva un cupo para esta matrícula; al quitarlo el stock no reflejaría la inscripción.
                curso.cupos_disponibles -= 1
                # Persiste solo el campo de disponibilidad; al quitarlo el descuento quedaría solo en memoria.
                curso.save(update_fields=['cupos_disponibles'])
                # Añade el precio de este curso al total; al quitarlo la orden quedaría con monto incorrecto.
                total_orden += curso.costo_matricula

            # Generación de la Matrícula en estado PAGADO con UUID de transacción
            # Crea la cabecera histórica de la compra; al quitarlo no existiría la orden agrupadora de los detalles.
            matricula = Matricula.objects.create(
                # Asocia la orden al alumno autenticado; al quitarlo no se podría saber quién se matriculó.
                estudiante=request.user,
                # Guarda el precio total calculado; al quitarlo no habría monto histórico correcto.
                total=total_orden,
                # Marca el estado inicial del checkout; al quitarlo se usaría el estado predeterminado del modelo.
                estado=Matricula.EstadoMatriculaChoices.PAGADO
            )

            # Emisión de inscripciones y tickets únicos con UUID
            # Construye un detalle/ticket por curso; al quitarlo la matrícula no tendría inscripciones individuales.
            detalles = [
                DetalleMatricula(
                    # Relaciona el ticket con la orden recién creada; al quitarlo el detalle quedaría huérfano.
                    matricula=matricula,
                    # Asocia el curso comprado; al quitarlo no se sabría qué curso representa el ticket.
                    curso=cursos_bloqueados[item.curso.id],
                    # Congela el precio al momento de la compra; al quitarlo cambios futuros del precio afectarían la referencia histórica.
                    precio_unitario=cursos_bloqueados[item.curso.id].costo_matricula,
                    # Asigna explícitamente un UUID al ticket; al quitarlo el modelo generaría otro con su valor predeterminado.
                    codigo_ticket=uuid.uuid4()
                )
                # Produce exactamente un detalle para cada ítem del carro; al quitarlo no se generarían los tickets.
                for item in items
            ]
            # Inserta los detalles en lote para reducir consultas; al quitarlo no quedarían persistidos.
            DetalleMatricula.objects.bulk_create(detalles)

            # Vaciado del carro persistente
            # Elimina los ítems tras completar la orden; al quitarlo el alumno podría confirmar de nuevo los mismos cursos.
            carro.items.all().delete()

        # Serializa la orden ya guardada para responder en formato JSON; al quitarlo no se tendría representación API de la matrícula.
        serializer = MatriculaSerializer(matricula)
        # Devuelve confirmación y la orden creada; al quitarlo el cliente no recibiría resultado HTTP de la operación.
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
    # Evita que usuarios anónimos o de otro rol accedan a este historial personal.
    permission_classes = [permissions.IsAuthenticated, IsEstudiante]

    @extend_schema(
        tags=['Matrículas'], summary='Consultar mis matrículas',
        description='Estudiante autenticado: devuelve únicamente sus órdenes y tickets oficiales.',
        responses={200: MatriculaSerializer(many=True), 401: OpenApiResponse(description='Autenticación requerida.'),
                   403: OpenApiResponse(description='Solo estudiantes.')},
    )
    def get(self, request):
        # Filtra por propietario, precarga detalles/curso/área y presenta primero las matrículas recientes.
        matriculas = Matricula.objects.filter(
            estudiante=request.user
        ).prefetch_related('detalles__curso__area').order_by('-fecha_creacion')
        # Serializa la colección y responde con éxito incluso si no hay registros.
        serializer = MatriculaSerializer(matriculas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# =====================================================================
# BLOQUE 6: GESTIÓN DE MATRÍCULAS Y CAMBIO DE ESTADOS (COORDINADOR)
# Endpoints: GET /api/matriculas/, PATCH /api/matriculas/{id}/estado/
# Cumple Requerimiento: Si la orden se CANCELA, el cupo se repone automáticamente.
# =====================================================================
@extend_schema_view(
    list=extend_schema(
        tags=['Matrículas'], summary='Listar matrículas de la plataforma',
        description='Coordinador: lista órdenes de todos los estudiantes. Permite filtrar por estado, usuario y fechas.',
        parameters=[
            OpenApiParameter('estado', OpenApiTypes.STR, description='PENDIENTE, PAGADO, COMPLETADO o CANCELADO.'),
            OpenApiParameter('estudiante', OpenApiTypes.STR, description='Búsqueda parcial por username.'),
            OpenApiParameter('fecha_desde', OpenApiTypes.DATE, description='Fecha mínima de creación.'),
            OpenApiParameter('fecha_hasta', OpenApiTypes.DATE, description='Fecha máxima de creación.'),
        ],
        responses={200: MatriculaSerializer(many=True), 401: OpenApiResponse(description='Autenticación requerida.'),
                   403: OpenApiResponse(description='Solo coordinación.')},
    ),
    retrieve=extend_schema(
        tags=['Matrículas'], summary='Consultar matrícula',
        description='Coordinador: obtiene una orden y sus inscripciones oficiales/tickets.',
        responses={200: MatriculaSerializer, 401: OpenApiResponse(description='Autenticación requerida.'),
                   403: OpenApiResponse(description='Solo coordinación.'), 404: OpenApiResponse(description='Matrícula inexistente.')},
    ),
)
class MatriculaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint /api/matriculas/
    Acceso exclusivo para Coordinadores Académicos para supervisar todas
    las transacciones realizadas en la institución y aplicar filtros avanzados.
    """
    # Consulta global para supervisión; las relaciones se cargan de antemano y se ordenan por fecha.
    queryset = Matricula.objects.select_related('estudiante').prefetch_related('detalles__curso').all().order_by('-fecha_creacion')
    # Conserva el formato de matrícula en las respuestas de solo lectura.
    serializer_class = MatriculaSerializer
    # Exige autenticación y rol coordinador para consultar matrículas institucionales.
    permission_classes = [permissions.IsAuthenticated, IsCoordinador]
    # Habilita los filtros del listado de supervisión.
    filter_backends = [DjangoFilterBackend]
    # Define los criterios permitidos para filtrar matrículas.
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
    # Protege las transiciones de estado y el inventario frente a cambios no autorizados.
    permission_classes = [permissions.IsAuthenticated, IsCoordinador]

    @extend_schema(
        tags=['Matrículas'], summary='Cambiar estado de una matrícula',
        description=(
            'Coordinador: permite PENDIENTE, PAGADO, COMPLETADO o CANCELADO. '
            'Al activar una orden, valida y descuenta cupos; al cancelar una orden con cupos reservados, los repone '
            'dentro de una transacción atómica.'
        ),
        request=CambiarEstadoMatriculaSerializer,
        examples=[OpenApiExample('Actualizar estado', value={'estado': 'CANCELADO'}, request_only=True)],
        responses={200: OpenApiResponse(description='Estado actualizado y cupos ajustados cuando corresponde.'),
                   400: OpenApiResponse(description='Estado inválido, cupos insuficientes o matrícula incompatible.'),
                   401: OpenApiResponse(description='Autenticación requerida.'),
                   403: OpenApiResponse(description='Solo coordinación.'), 404: OpenApiResponse(description='Matrícula inexistente.')},
    )
    def patch(self, request, pk):
        # Devuelve HTTP 404 si la matrícula solicitada no existe.
        matricula = get_object_or_404(Matricula, id=pk)
        # Valida el estado entrante antes de modificar la matrícula.
        serializer = CambiarEstadoMatriculaSerializer(data=request.data)

        # Expone errores de validación y evita persistir estados no admitidos.
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Conserva los estados nuevo y anterior para decidir la reposición y formar la respuesta.
        nuevo_estado = serializer.validated_data['estado']
        # Agrupa escrituras y bloquea la fila durante la actualización para evitar cambios parciales.
        with transaction.atomic():
            # Vuelve a obtener y bloquear la fila para actualizar el estado de forma segura.
            matricula_bloqueada = Matricula.objects.select_for_update().get(id=pk)
            estado_anterior = matricula_bloqueada.estado

            # Evita escrituras innecesarias si la petición no cambia el estado.
            if nuevo_estado == estado_anterior:
                return Response({"mensaje": f"La matrícula ya se encuentra en estado {nuevo_estado}."}, status=status.HTTP_200_OK)

            estados_con_cupo_reservado = {
                Matricula.EstadoMatriculaChoices.PAGADO,
                Matricula.EstadoMatriculaChoices.COMPLETADO
            }
            detalles = list(
                matricula_bloqueada.detalles.order_by('curso_id', 'id')
            )
            curso_ids = sorted({detalle.curso_id for detalle in detalles})
            cursos_bloqueados = {
                curso.id: curso
                for curso in Curso.objects.select_for_update().filter(id__in=curso_ids).order_by('id')
            }

            # Al activar una boleta cancelada o pendiente se comprueba y descuenta stock otra vez.
            # Aplica a PAGADO y COMPLETADO porque ambos estados representan inscripciones vigentes.
            if nuevo_estado in estados_con_cupo_reservado and estado_anterior not in estados_con_cupo_reservado:
                # No permite reactivar esta boleta si el mismo estudiante ya tiene
                # otra matrícula vigente para cualquiera de estos cursos.
                cursos_con_otra_inscripcion = list(
                    DetalleMatricula.objects.filter(
                        matricula__estudiante=matricula_bloqueada.estudiante,
                        matricula__estado__in=estados_con_cupo_reservado,
                        curso_id__in=curso_ids
                    ).exclude(
                        matricula_id=matricula_bloqueada.id
                    ).values_list('curso__titulo', flat=True)
                )
                if cursos_con_otra_inscripcion:
                    return Response({
                        "error": "No se puede activar la boleta porque el estudiante ya tiene una inscripción vigente en algunos cursos.",
                        "cursos_ya_matriculados": cursos_con_otra_inscripcion
                    }, status=status.HTTP_400_BAD_REQUEST)

                cursos_sin_cupo = [
                    cursos_bloqueados[detalle.curso_id].titulo
                    for detalle in detalles
                    if cursos_bloqueados[detalle.curso_id].cupos_disponibles < 1
                ]
                if cursos_sin_cupo:
                    return Response({
                        "error": "No se puede activar la matrícula: no hay cupos disponibles para todos los cursos.",
                        "cursos_agotados": cursos_sin_cupo
                    }, status=status.HTTP_400_BAD_REQUEST)

                for detalle in detalles:
                    curso = cursos_bloqueados[detalle.curso_id]
                    curso.cupos_disponibles -= 1
                    curso.save(update_fields=['cupos_disponibles'])

            # Solo una boleta que tenía cupos reservados los devuelve al pasar a un estado no vigente.
            # Esto incluye CANCELADO y PENDIENTE, sin inflar el stock al cancelar una orden ya pendiente.
            elif estado_anterior in estados_con_cupo_reservado and nuevo_estado not in estados_con_cupo_reservado:
                for detalle in detalles:
                    curso = cursos_bloqueados[detalle.curso_id]
                    curso.cupos_disponibles = min(curso.cupos_totales, curso.cupos_disponibles + 1)
                    curso.save(update_fields=['cupos_disponibles'])

            # Persiste únicamente estado y marca temporal; al quitarlo el cambio no quedaría guardado.
            matricula_bloqueada.estado = nuevo_estado
            matricula_bloqueada.save(update_fields=['estado', 'fecha_actualizacion'])

        # Informa la transición y si se ejecutó la reposición indicada por el estado solicitado.
        return Response({
            "mensaje": f"Estado de la matrícula {matricula.codigo_transaccion} actualizado a {nuevo_estado}.",
            "estado_anterior": estado_anterior,
            "nuevo_estado": nuevo_estado,
            "cupos_repuestos": (
                estado_anterior in estados_con_cupo_reservado
                and nuevo_estado not in estados_con_cupo_reservado
            ),
            "cupos_reservados": (
                estado_anterior not in estados_con_cupo_reservado
                and nuevo_estado in estados_con_cupo_reservado
            )
        }, status=status.HTTP_200_OK)


# =====================================================================
# BLOQUE 7: REGISTRO DE USUARIOS CON ASIGNACIÓN DE ROL
# Endpoint: POST /api/registro/
# =====================================================================
class RegistroAPIView(APIView):
    """
    Endpoint público POST /api/registro/
    Permite el registro de nuevos usuarios con rol ESTUDIANTE.
    El rol se fuerza a 'ESTUDIANTE' en el servidor independientemente
    de lo que el cliente envíe, previniendo escalada de privilegios.
    Los Coordinadores son creados exclusivamente por consola/backend.
    Emite tokens JWT con claims de rol para inicio de sesión inmediato.
    """
    # El alta es pública; el rol privilegio se asigna en el servidor, nunca desde la petición.
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Autenticación'], summary='Registrar cuenta de estudiante',
        description='Público: crea una cuenta de estudiante y un carro persistente. El servidor ignora el rol enviado por el cliente.',
        request=UsuarioSerializer,
        examples=[OpenApiExample('Registro de estudiante', value={
            'username': 'estudiante_demo', 'email': 'alumno@example.cl', 'first_name': 'Ana',
            'last_name': 'Pérez', 'telefono': '+56912345678', 'password': 'una-clave-segura',
        }, request_only=True)],
        responses={201: OpenApiResponse(description='Cuenta creada; devuelve tokens de acceso y perfil.'),
                   400: OpenApiResponse(description='Campos inválidos o nombre de usuario duplicado.')},
    )
    def post(self, request):
        # =====================================================================
        # SEGURIDAD: Forzar rol ESTUDIANTE en registro público.
        # Se hace una copia mutable del request.data para sobreescribir el campo
        # 'rol', ignorando cualquier valor que el cliente pudiera enviar.
        # Esto garantiza que ningún usuario pueda auto-asignarse el rol COORDINADOR
        # desde la interfaz web o mediante una solicitud directa a la API.
        # =====================================================================
        data = request.data.copy()
        data['rol'] = 'ESTUDIANTE'  # Registro web siempre crea Estudiantes

        # Aplica las validaciones del usuario; los errores de campo se devuelven sin crear cuenta.
        serializer = UsuarioSerializer(data=data)
        if serializer.is_valid():
            # Persiste la cuenta y genera credenciales inmediatamente para iniciar sesión.
            user = serializer.save()

            # Emisión inmediata de tokens JWT para inicio de sesión directo tras registro
            refresh = CustomTokenObtainPairSerializer.get_token(user)

            # Incluye datos públicos del usuario y ambos JWT en la respuesta de creación.
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

        # Conserva los errores del serializador y comunica que la solicitud no es válida.
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
    # Entrega la portada; quitar el render impediría mostrar el catálogo web.
    return render(request, 'academic/index.html')


def cursos_view(request):
    """Vista de Catálogo de Cursos y Bootcamps."""
    # Reutiliza la plantilla principal; al quitarlo dejaría de renderizarse esta página.
    return render(request, 'academic/index.html')


def carro_view(request):
    """Vista del Carro de Matrícula Persistente."""
    # Renderiza la interfaz del carro; al quitarlo no se serviría esta pantalla.
    return render(request, 'academic/carro.html')


def matriculas_view(request):
    """Vista de Historial de Matrículas e Inscripciones Oficiales."""
    # Renderiza el historial; al quitarlo no se serviría esta pantalla.
    return render(request, 'academic/matriculas.html')


def dashboard_coordinador_view(request):
    """Entrega el shell del panel; sus datos se solicitan a endpoints protegidos por coordinación."""
    return render(request, 'academic/dashboard.html')


def areas_view(request):
    """Entrega la interfaz CRUD de áreas, cuyas mutaciones se autorizan en la API."""
    return render(request, 'academic/areas.html')


def login_view(request):
    """Vista del Formulario de Inicio de Sesión JWT estilo profesional."""
    # Sirve el formulario web; al quitarlo no habría pantalla de acceso.
    return render(request, 'academic/login.html')


def registro_view(request):
    """Vista del Formulario de Registro con Roles estilo profesional."""
    # Sirve el formulario; al quitarlo no habría pantalla para iniciar el registro público.
    return render(request, 'academic/registro.html')


def redirect_to_home(request, path=''):
    """
    Manejador Fallback / Comodín:
    Redirige cualquier ruta no contemplada directamente a la portada ('/'),
    evitando pantallas 404 por defecto de Django según lo requerido por el usuario.
    """
    # Redirige toda ruta de fallback a la URL nombrada index en vez de mostrar el 404 predeterminado.
    return redirect('index')


# Alias que permiten configurar este mismo manejador como fallback o página 404 personalizada.
fallback_view = redirect_to_home
custom_404_view = redirect_to_home
