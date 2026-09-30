from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from academic.models import Area, Curso, CarroMatricula, ItemCarroMatricula

# Toma el modelo de usuario activo para sembrar las cuentas de demostración;
# al quitarlo, el comando no podría crear usuarios compatibles con el proyecto.
User = get_user_model()

class Command(BaseCommand):
    # Django descubre esta clase como el comando `poblar_datos`; sin ella no se
    # podría ejecutar la carga inicial mediante manage.py.
    help = 'Pobla la base de datos con usuarios de prueba (Estudiante y Coordinador), áreas y cursos de EdTech'

    def handle(self, *args, **kwargs):
        # Punto de entrada de la carga idempotente de datos demostrativos;
        # al quitarlo Django ya no tendría lógica que ejecutar para el comando.
        self.stdout.write(self.style.NOTICE("Iniciando carga de datos iniciales EdTech..."))

        # Crea o actualiza el coordinador con acceso administrativo; sin esta
        # cuenta se pierde el usuario de demostración para tareas de coordinación.
        coord, created = User.objects.get_or_create(
            username='coordinador',
            defaults={
                'email': 'coordinador@edtech.cl',
                'first_name': 'Prof. Marcelo',
                'last_name': 'Alvarado',
                'rol': User.RolChoices.COORDINADOR,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            coord.set_password('admin123')
            coord.save()
            self.stdout.write(self.style.SUCCESS("Coordinador 'coordinador' creado (clave: admin123)."))
        else:
            coord.rol = User.RolChoices.COORDINADOR
            coord.is_staff = True
            coord.is_superuser = True
            coord.set_password('admin123')
            coord.save()

        # Crea o actualiza el primer estudiante y sus credenciales de prueba;
        # quitarlo elimina este usuario demostrativo de la base sembrada.
        estudiante1, created = User.objects.get_or_create(
            username='estudiante1',
            defaults={
                'email': 'cesar.aedo@edtech.cl',
                'first_name': 'César',
                'last_name': 'Aedo',
                'rol': User.RolChoices.ESTUDIANTE,
                'rut': '20.123.456-7',
                'telefono': '+56912345678',
            }
        )
        if created:
            estudiante1.set_password('estudiante123')
            estudiante1.save()
            self.stdout.write(self.style.SUCCESS("Estudiante 'estudiante1' creado (clave: estudiante123)."))
        else:
            estudiante1.first_name = 'César'
            estudiante1.last_name = 'Aedo'
            estudiante1.email = 'cesar.aedo@edtech.cl'
            estudiante1.rol = User.RolChoices.ESTUDIANTE
            estudiante1.set_password('estudiante123')
            estudiante1.save()


        # Crea o actualiza un segundo perfil estudiante para pruebas de uso;
        # sin este bloque ya no habría esa cuenta de demostración.
        estudiante2, created = User.objects.get_or_create(
            username='estudiante2',
            defaults={
                'email': 'ana.gomez@edtech.cl',
                'first_name': 'Ana',
                'last_name': 'Gómez',
                'rol': User.RolChoices.ESTUDIANTE,
                'rut': '21.987.654-3',
                'telefono': '+56987654321',
            }
        )
        if created:
            estudiante2.set_password('estudiante123')
            estudiante2.save()
            self.stdout.write(self.style.SUCCESS("Estudiante 'estudiante2' creado (clave: estudiante123)."))
        else:
            estudiante2.rol = User.RolChoices.ESTUDIANTE
            estudiante2.set_password('estudiante123')
            estudiante2.save()

        # Asegura un carro persistente por estudiante para probar la relación
        # usuario-carro; sin estas filas los carros aparecerían solo al crearse
        # mediante el flujo de registro.
        carro1, _ = CarroMatricula.objects.get_or_create(usuario=estudiante1)
        carro2, _ = CarroMatricula.objects.get_or_create(usuario=estudiante2)

        # Define las áreas iniciales y sus datos visibles; al retirarlas el
        # catálogo de muestra carecería de estas categorías.
        areas_data = [
            {
                'nombre': 'Desarrollo Web & Backend',
                'descripcion': 'Arquitectura de servicios REST, Django, frameworks modernos y persistencia relacional.',
                'icono': 'bi-code-slash'
            },
            {
                'nombre': 'Ciberseguridad & Redes',
                'descripcion': 'Seguridad ofensiva y defensiva, auditoría de vulnerabilidades y hardening de sistemas.',
                'icono': 'bi-shield-lock'
            },
            {
                'nombre': 'Inteligencia Artificial & Datos',
                'descripcion': 'Machine Learning, Deep Learning, procesamiento de lenguaje natural y analítica avanzada.',
                'icono': 'bi-cpu'
            },
            {
                'nombre': 'Cloud Architecture & DevOps',
                'descripcion': 'Infraestructura como código, contenedores Docker, Kubernetes y pipelines CI/CD.',
                'icono': 'bi-cloud-check'
            },
        ]

        # Conserva las áreas recuperadas/creadas para asociarlas a los cursos;
        # sin este mapa no se podrían enlazar cursos con su área correspondiente.
        areas_creadas = {}
        for a_data in areas_data:
            area, _ = Area.objects.get_or_create(
                nombre=a_data['nombre'],
                defaults={'descripcion': a_data['descripcion'], 'icono': a_data['icono'], 'activo': True}
            )
            areas_creadas[a_data['nombre']] = area

        # Prepara el catálogo de cursos y bootcamps que se insertará a
        # continuación; al quitarlo no habría oferta inicial demostrativa.
        hoy = date.today()
        cursos_data = [
            {
                'titulo': 'Bootcamp Fullstack Django & PostgreSQL Avanzado',
                'descripcion': 'Construcción integral de APIs REST empresariales con autenticación JWT, transacciones atómicas y PostgreSQL nativo.',
                'area': areas_creadas['Desarrollo Web & Backend'],
                'modalidad': Curso.ModalidadChoices.BOOTCAMP,
                'costo_matricula': Decimal('120000.00'),
                'fecha_inicio': hoy + timedelta(days=10),
                'fecha_termino': hoy + timedelta(days=90),
                'cupos_totales': 25,
                'cupos_disponibles': 25,
                'imagen_url': 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600&auto=format&fit=crop&q=60',
            },
            {
                'titulo': 'Bootcamp Especializado en Ciberseguridad Ofensiva & Pentesting',
                'descripcion': 'Técnicas de penetración, análisis de exploits, seguridad perimetral y mitigación de amenazas críticas.',
                'area': areas_creadas['Ciberseguridad & Redes'],
                'modalidad': Curso.ModalidadChoices.BOOTCAMP,
                'costo_matricula': Decimal('150000.00'),
                'fecha_inicio': hoy + timedelta(days=15),
                'fecha_termino': hoy + timedelta(days=105),
                'cupos_totales': 20,
                'cupos_disponibles': 20,
                'imagen_url': 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=600&auto=format&fit=crop&q=60',
            },
            {
                'titulo': 'Curso de Inteligencia Artificial Generativa y LLMs',
                'descripcion': 'Entrenamiento y despliegue de modelos de lenguaje, embeddings y agentes autónomos inteligentes.',
                'area': areas_creadas['Inteligencia Artificial & Datos'],
                'modalidad': Curso.ModalidadChoices.CURSO,
                'costo_matricula': Decimal('95000.00'),
                'fecha_inicio': hoy + timedelta(days=20),
                'fecha_termino': hoy + timedelta(days=60),
                'cupos_totales': 30,
                'cupos_disponibles': 30,
                'imagen_url': 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=600&auto=format&fit=crop&q=60',
            },
            {
                'titulo': 'Taller Práctico: Despliegue en Kubernetes & CI/CD Pipelines',
                'descripcion': 'Estrategias de orquestación en la nube con microservicios, monitorización y entrega continua automatizada.',
                'area': areas_creadas['Cloud Architecture & DevOps'],
                'modalidad': Curso.ModalidadChoices.TALLER,
                'costo_matricula': Decimal('45000.00'),
                'fecha_inicio': hoy + timedelta(days=5),
                'fecha_termino': hoy + timedelta(days=15),
                'cupos_totales': 15,
                'cupos_disponibles': 15,
                'imagen_url': 'https://images.unsplash.com/photo-1667372393119-3d4c48d07fc9?w=600&auto=format&fit=crop&q=60',
            },
            {
                'titulo': 'Curso Rápido: Fundamentos de Microservicios con FastAPI & Docker',
                'descripcion': 'Diseño de microservicios ultrarrápidos con validación Pydantic, contenedores Docker y concurrencia asíncrona.',
                'area': areas_creadas['Desarrollo Web & Backend'],
                'modalidad': Curso.ModalidadChoices.CURSO,
                'costo_matricula': Decimal('60000.00'),
                'fecha_inicio': hoy + timedelta(days=8),
                'fecha_termino': hoy + timedelta(days=38),
                'cupos_totales': 2, # Cupos reducidos para probar validación de cupos agotados
                'cupos_disponibles': 2,
                'imagen_url': 'https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?w=600&auto=format&fit=crop&q=60',
            }
        ]

        # Reutiliza cursos existentes o registra los faltantes sin duplicar
        # títulos; sin este recorrido los cursos definidos no llegarían a BD.
        cursos_creados = []
        for c_data in cursos_data:
            curso, _ = Curso.objects.get_or_create(
                titulo=c_data['titulo'],
                defaults=c_data
            )
            cursos_creados.append(curso)

        # Agrega un curso al carro inicial del primer estudiante para mostrar
        # persistencia; sin ello ese carro se cargaría vacío al poblar la BD.
        if cursos_creados:
            ItemCarroMatricula.objects.get_or_create(
                carro=carro1,
                curso=cursos_creados[0]
            )

        # Informa resultado y credenciales de las cuentas sembradas; al quitar
        # estas salidas la carga aún funcionaría, pero no se comunicaría su uso.
        self.stdout.write(self.style.SUCCESS("¡Base de datos poblada exitosamente con datos de prueba!"))
        self.stdout.write(self.style.NOTICE("Credenciales de acceso:"))
        self.stdout.write(self.style.NOTICE(" - Coordinador:  usuario 'coordinador' / pass 'admin123'"))
        self.stdout.write(self.style.NOTICE(" - Estudiante 1: usuario 'estudiante1' / pass 'estudiante123' (Tiene 1 curso en su carro)"))
        self.stdout.write(self.style.NOTICE(" - Estudiante 2: usuario 'estudiante2' / pass 'estudiante123'"))
