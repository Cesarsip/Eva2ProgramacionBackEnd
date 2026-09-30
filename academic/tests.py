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

# Usa el modelo de usuario configurado en Django; sin esta resolución la suite
# dependería de un modelo fijo y fallaría al probar el usuario personalizado.
User = get_user_model()

# =====================================================================
# SUITE DE PRUEBAS AUTOMATIZADAS - EVALUACIÓN N°2 BACKEND (100 PUNTOS)
# Valida la integridad técnica, seguridad JWT, RBAC, persistencia de carro,
# transacciones atómicas de stock y filtros.
# Si se elimina esta suite, esos comportamientos dejan de verificarse
# automáticamente y las regresiones podrían pasar inadvertidas.
# =====================================================================

class EdTechBackendTestSuite(TestCase):

    def setUp(self):
        """Inicialización de usuarios con roles RBAC y catálogo inicial."""
        # Cada prueba parte con datos aislados y repetibles; sin esta preparación
        # las pruebas dependerían de registros externos o de ejecuciones previas.
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

    def test_visitante_puede_abrir_carro_y_ver_su_acceso_en_catalogo(self):
        """El navbar, el catálogo y la vista del carro exponen el flujo de invitado."""
        catalogo = self.client.get('/catalogo/')
        self.assertEqual(catalogo.status_code, status.HTTP_200_OK)
        self.assertContains(catalogo, 'id="nav-item-carro"')
        self.assertContains(catalogo, 'id="catalog-cart-link"')
        self.assertContains(catalogo, 'id="catalog-cart-badge"')

        carro = self.client.get('/carro/')
        self.assertEqual(carro.status_code, status.HTTP_200_OK)
        self.assertContains(carro, 'localStorage')
        self.assertContains(carro, 'Iniciar Sesión para Confirmar Matrícula')
        self.assertContains(carro, 'Registrarse para Matricularse')

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

    def test_coordinador_crud_de_areas_y_estudiante_solo_lectura(self):
        """Coordinación puede crear/editar/eliminar áreas y el estudiante solo consultarlas."""
        self.client.force_authenticate(user=self.coordinador)
        crear = self.client.post('/api/areas/', {
            'nombre': 'Diseño de Producto',
            'descripcion': 'UX y diseño digital',
            'icono': 'bi-palette',
            'activo': True
        }, format='json')
        self.assertEqual(crear.status_code, status.HTTP_201_CREATED)
        area_id = crear.data['id']

        editar = self.client.patch(
            f'/api/areas/{area_id}/',
            {'descripcion': 'Diseño UX y UI'},
            format='json'
        )
        self.assertEqual(editar.status_code, status.HTTP_200_OK)
        self.assertEqual(editar.data['descripcion'], 'Diseño UX y UI')

        self.client.force_authenticate(user=self.estudiante)
        lectura = self.client.get(f'/api/areas/{area_id}/')
        self.assertEqual(lectura.status_code, status.HTTP_200_OK)
        no_autorizado = self.client.delete(f'/api/areas/{area_id}/')
        self.assertEqual(no_autorizado.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.coordinador)
        eliminar = self.client.delete(f'/api/areas/{area_id}/')
        self.assertEqual(eliminar.status_code, status.HTTP_204_NO_CONTENT)

    def test_panel_coordinador_ve_todas_y_estudiante_solo_sus_matriculas(self):
        """El panel global admite personal staff y el historial del estudiante queda filtrado por propietario."""
        otro_estudiante = User.objects.create_user(
            username='otro_estudiante',
            email='otro@edtech.cl',
            password='Password123!',
            rol=User.RolChoices.ESTUDIANTE
        )
        staff_con_rol_estudiante = User.objects.create_user(
            username='staff_academico',
            email='staff@edtech.cl',
            password='Password123!',
            rol=User.RolChoices.ESTUDIANTE,
            is_staff=True
        )
        matricula_propia = Matricula.objects.create(
            estudiante=self.estudiante,
            total=Decimal('100000.00'),
            estado=Matricula.EstadoMatriculaChoices.PAGADO
        )
        matricula_ajena = Matricula.objects.create(
            estudiante=otro_estudiante,
            total=Decimal('50000.00'),
            estado=Matricula.EstadoMatriculaChoices.PAGADO
        )

        self.client.force_authenticate(user=staff_con_rol_estudiante)
        panel_global = self.client.get('/api/matriculas/')
        self.assertEqual(panel_global.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {item['id'] for item in panel_global.data},
            {matricula_propia.id, matricula_ajena.id}
        )

        self.client.force_authenticate(user=self.estudiante)
        historial_personal = self.client.get('/api/mis-matriculas/')
        self.assertEqual(historial_personal.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in historial_personal.data], [matricula_propia.id])

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
        curso_id = response.data['id']

        # PUT/PATCH y DELETE completan el CRUD del catálogo mediante el ViewSet.
        respuesta_edicion = self.client.patch(
            f'/api/cursos/{curso_id}/',
            {'titulo': 'Bootcamp actualizado'},
            format='json'
        )
        self.assertEqual(respuesta_edicion.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta_edicion.data['titulo'], 'Bootcamp actualizado')

        respuesta_eliminacion = self.client.delete(f'/api/cursos/{curso_id}/')
        self.assertEqual(respuesta_eliminacion.status_code, status.HTTP_204_NO_CONTENT)

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

    def test_no_permite_agregar_al_carro_un_curso_ya_matriculado(self):
        """Una compra activa bloquea una segunda inscripción al mismo curso."""
        self.client.force_authenticate(user=self.estudiante)
        self.client.post('/api/carro-matricula/', {'curso_id': self.curso1.id})
        checkout = self.client.post('/api/matriculas/confirmar/')
        self.assertEqual(checkout.status_code, status.HTTP_201_CREATED)

        repeticion = self.client.post('/api/carro-matricula/', {'curso_id': self.curso1.id})
        self.assertEqual(repeticion.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('inscripción activa', repeticion.data['error'])

        carro = CarroMatricula.objects.get(usuario=self.estudiante)
        self.assertEqual(carro.items.count(), 0)

    def test_checkout_rechaza_curso_matriculado_tras_agregarlo_al_carro(self):
        """Revalida duplicados en checkout si la inscripción se creó después del carro."""
        carro, _ = CarroMatricula.objects.get_or_create(usuario=self.estudiante)
        ItemCarroMatricula.objects.create(carro=carro, curso=self.curso1)
        Matricula.objects.create(
            estudiante=self.estudiante,
            total=self.curso1.costo_matricula,
            estado=Matricula.EstadoMatriculaChoices.PAGADO
        ).detalles.create(
            curso=self.curso1,
            precio_unitario=self.curso1.costo_matricula
        )

        self.client.force_authenticate(user=self.estudiante)
        respuesta = self.client.post('/api/matriculas/confirmar/')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cursos_ya_matriculados', respuesta.data)

        self.curso1.refresh_from_db()
        self.assertEqual(self.curso1.cupos_disponibles, 20)
        self.assertEqual(carro.items.count(), 1)

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

    def test_coordinador_reactiva_boleta_cancelada_con_validacion_de_stock(self):
        """El coordinador puede reactivar con cupos y el stock cambia de forma transaccional."""
        self.client.force_authenticate(user=self.estudiante)
        self.client.post('/api/carro-matricula/', {'curso_id': self.curso1.id})
        checkout = self.client.post('/api/matriculas/confirmar/')
        matricula_id = checkout.data['matricula']['id']
        self.curso1.refresh_from_db()
        self.assertEqual(self.curso1.cupos_disponibles, 19)

        # El cliente de prueba venía autenticado como estudiante; limpia ese override
        # para verificar que el endpoint funciona realmente con el JWT Bearer.
        self.client.force_authenticate(user=None)
        login_coordinador = self.client.post('/api/token/', {
            'username': 'coordinador_test',
            'password': 'Password123!'
        })
        self.assertEqual(login_coordinador.status_code, status.HTTP_200_OK)
        self.assertEqual(login_coordinador.data['usuario']['rol'], 'COORDINADOR')
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_coordinador.data['access']}"
        )
        cancelada = self.client.patch(
            f'/api/matriculas/{matricula_id}/estado/',
            {'estado': 'CANCELADO'}
        )
        self.assertEqual(cancelada.status_code, status.HTTP_200_OK, cancelada.data)
        self.assertTrue(cancelada.data['cupos_repuestos'])
        self.curso1.refresh_from_db()
        self.assertEqual(self.curso1.cupos_disponibles, 20)

        reactivada = self.client.patch(
            f'/api/matriculas/{matricula_id}/estado/',
            {'estado': 'PAGADO'}
        )
        self.assertEqual(reactivada.status_code, status.HTTP_200_OK)
        self.assertTrue(reactivada.data['cupos_reservados'])
        self.curso1.refresh_from_db()
        self.assertEqual(self.curso1.cupos_disponibles, 19)

        pendiente = self.client.patch(
            f'/api/matriculas/{matricula_id}/estado/',
            {'estado': 'PENDIENTE'}
        )
        self.assertEqual(pendiente.status_code, status.HTTP_200_OK)
        self.assertTrue(pendiente.data['cupos_repuestos'])
        self.curso1.refresh_from_db()
        self.assertEqual(self.curso1.cupos_disponibles, 20)

    def test_coordinador_no_reactiva_boleta_si_falta_cupo(self):
        """La falta de cupo deja intactos el estado y el inventario de la boleta."""
        self.client.force_authenticate(user=self.estudiante)
        self.client.post('/api/carro-matricula/', {'curso_id': self.curso1.id})
        checkout = self.client.post('/api/matriculas/confirmar/')
        matricula_id = checkout.data['matricula']['id']

        self.client.force_authenticate(user=self.coordinador)
        self.client.patch(
            f'/api/matriculas/{matricula_id}/estado/',
            {'estado': 'CANCELADO'}
        )
        self.curso1.cupos_disponibles = 0
        self.curso1.save(update_fields=['cupos_disponibles'])

        respuesta = self.client.patch(
            f'/api/matriculas/{matricula_id}/estado/',
            {'estado': 'PAGADO'}
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cursos_agotados', respuesta.data)
        self.assertEqual(
            Matricula.objects.get(id=matricula_id).estado,
            Matricula.EstadoMatriculaChoices.CANCELADO
        )
        self.curso1.refresh_from_db()
        self.assertEqual(self.curso1.cupos_disponibles, 0)

    def test_coordinador_no_reactiva_si_estudiante_ya_compro_el_mismo_curso(self):
        """Reactivar no puede crear dos matrículas vigentes para el mismo curso."""
        self.client.force_authenticate(user=self.estudiante)
        self.client.post('/api/carro-matricula/', {'curso_id': self.curso1.id})
        primera_compra = self.client.post('/api/matriculas/confirmar/')
        matricula_anterior_id = primera_compra.data['matricula']['id']

        self.client.force_authenticate(user=self.coordinador)
        self.client.patch(
            f'/api/matriculas/{matricula_anterior_id}/estado/',
            {'estado': 'CANCELADO'}
        )

        self.client.force_authenticate(user=self.estudiante)
        self.client.post('/api/carro-matricula/', {'curso_id': self.curso1.id})
        segunda_compra = self.client.post('/api/matriculas/confirmar/')
        self.assertEqual(segunda_compra.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.coordinador)
        reactivacion = self.client.patch(
            f'/api/matriculas/{matricula_anterior_id}/estado/',
            {'estado': 'PAGADO'}
        )
        self.assertEqual(reactivacion.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cursos_ya_matriculados', reactivacion.data)
        self.assertEqual(
            Matricula.objects.get(id=matricula_anterior_id).estado,
            Matricula.EstadoMatriculaChoices.CANCELADO
        )
        self.curso1.refresh_from_db()
        self.assertEqual(self.curso1.cupos_disponibles, 19)

    def test_cancelar_boleta_cancela_todos_sus_cursos_y_devuelve_todos_los_cupos(self):
        """Cancelar una boleta devuelve cada cupo de la orden completa."""
        curso_extra = Curso.objects.create(
            titulo='Curso FastAPI & Microservicios',
            descripcion='Arquitectura moderna de APIs',
            area=self.area,
            modalidad=Curso.ModalidadChoices.CURSO,
            costo_matricula=Decimal('80000.00'),
            fecha_inicio=date.today() + timedelta(days=15),
            fecha_termino=date.today() + timedelta(days=45),
            cupos_totales=15,
            cupos_disponibles=15,
            activo=True
        )

        self.client.force_authenticate(user=self.estudiante)
        self.client.post('/api/carro-matricula/', {
            'cursos_ids': [self.curso1.id, curso_extra.id]
        }, format='json')
        checkout = self.client.post('/api/matriculas/confirmar/')
        self.assertEqual(checkout.status_code, status.HTTP_201_CREATED)
        matricula = checkout.data['matricula']
        self.assertEqual(len(matricula['detalles']), 2)

        # La boleta agrupa ambos cursos; su cancelación repone todos sus cupos.
        self.client.force_authenticate(user=self.coordinador)
        cancelacion_total = self.client.patch(
            f"/api/matriculas/{matricula['id']}/estado/",
            {'estado': 'CANCELADO'}
        )
        self.assertEqual(cancelacion_total.status_code, status.HTTP_200_OK)
        self.curso1.refresh_from_db()
        curso_extra.refresh_from_db()
        self.assertEqual(self.curso1.cupos_disponibles, 20)
        self.assertEqual(curso_extra.cupos_disponibles, 15)
        matricula_db = Matricula.objects.get(id=matricula['id'])
        self.assertEqual(matricula_db.estado, Matricula.EstadoMatriculaChoices.CANCELADO)
        self.assertEqual(matricula_db.total, Decimal('180000.00'))
        self.assertEqual(matricula_db.detalles.count(), 2)

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

        # El filtro complementario debe devolver solo cursos sin disponibilidad.
        res_agotado = self.client.get('/api/cursos/?agotado=true')
        self.assertEqual(res_agotado.status_code, status.HTTP_200_OK)
        self.assertEqual([curso['id'] for curso in res_agotado.data], [self.curso_sin_cupo.id])

    # -----------------------------------------------------------------
    # PRUEBA 8: DOCUMENTACIÓN SWAGGER / OPENAPI EN /API/DOCS/
    # -----------------------------------------------------------------
    def test_documentacion_swagger_operativa(self):
        """Verifica Swagger UI y que el esquema OpenAPI agrupe y describa los recursos reales."""
        response = self.client.get('/api/docs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schema = self.client.get('/api/schema/')
        self.assertEqual(schema.status_code, status.HTTP_200_OK)
        self.assertIn('paths', schema.data)
        self.assertIn('/api/cursos/', schema.data['paths'])
        self.assertIn('/api/matriculas/confirmar/', schema.data['paths'])
        self.assertIn('Cursos', {tag['name'] for tag in schema.data['tags']})
        filtros_cursos = schema.data['paths']['/api/cursos/']['get']['parameters']
        self.assertIn('agotado', [parametro['name'] for parametro in filtros_cursos])

    def test_bajas_logicas_de_areas_y_cursos_se_pueden_revertir(self):
        """Desactivar preserva las relaciones y las rutas de reactivación restauran la oferta."""
        self.client.force_authenticate(user=self.coordinador)
        baja_area = self.client.delete(f'/api/areas/{self.area.id}/')
        self.assertEqual(baja_area.status_code, status.HTTP_204_NO_CONTENT)
        self.area.refresh_from_db()
        self.assertFalse(self.area.activo)
        self.assertTrue(Curso.objects.filter(area=self.area).exists())

        areas_inactivas_coordinador = self.client.get('/api/areas/')
        self.assertEqual(areas_inactivas_coordinador.status_code, status.HTTP_200_OK)
        self.assertTrue(any(not area['activo'] for area in areas_inactivas_coordinador.data))

        reactivar_area = self.client.post(f'/api/areas/{self.area.id}/reactivar/')
        self.assertEqual(reactivar_area.status_code, status.HTTP_200_OK)
        self.area.refresh_from_db()
        self.assertTrue(self.area.activo)

        baja_curso = self.client.delete(f'/api/cursos/{self.curso1.id}/')
        self.assertEqual(baja_curso.status_code, status.HTTP_204_NO_CONTENT)
        self.curso1.refresh_from_db()
        self.assertFalse(self.curso1.activo)

        # Simula una consulta anónima: coordinación sí puede ver cursos inactivos.
        self.client.force_authenticate(user=None)
        oferta_publica = self.client.get('/api/cursos/')
        self.assertEqual(oferta_publica.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.curso1.id, [curso['id'] for curso in oferta_publica.data])

        self.client.force_authenticate(user=self.coordinador)
        reactivar_curso = self.client.post(f'/api/cursos/{self.curso1.id}/reactivar/')
        self.assertEqual(reactivar_curso.status_code, status.HTTP_200_OK)
        self.curso1.refresh_from_db()
        self.assertTrue(self.curso1.activo)

    # -----------------------------------------------------------------
    # PRUEBA 9: RE_PATH FALLBACK REDIRIGE AL INICIO
    # -----------------------------------------------------------------
    def test_fallback_repath_redirige_a_inicio(self):
        """Cualquier ruta inválida debe redirigir al inicio mediante fallback (302)."""
        response = self.client.get('/ruta-inexistente-12345/')
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, '/')

    # -----------------------------------------------------------------
    # PRUEBA 10: REGISTRO DE USUARIOS CON ROL (ESTUDIANTE / COORDINADOR)
    # -----------------------------------------------------------------
    def test_registro_usuario_con_rol(self):
        """Verifica que el registro cree al usuario con su rol y carro persistente."""
        res = self.client.post('/api/registro/', {
            'first_name': 'Juan',
            'last_name': 'Perez',
            'email': 'juan@edtech.cl',
            'username': 'juanperez',
            'telefono': '+56911223344',
            'password': 'Password123!',
            'rol': 'ESTUDIANTE'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', res.data)
        self.assertEqual(res.data['usuario']['rol'], 'ESTUDIANTE')

        # Verificar que se creó su carro persistente
        self.assertTrue(CarroMatricula.objects.filter(usuario__username='juanperez').exists())

    # -----------------------------------------------------------------
    # PRUEBA 11: SINCRONIZACIÓN POR LOTES DE CARRO ANÓNIMO A POSTGRESQL
    # -----------------------------------------------------------------
    def test_sincronizacion_carro_anonimo_por_lotes(self):
        """
        Verifica que al sincronizar cursos desde localStorage (cursos_ids),
        se agreguen al carro en PostgreSQL sin duplicar los ya existentes.
        """
        self.client.force_authenticate(user=self.estudiante)

        # Crear un curso extra
        curso_extra = Curso.objects.create(
            titulo='Curso FastAPI & Microservicios',
            descripcion='Arquitectura moderna de APIs',
            area=self.area,
            modalidad=Curso.ModalidadChoices.CURSO,
            costo_matricula=Decimal('80000.00'),
            fecha_inicio=date.today() + timedelta(days=15),
            fecha_termino=date.today() + timedelta(days=45),
            cupos_totales=15,
            cupos_disponibles=15,
            activo=True
        )

        # Enviar lista de cursos acumulados anónimamente
        res = self.client.post('/api/carro-matricula/', {
            'cursos_ids': [self.curso1.id, curso_extra.id]
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_items'], 2)

        # Reenviar cursos del carro debe rechazarse claramente sin alterar el lote existente.
        res_dup = self.client.post('/api/carro-matricula/', {
            'cursos_ids': [self.curso1.id, curso_extra.id]
        }, format='json')
        self.assertEqual(res_dup.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('carro de matrícula', res_dup.data['error'])
        carro = CarroMatricula.objects.get(usuario=self.estudiante)
        self.assertEqual(carro.items.count(), 2)

        # Dos IDs iguales en el mismo lote también se rechazan sin insertar parcialmente.
        carro.items.all().delete()
        res_repetido_en_lote = self.client.post('/api/carro-matricula/', {
            'cursos_ids': [self.curso1.id, self.curso1.id]
        }, format='json')
        self.assertEqual(res_repetido_en_lote.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('más de una vez', res_repetido_en_lote.data['error'])
        self.assertEqual(carro.items.count(), 0)
