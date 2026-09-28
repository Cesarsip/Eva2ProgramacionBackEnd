import uuid
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import jwt
from django.conf import settings

from academic.models import Area, Curso, CarroMatricula, ItemCarroMatricula, Matricula, DetalleMatricula

User = get_user_model()

# =====================================================================
# SUITE DE PRUEBAS AUTOMATIZADAS - EVALUACIÓN N°2 BACKEND (100 PUNTOS)
# Valida la integridad técnica, seguridad JWT, RBAC, persistencia de carro,
# transacciones atómicas de stock y filtros.
# =====================================================================

class EdTechBackendTestSuite(TestCase):

    def setUp(self):
        """Inicialización de usuarios con roles RBAC y catálogo inicial."""
        self.client = APIClient()

        # 1. Crear Usuario con Rol Coordinador
        self.coordinador = User.objects.create_user(
            username='coordinador_test',
            email='coord@edtech.cl',
            password='Password123!',
            rol=User.RolChoices.COORDINADOR,
            first_name='Marcelo',
            last_name='Alvarado',
            is_staff=True
        )

        # 2. Crear Usuario con Rol Estudiante
        self.estudiante = User.objects.create_user(
            username='estudiante_test',
            email='estudiante@edtech.cl',
            password='Password123!',
            rol=User.RolChoices.ESTUDIANTE,
            first_name='César',
            last_name='Silva'
        )

        # 3. Crear Área de Conocimiento
        self.area = Area.objects.create(
            nombre='Desarrollo Web & Backend',
            descripcion='Cursos avanzados de Python, Django y PostgreSQL'
        )

        # 4. Crear Cursos de Prueba
        hoy = date.today()
        self.curso1 = Curso.objects.create(
            titulo='Curso Django REST Framework & PostgreSQL',
            descripcion='Arquitectura REST con JWT y control transaccional',
            area=self.area,
            modalidad=Curso.ModalidadChoices.BOOTCAMP,
            costo_matricula=Decimal('100000.00'),
            fecha_inicio=hoy + timedelta(days=10),
            fecha_termino=hoy + timedelta(days=60),
            cupos_totales=20,
            cupos_disponibles=20,
            activo=True
        )

        self.curso_sin_cupo = Curso.objects.create(
            titulo='Taller Cupos Agotados',
            descripcion='Taller intensivo sin vacantes',
            area=self.area,
            modalidad=Curso.ModalidadChoices.TALLER,
            costo_matricula=Decimal('50000.00'),
            fecha_inicio=hoy + timedelta(days=5),
            fecha_termino=hoy + timedelta(days=15),
            cupos_totales=5,
            cupos_disponibles=0,  # 0 cupos libres
            activo=True
        )

    # -----------------------------------------------------------------
    # PRUEBA 1: AUTENTICACIÓN JWT CON CLAIMS PERSONALIZADOS DE ROL
    # -----------------------------------------------------------------
    def test_login_jwt_retorna_tokens_y_claims_de_rol(self):
        """Verifica que el login retorne access y refresh con el rol en el payload."""
        response = self.client.post('/api/token/', {
            'username': 'estudiante_test',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['usuario']['rol'], 'ESTUDIANTE')

        # Decodificar el token para verificar los claims del payload
        access_token = response.data['access']
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
        self.assertEqual(payload['rol'], 'ESTUDIANTE')
        self.assertEqual(payload['username'], 'estudiante_test')

    # -----------------------------------------------------------------
    # PRUEBA 2: PERMISOS RBAC EN CATÁLOGO (PÚBLICO VS COORDINADOR)
    # -----------------------------------------------------------------
    def test_catalogo_es_publico_para_lectura(self):
        """GET /api/cursos/ y /api/areas/ deben ser accesibles anónimamente."""
        res_cursos = self.client.get('/api/cursos/')
        self.assertEqual(res_cursos.status_code, status.HTTP_200_OK)

        res_areas = self.client.get('/api/areas/')
        self.assertEqual(res_areas.status_code, status.HTTP_200_OK)

    def test_estudiante_no_puede_crear_cursos(self):
        """Un estudiante debe recibir HTTP 403 al intentar crear un curso."""
        self.client.force_authenticate(user=self.estudiante)
        response = self.client.post('/api/cursos/', {
            'titulo': 'Curso Hacker',
            'descripcion': 'Intento no autorizado',
            'area': self.area.id,
            'modalidad': 'CURSO',
            'costo_matricula': 10000,
            'cupos_totales': 10,
            'cupos_disponibles': 10,
            'fecha_inicio': '2026-10-01',
            'fecha_termino': '2026-11-01'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_coordinador_si_puede_crear_cursos(self):
        """Un coordinador autenticado puede crear cursos en el catálogo."""
        self.client.force_authenticate(user=self.coordinador)
        response = self.client.post('/api/cursos/', {
            'titulo': 'Nuevo Bootcamp Coordinador',
            'descripcion': 'Aprobado por dirección académica',
            'area': self.area.id,
            'modalidad': 'BOOTCAMP',
            'costo_matricula': 120000,
            'cupos_totales': 15,
            'cupos_disponibles': 15,
            'fecha_inicio': '2026-10-10',
            'fecha_termino': '2026-12-10'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # -----------------------------------------------------------------
    # PRUEBA 3: CARRO DE MATRÍCULA PERSISTENTE Y NO DUPLICIDAD
    # -----------------------------------------------------------------
    def test_persistencia_carro_y_no_duplicados(self):
        """
        Verifica que el carro persista en BD vinculado 1 a 1 al usuario
        y rechace agregar el mismo curso dos veces al carro activo.
        """
        self.client.force_authenticate(user=self.estudiante)

        # 1. Agregar curso al carro
        res1 = self.client.post('/api/carro-matricula/', {'curso_id': self.curso1.id})
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Verificar que el stock NO haya disminuido al agregar al carro
        self.curso1.refresh_from_db()
        self.assertEqual(self.curso1.cupos_disponibles, 20)

        # 2. Intentar agregar el mismo curso por segunda vez (debe fallar)
        res_dup = self.client.post('/api/carro-matricula/', {'curso_id': self.curso1.id})
        self.assertEqual(res_dup.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ya se encuentra en su carro', res_dup.data['error'])

        # 3. Persistencia post-logout: simular desconexión
        self.client.logout()

        # Reconectar y consultar carro
        self.client.force_authenticate(user=self.estudiante)
        res_get = self.client.get('/api/carro-matricula/')
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(res_get.data['total_items'], 1)
        self.assertEqual(res_get.data['items'][0]['curso']['id'], self.curso1.id)

    # -----------------------------------------------------------------
    # PRUEBA 4: CHECKOUT TRANSACCIONAL, DESCUENTO ATÓMICO Y EMISIÓN UUID
    # -----------------------------------------------------------------
    def test_checkout_descuenta_cupos_y_genera_tickets_uuid(self):
        """
        Verifica que al confirmar el carro (PAGADO):
        - Se valide disponibilidad de cupos.
        - Se descuente el cupo en el catálogo (atómico).
        - Se genere la matrícula en PAGADO y tickets con UUID único.
        - Se vacíe el carro persistente.
        """
        self.client.force_authenticate(user=self.estudiante)
        self.client.post('/api/carro-matricula/', {'curso_id': self.curso1.id})

        # Ejecutar checkout
        res_checkout = self.client.post('/api/matriculas/confirmar/')
        self.assertEqual(res_checkout.status_code, status.HTTP_201_CREATED)

        # 1. Validar que el stock del curso se descontó en 1
        self.curso1.refresh_from_db()
        self.assertEqual(self.curso1.cupos_disponibles, 19)

        # 2. Validar que el carro quedó vacío
        carro = CarroMatricula.objects.get(usuario=self.estudiante)
        self.assertEqual(carro.items.count(), 0)

        # 3. Validar estado PAGADO y emisión de UUID
        matricula_data = res_checkout.data['matricula']
        self.assertEqual(matricula_data['estado'], 'PAGADO')
        self.assertTrue(uuid.UUID(matricula_data['codigo_transaccion']))
        self.assertEqual(len(matricula_data['detalles']), 1)
        self.assertTrue(uuid.UUID(matricula_data['detalles'][0]['codigo_ticket']))

    # -----------------------------------------------------------------
    # PRUEBA 5: RECHAZO DE CHECKOUT SI HAY CUPOS INSUFICIENTES
    # -----------------------------------------------------------------
    def test_checkout_rechaza_transaccion_si_no_hay_cupos(self):
        """Si un curso en el carro no tiene cupos disponibles, la compra se rechaza."""
        self.client.force_authenticate(user=self.estudiante)

        # Forzar agregar el curso agotado en el carro
        carro, _ = CarroMatricula.objects.get_or_create(usuario=self.estudiante)
        ItemCarroMatricula.objects.create(carro=carro, curso=self.curso_sin_cupo)

        # Intentar pagar
        res_checkout = self.client.post('/api/matriculas/confirmar/')
        self.assertEqual(res_checkout.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cursos_agotados', res_checkout.data)

        # El curso sigue con 0 cupos y el carro no se borra
        self.curso_sin_cupo.refresh_from_db()
        self.assertEqual(self.curso_sin_cupo.cupos_disponibles, 0)
        self.assertEqual(carro.items.count(), 1)

    # -----------------------------------------------------------------
    # PRUEBA 6: REPOSICIÓN AUTOMÁTICA DE STOCK AL CANCELAR MATRÍCULA
    # -----------------------------------------------------------------
    def test_cancelacion_por_coordinador_repone_cupos_al_catalogo(self):
        """
        Si una orden PAGADA es cancelada por el Coordinador,
        los cupos se liberan automáticamente en PostgreSQL.
        """
        # 1. El estudiante compra el curso1 (baja de 20 a 19 cupos)
        self.client.force_authenticate(user=self.estudiante)
        self.client.post('/api/carro-matricula/', {'curso_id': self.curso1.id})
        res_checkout = self.client.post('/api/matriculas/confirmar/')
        matricula_id = res_checkout.data['matricula']['id']

        self.curso1.refresh_from_db()
        self.assertEqual(self.curso1.cupos_disponibles, 19)

        # 2. El Coordinador cancela la matrícula
        self.client.force_authenticate(user=self.coordinador)
        res_patch = self.client.patch(f'/api/matriculas/{matricula_id}/estado/', {
            'estado': 'CANCELADO'
        })
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        self.assertTrue(res_patch.data['cupos_repuestos'])

        # 3. Verificar que el cupo volvió a 20 automáticamente
        self.curso1.refresh_from_db()
        self.assertEqual(self.curso1.cupos_disponibles, 20)

    # -----------------------------------------------------------------
    # PRUEBA 7: FILTROS CON DJANGO-FILTER EN ENDPOINT /API/CURSOS/
    # -----------------------------------------------------------------
    def test_filtros_django_filter_en_cursos(self):
        """Verifica el funcionamiento de filtros por área y cupos."""
        # Filtro por área existente
        res_area = self.client.get(f'/api/cursos/?area={self.area.id}')
        self.assertEqual(res_area.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_area.data), 2)

        # Filtro por solo cursos con cupo
        res_cupo = self.client.get('/api/cursos/?con_cupo=true')
        self.assertEqual(res_cupo.status_code, status.HTTP_200_OK)
        # Solo curso1 tiene cupos > 0
        self.assertEqual(len(res_cupo.data), 1)
        self.assertEqual(res_cupo.data[0]['id'], self.curso1.id)

    # -----------------------------------------------------------------
    # PRUEBA 8: DOCUMENTACIÓN SWAGGER / OPENAPI EN /API/DOCS/
    # -----------------------------------------------------------------
    def test_documentacion_swagger_operativa(self):
        """Verifica que el endpoint /api/docs/ responda correctamente (200 OK)."""
        response = self.client.get('/api/docs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # -----------------------------------------------------------------
    # PRUEBA 9: RE_PATH FALLBACK REDIRIGE AL INICIO
    # -----------------------------------------------------------------
    def test_fallback_repath_redirige_a_inicio(self):
        """Cualquier ruta inválida debe redirigir al inicio mediante fallback (302)."""
        response = self.client.get('/ruta-inexistente-12345/')
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, '/')
