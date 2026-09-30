# Guía Maestra de Defensa Oral y Preguntas Técnicas &middot; EVA-2
## Asignatura: Desarrollo Backend &middot; Ponderación Oral: 70 Puntos (70%)
### Proyecto 2: Plataforma de Reservas de Cursos y Bootcamps (EdTech)
**Estudiante:** CESAR ANTONIO AEDO ALVAREZ &middot; **Sección:** IEC-N4-C2 &middot; **Docente:** Marcelo Alvarado &middot; **Año:** 2026


---

## 🏛️ Criterio 1: Dominio de la Arquitectura, Configuración DB y Modelos (12 Pts)

### Pregunta 1.1: ¿Cómo está configurado PostgreSQL en Django y qué ventajas ofrece sobre SQLite?
> **Respuesta:**
> En `academic_project/settings.py`, el diccionario `DATABASES['default']` utiliza de forma nativa el motor `django.db.backends.postgresql`:
> ```python
> DATABASES = {
>     'default': {
>         'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.postgresql'),
>         'NAME': os.environ.get('DB_NAME', 'edtech_db'),
>         'USER': os.environ.get('DB_USER', 'postgres'),
>         'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
>         'HOST': os.environ.get('DB_HOST', 'localhost'),
>         'PORT': os.environ.get('DB_PORT', '5432'),
>     }
> }
> ```
> **Ventajas técnicas de PostgreSQL:**
> 1. **Concurrencia real a nivel de fila:** Soporta bloqueos pesimistas (`SELECT FOR UPDATE`), esenciales para el control transaccional de cupos de cursos, a diferencia de SQLite que bloquea el archivo entero de la base de datos al escribir.
> 2. **Integridad referencial y tipos nativos:** Soporte nativo para tipos UUID, campos numéricos decimales exactos (`Numeric/Decimal`), índices hash y B-tree.
> 3. **Escalabilidad de producción:** Permite múltiples conexiones concurrentes sin sufrir errores de "database is locked".

### Pregunta 1.2: ¿Cuáles son las relaciones entre tablas del sistema y por qué se usaron?
> **Respuesta:**
> - **Usuario a CarroMatricula (1 a 1 - `OneToOneField`):** Garantiza que cada estudiante tenga exactamente un único carro activo persistente en base de datos.
> - **CarroMatricula a ItemCarroMatricula (1 a N - `ForeignKey`):** Permite que un carro contenga múltiples cursos seleccionados. Con `unique_together = ('carro', 'curso')` se asegura que no se pueda agregar el mismo curso dos veces al mismo carro activo.
> - **Area a Curso (1 a N - `ForeignKey`):** Cada curso pertenece a una única área de conocimiento (ej: Ciberseguridad, Desarrollo Web).
> - **Matricula a DetalleMatricula (1 a N - `ForeignKey`):** Una orden histórica consolida múltiples inscripciones de cursos.
> - **DetalleMatricula a Curso (`ForeignKey(on_delete=models.PROTECT)`):** Se usa `PROTECT` para que no se pueda borrar un curso del catálogo si ya existen matrículas históricas asociadas a él.

### Pregunta 1.3: ¿Dónde y por qué se utilizó la propiedad explícita CHOICES en los modelos?
> **Respuesta:**
> Se implementó en tres modelos clave mediante `models.TextChoices`:
> 1. `Usuario.RolChoices`: Restringe el acceso a `ESTUDIANTE` y `COORDINADOR`.
> 2. `Curso.ModalidadChoices`: Restringe el tipo de programa a `BOOTCAMP` (Bootcamp Intensivo), `CURSO` (Curso Regular) y `TALLER` (Taller Especializado).
> 3. `Matricula.EstadoMatriculaChoices`: Define la máquina de estados de la transacción:
>    ```python
>    class EstadoMatriculaChoices(models.TextChoices):
>        PENDIENTE = 'PENDIENTE', 'Pendiente de Pago'
>        PAGADO = 'PAGADO', 'Pagado'
>        COMPLETADO = 'COMPLETADO', 'Completado'
>        CANCELADO = 'CANCELADO', 'Cancelado'
>    ```
> Si se eliminara `CHOICES`, la base de datos y los serializadores aceptarían cualquier cadena de texto arbitraria, rompiendo la integridad de estados de la orden y los permisos del sistema.

---

## 🔐 Criterio 2: Defensa del Flujo JWT, Claims de Rol y Permisos RBAC (12 Pts)

### Pregunta 2.1: ¿Cómo se implementó la autenticación JWT y la inyección de claims de rol?
> **Respuesta:**
> Se utilizó la librería `djangorestframework-simplejwt`. En lugar de emitir un token estándar, se creó el serializador personalizado `CustomTokenObtainPairSerializer` que sobreescribe el método de clase `get_token(cls, user)`:
> ```python
> @classmethod
> def get_token(cls, user):
>     token = super().get_token(user)
>     # Inyección de claims en el payload del JWT
>     token['rol'] = user.rol
>     token['username'] = user.username
>     token['email'] = user.email
>     token['nombre_completo'] = f"{user.first_name} {user.last_name}".strip()
>     return token
> ```
> De esta forma, cualquier servicio o cliente puede descifrar el payload del token y leer el rol del usuario directamente sin realizar consultas adicionales a la base de datos.

### Pregunta 2.2: ¿Cómo interactúan los claims del token con las clases de permisos en DRF?
> **Respuesta:**
> Cuando el cliente envía `Authorization: Bearer <access_token>`, `JWTAuthentication` valida la firma criptográfica con la `SECRET_KEY` y carga la instancia del usuario en `request.user`.
> Luego, las clases de permiso personalizadas en `academic/permissions.py` inspeccionan dicho objeto:
> - `IsEstudiante`: Verifica `request.user.is_authenticated and request.user.rol == 'ESTUDIANTE'`.
> - `IsCoordinador`: Verifica `request.user.is_authenticated and (request.user.rol == 'COORDINADOR' or request.user.is_staff)`.
> - `IsCoordinadorOrReadOnly`: Para métodos seguros (`GET`, `HEAD`, `OPTIONS`) permite el acceso público (`SAFE_METHODS`); para métodos de mutación (`POST`, `PUT`, `DELETE`), exige que sea Coordinador.

---

## 🛒 Criterio 3: Defensa del Carro de Compras Persistente (12 Pts)

### Pregunta 3.1: ¿Cómo se garantiza técnicamente que el carro persista post-logout y entre distintos dispositivos?
> **Respuesta:**
> En `academic/models.py`, el modelo `CarroMatricula` no utiliza sesiones temporales de Django ni `localStorage` del frontend para almacenar los ítems. Se modela como una tabla nativa en PostgreSQL vinculada al `id` del usuario (`OneToOneField(Usuario)`):
> ```python
> class CarroMatricula(models.Model):
>     usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carro_matricula')
> ```
> Cuando el estudiante hace `GET /api/carro-matricula/`, el backend ejecuta:
> ```python
> carro, _ = CarroMatricula.objects.get_or_create(usuario=request.user)
> ```
> Aunque el alumno cierre sesión (`logout`), borre sus cookies o inicie sesión desde su teléfono móvil, al autenticarse con su token JWT, el backend siempre consultará la misma fila en PostgreSQL asociada a su `user.id`.

### Pregunta 3.2: ¿Dónde se implementa la regla de negocio que prohíbe agregar el mismo curso dos veces al carro?
> **Respuesta:**
> Se implementa en dos niveles:
> 1. **Nivel Base de Datos (Integridad dura):** En `ItemCarroMatricula.Meta` con `unique_together = ('carro', 'curso')`.
> 2. **Nivel API (Validación lógica en `views.py`):**
>    ```python
>    if ItemCarroMatricula.objects.filter(carro=carro, curso=curso).exists():
>        return Response(
>            {"error": f"El curso '{curso.titulo}' ya se encuentra en su carro de matrícula activo."},
>            status=status.HTTP_400_BAD_REQUEST
>        )
>    ```

### Pregunta 3.3: ¿Por qué el stock de cupos NO se descuenta al agregar un curso al carro?
> **Respuesta:**
> Si se descontara el cupo al agregar al carro, un usuario malintencionado podría "reservar" todos los cupos del catálogo agregándolos a su carro sin pagarlos, dejando a la academia sin disponibilidad para estudiantes reales (ataque de denegación de servicio de inventario). Por ello, el carro solo almacena **intención de compra**; el descuento atómico se realiza únicamente al validar el pago durante el checkout.

---

## ⚡ Criterio 4: Defensa del Ciclo Transaccional, Checkout y Stock (12 Pts)

### Pregunta 4.1: Explique el flujo exacto del Checkout y cómo se previenen condiciones de carrera (Race Conditions).
> **Respuesta:**
> En el endpoint `POST /api/matriculas/confirmar/`:
> 1. Se abre un bloque transaccional atómico con `with transaction.atomic():`.
> 2. Se obtienen los IDs de los cursos en el carro y se aplica **bloqueo pesimista de fila** con `select_for_update()`:
>    ```python
>    cursos_bloqueados = {
>        c.id: c for c in Curso.objects.select_for_update().filter(id__in=curso_ids)
>    }
>    ```
>    Esto previene que dos estudiantes paguen el último cupo al mismo milisegundo: la segunda transacción debe esperar a que la primera termine y leerá el saldo actualizado.
> 3. Se valida que `curso.cupos_disponibles >= 1`. Si algún curso no tiene cupo, la transacción se aborta con `HTTP 400`.
> 4. Si hay stock:
>    - Se descuenta el cupo: `curso.cupos_disponibles -= 1; curso.save()`.
>    - Se genera la `Matricula` en estado `PAGADO` con su código UUID.
>    - Se generan las inscripciones oficiales (`DetalleMatricula`) asignando un ticket único `UUID` por cada curso.
>    - Se vacían los ítems del carro: `carro.items.all().delete()`.

### Pregunta 4.2: ¿Qué ocurre si un Coordinador cancela una matrícula previamente pagada?
> **Respuesta:**
> En `PATCH /api/matriculas/{id}/estado/`:
> Si el nuevo estado es `CANCELADO` y el estado anterior era `PAGADO` o `COMPLETADO`, dentro de un bloque `transaction.atomic()`, el backend recupera cada curso inscrito y restituye el cupo disponible:
> ```python
> for detalle in matricula_bloqueada.detalles.select_related('curso').all():
>     curso = Curso.objects.select_for_update().get(id=detalle.curso_id)
>     curso.cupos_disponibles = min(curso.cupos_totales, curso.cupos_disponibles + 1)
>     curso.save(update_fields=['cupos_disponibles'])
> ```
> De esta forma, el cupo vuelve inmediatamente a estar disponible en el catálogo para que otro estudiante pueda matricularse.

---

## 🔍 Criterio 5: Explicación de Filtros, Búsqueda y Documentación OpenAPI (10 Pts)

### Pregunta 5.1: ¿Cómo funciona `django-filter` y qué parámetros acepta el catálogo?
> **Respuesta:**
> Se configuró `DjangoFilterBackend` en `settings.py` y en `CursoViewSet`. La clase `CursoFilter` (`academic/filters.py`) mapea los parámetros de la URL a consultas optimizadas del ORM:
> - `?area=1`: Filtra exactamente por el ID del área.
> - `?area_nombre=web`: Búsqueda parcial case-insensitive (`icontains`) sobre el nombre del área.
> - `?titulo=django`: Búsqueda parcial (`icontains`) sobre el título del curso.
> - `?precio_min=50000` y `?precio_max=150000`: Rango de precios (`costo_matricula__gte` y `costo_matricula__lte`).
> - `?con_cupo=true`: Filtra únicamente aquellos cursos donde `cupos_disponibles > 0`.

### Pregunta 5.2: ¿Cómo está integrada la documentación Swagger / OpenAPI?
> **Respuesta:**
> Se utilizó `drf-yasg`. En `academic_project/urls.py` se definió `schema_view` y se expuso operativamente en la ruta exigida por la pauta de cotejo:
> ```python
> path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-docs'),
> ```
> Permite inspeccionar todos los endpoints de la API, probar la autenticación Bearer JWT mediante el botón `Authorize` y visualizar los esquemas de entrada y salida de datos.

---

## 🎨 Criterio 6: Justificación de Calidad del Código, Comentarios y Footer (12 Pts)

### Pregunta 6.1: ¿Cómo se implementó la renderización de los datos del alumno en el footer?
> **Respuesta:**
> Se diseñó un `Context Processor` en `academic/context_processors.py`:
> ```python
> def student_footer_context(request):
>     student_info = getattr(settings, 'STUDENT_DATA', {...})
>     return {
>         'ALUMNO_NOMBRE': student_info.get('NOMBRE_COMPLETO'),
>         'ALUMNO_SECCION': student_info.get('SECCION'),
>         'ALUMNO_ANIO': student_info.get('ANIO'),
>     }
> ```
> Este procesador está registrado en `settings.py` dentro de `TEMPLATES['OPTIONS']['context_processors']`, lo que hace que variables como `{{ ALUMNO_NOMBRE }}`, `{{ ALUMNO_SECCION }}` y `{{ ALUMNO_ANIO }}` estén disponibles automáticamente en `templates/academic/base.html` y en cualquier vista HTML sin necesidad de inyectarlas manualmente en cada controlador.

### Pregunta 6.2: ¿Cómo se estructuró la documentación en bloques del código fuente?
> **Respuesta:**
> Cada archivo (`models.py`, `serializers.py`, `views.py`, `permissions.py`, `filters.py`, `settings.py`) está seccionado en bloques comentados que explican:
> 1. El objetivo del bloque de código.
> 2. El criterio de evaluación o regla de negocio que satisface.
> 3. El impacto que ocurriría en el sistema si dicho bloque fuese eliminado o alterado.
