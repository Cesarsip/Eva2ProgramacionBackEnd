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
> Los módulos principales (`models.py`, `serializers.py`, `views.py`, `permissions.py`, `filters.py`, `settings.py`) están organizados en bloques comentados y docstrings que explican:
> 1. El objetivo del bloque de código.
> 2. El criterio de evaluación o regla de negocio que satisface.
> 3. El impacto que ocurriría en el sistema si dicho bloque fuese eliminado o alterado.

### Aclaración importante para la defensa
> El checkout de este proyecto **simula la confirmación del pago**: no integra una pasarela bancaria real. Al confirmar, registra la matrícula como `PAGADO`, descuenta cupos y emite tickets dentro de una transacción. Si preguntan por pagos reales, explica que haría falta integrar un proveedor externo y verificar su confirmación antes de marcar la orden como pagada.

---

## 🎤 Simulación de preguntas orales

Intenta responder cada pregunta en voz alta en 30–60 segundos antes de leer la respuesta. En la defensa, explica primero la idea, luego nombra el archivo o mecanismo y termina diciendo qué pasa si se quita.

### 1. ¿Qué diferencia hay entre autenticación y autorización?
> **Respuesta:** La autenticación comprueba quién es el usuario; aquí se realiza al validar el JWT. La autorización decide qué puede hacer ese usuario; aquí se aplica con permisos DRF y su rol (`ESTUDIANTE` o `COORDINADOR`). Sin autenticación no se identifica al solicitante; sin autorización un usuario autenticado podría ejecutar acciones que no le corresponden.

### 2. ¿Qué hace un modelo de Django?
> **Respuesta:** Define la estructura de una entidad y cómo se guarda en la base de datos. Por ejemplo, `Curso` determina campos como título, precio y cupos, y relaciones con `Area`. Si se elimina o cambia un campo sin migrar, el ORM y el esquema de la base de datos dejarían de coincidir.

### 3. ¿Para qué sirven las migraciones?
> **Respuesta:** Son versiones de cambios del esquema derivados de los modelos. `makemigrations` genera los archivos de cambio y `migrate` los aplica a la base de datos. Sin aplicarlas, las tablas o columnas requeridas pueden no existir.

### 4. ¿Qué trabajo hace un serializador?
> **Respuesta:** Convierte instancias del modelo a datos JSON y valida los datos JSON que llegan a la API. `CursoSerializer`, por ejemplo, expone datos del curso y valida fechas y cupos. Sin él, cada endpoint tendría que implementar manualmente conversión y validación.

### 5. ¿Qué representa un endpoint y qué significa GET, POST, PATCH y DELETE?
> **Respuesta:** Un endpoint es una URL de la API asociada a una operación. GET consulta, POST crea o inicia una operación, PATCH actualiza parcialmente y DELETE elimina. Usar el método correcto hace explícita la intención y permite aplicar validaciones y permisos adecuados.

### 6. ¿Por qué se usa JWT y qué contiene el token?
> **Respuesta:** JWT permite que el cliente presente una credencial firmada en solicitudes posteriores, normalmente como `Authorization: Bearer <token>`. Este proyecto incluye claims como el rol y el nombre de usuario. La firma permite verificar que el contenido no se alteró; el payload no debe tratarse como secreto.

### 7. ¿Por qué el registro público no permite crear coordinadores?
> **Respuesta:** El servidor fuerza el rol de estudiante al procesar el registro público. No confía en el rol que envíe el navegador, porque un cliente podría intentar elevar sus privilegios. Si se quitara esa regla, un visitante podría registrarse como coordinador.

### 8. ¿Por qué el carro se guarda en la base de datos?
> **Respuesta:** El carro persistente se relaciona uno a uno con el usuario y sus ítems se guardan como filas. Así permanece después de cerrar sesión y se recupera desde otro dispositivo. Si se guardara solo en memoria o en una sesión local, se podría perder al cambiar de navegador o expirar la sesión.

### 9. ¿Cuándo se descuenta un cupo y por qué?
> **Respuesta:** Al confirmar la matrícula, no al agregar el curso al carro. El carro expresa intención de compra; descontar antes permitiría retener cupos sin completar la operación. Si se eliminara el descuento del checkout, se podrían confirmar más matrículas que vacantes.

### 10. ¿Qué aportan `transaction.atomic()` y `select_for_update()`?
> **Respuesta:** `transaction.atomic()` hace que las escrituras relacionadas se confirmen juntas o se reviertan juntas. `select_for_update()` bloquea temporalmente las filas de cursos mientras se revisan y descuentan los cupos, para evitar que dos compras consuman el último cupo simultáneamente en PostgreSQL. Sin la transacción podrían quedar datos parciales; sin bloqueo de fila, podrían producirse sobreventas concurrentes.

### 11. ¿Qué hace el sistema al cancelar una matrícula pagada?
> **Respuesta:** Un coordinador puede cambiar su estado. Si se cancela una matrícula que estaba pagada o completada, el backend devuelve los cupos de cada curso dentro de una transacción. Sin esa reposición, la disponibilidad quedaría artificialmente reducida.

### 12. ¿Qué diferencia hay entre `CASCADE` y `PROTECT`?
> **Respuesta:** `CASCADE` elimina los registros dependientes cuando se borra el objeto relacionado; se usa, por ejemplo, para limpiar ítems del carro al borrar el carro. `PROTECT` impide borrar un curso que ya aparece en una inscripción histórica, para no perder la integridad del historial.

### 13. ¿Para qué sirven los filtros y cómo se usan?
> **Respuesta:** `django-filter` traduce parámetros de URL como `?precio_max=50000` o `?con_cupo=true` a condiciones de consulta en el ORM. Sin el FilterSet o el backend configurado, los parámetros no filtrarían el catálogo.

### 14. ¿Qué es un context processor?
> **Respuesta:** Es una función que añade datos al contexto de las plantillas. `student_footer_context` permite que el footer use nombre, sección y año sin repetir esos valores en cada vista. Si no se registra en `settings.py`, esas variables no estarán disponibles automáticamente.

### 15. ¿Cómo explicarías la estructura del proyecto de principio a fin?
> **Respuesta:** `academic_project/settings.py` configura Django y las dependencias; las URLs enlazan rutas con vistas; `academic/models.py` define datos y relaciones; `serializers.py` valida y representa JSON; `views.py` implementa las operaciones; `permissions.py` controla roles; `filters.py` busca y filtra; las plantillas muestran la interfaz; y las pruebas verifican que los flujos funcionen.

### Pregunta sorpresa: ¿Por qué hay un archivo llamado `serializer.py` además de `serializers.py`?
> **Respuesta:** `academic/serializers.py` contiene los serializadores de la aplicación EdTech descrita en esta defensa. `academic/serializer.py` parece un archivo legado de otro ejercicio con modelos `Teacher`, `Course` y `Student`; no forma parte del flujo principal actual y no debe confundirse con el módulo plural importado por las vistas.

### Repaso de 60 segundos
> “Es una API Django REST para cursos y matrículas. Los modelos definen usuarios con roles, áreas, cursos, carros y órdenes. JWT autentica; permisos RBAC autorizan. El catálogo es público para lectura y la gestión se reserva al coordinador. El estudiante conserva un carro persistente. En el checkout se valida y bloquea el stock dentro de una transacción, se crea la matrícula y se emiten tickets UUID. Al cancelar una matrícula pagada se devuelven cupos. Los filtros facilitan búsquedas y Swagger documenta la API.”

---

## 🗺️ Mapa para estudiar el repositorio completo

Sigue una solicitud en este orden para ubicar rápidamente qué hace cada archivo:

1. **`academic_project/settings.py`:** configura aplicaciones instaladas, middleware, plantillas, base de datos, JWT, zona horaria y datos del pie de página. Si se quita una aplicación requerida, Django no carga esa funcionalidad; si la base de datos está mal configurada, no se pueden leer ni guardar matrículas.
2. **`academic_project/urls.py` y `academic/urls.py`:** conectan las rutas web y API con las vistas. Si se quita una ruta, esa URL deja de estar disponible aunque la vista siga existiendo.
3. **`academic/models.py`:** define usuarios, áreas, cursos, carros, matrículas y detalles/tickets, con sus campos y relaciones. Si falta un campo o una relación, se pierde esa información o integridad en la base de datos.
4. **`academic/serializers.py`:** transforma modelos a JSON y valida los datos que llegan por la API. Si se quitan validaciones, podrían guardarse fechas o cupos incorrectos.
5. **`academic/views.py`:** ejecuta los casos de uso: consultar catálogo, gestionar carro, confirmar matrícula, ver historial y cambiar estados. Si una vista no está conectada desde URLs, el cliente no puede invocarla.
6. **`academic/permissions.py`:** separa lo que puede hacer un estudiante, un coordinador o un visitante. Si se quita el permiso de una vista, se pierde esa barrera de acceso.
7. **`academic/filters.py`:** convierte parámetros como precio o modalidad en filtros de consulta. Si se quita un filtro, ese criterio deja de servir en el catálogo.
8. **`academic/context_processors.py`:** comparte los datos del alumno con las plantillas. Si no se registra en `settings.py`, las variables correspondientes no aparecen automáticamente.
9. **`templates/academic/`:** presenta la interfaz HTML; `base.html` comparte estructura, navegación y footer y las demás plantillas muestran catálogo, login, registro, carro e historial. Si una página no extiende la plantilla base, no hereda ese marco compartido.
10. **`academic/tests.py`:** prueba de manera automatizada permisos, JWT, carro, stock y matrículas. Si se quitan pruebas, la aplicación puede seguir ejecutándose, pero se pierde una comprobación repetible de esos comportamientos.
11. **`academic/management/commands/poblar_datos.py`:** crea datos de demostración con un comando de Django. Si no se ejecuta, no se cargan automáticamente sus ejemplos.
12. **`academic/migrations/`:** conserva los cambios versionados del esquema. Si no se ejecutan con `migrate`, la base de datos puede no tener las tablas que esperan los modelos.
13. **`academic_project/asgi.py` y `wsgi.py`:** exponen la aplicación para servidores ASGI y WSGI. Si se eliminan, los servidores que buscan esos puntos de entrada no podrán iniciar Django.
14. **`init_db.sql`:** ayuda a crear la base PostgreSQL antes de correr migraciones. Si se omite, hay que crear la base de otra forma antes de que Django pueda conectarse.
15. **`requirements.txt`:** declara librerías externas necesarias. Si falta una dependencia, los imports de esa librería fallan al iniciar Django.
16. **`data/academic_mock.json`:** contiene datos de ejemplo estructurados como JSON. JSON estricto no permite comentarios; por eso se explica aquí y no se insertan comentarios dentro del archivo, ya que dejaría de poder parsearse.
17. **`academic/serializer.py`:** contiene serializadores de entidades Teacher/Course/Student de otro modelo, distintos a los de la aplicación actual; antes de borrarlo conviene confirmar que ningún consumidor externo lo necesite.

### Aclaración sobre “comentar cada línea”
> Los comentarios explicativos se colocan junto a instrucciones o elementos funcionales, procurando que cada explicación abarque la instrucción completa. No se insertan comentarios en líneas en blanco ni dentro de una lista de argumentos, una etiqueta HTML abierta o un JSON estricto cuando eso impediría interpretar el archivo. En esos casos la explicación se pone junto al bloque o en esta guía. La intención es que el proyecto continúe ejecutándose, no simular comentarios literales a costa de romper la sintaxis.

### Preguntas adicionales para practicar

#### 16. ¿Qué pasa desde que escribo una URL de la API hasta que recibo JSON?
> **Respuesta:** Django compara la URL con `urlpatterns`. La ruta seleccionada llama a una vista; DRF autentica y revisa permisos; la vista consulta o modifica modelos usando el ORM; el serializador convierte o valida los datos; y `Response` devuelve el JSON con un código HTTP. Si se elimina un eslabón, no se puede completar el recorrido.

#### 17. ¿Qué diferencia hay entre PostgreSQL y SQLite en este proyecto?
> **Respuesta:** PostgreSQL es la base prevista para el entorno normal y permite bloqueos de filas con `select_for_update()` para coordinar compras simultáneas. SQLite se usa como alternativa local/pruebas según la configuración. Si la conexión PostgreSQL no está disponible, el código puede usar SQLite en los escenarios configurados, pero no debo afirmar que ese fallback reemplaza las propiedades de concurrencia de PostgreSQL.

#### 18. ¿Qué es el ORM y por qué se usa?
> **Respuesta:** El ORM permite consultar y modificar tablas usando modelos Python, por ejemplo `Curso.objects.filter(...)`, sin escribir SQL manual para cada operación. Ayuda a mantener consultas vinculadas al modelo. Si se evita o configura mal, las consultas pueden fallar o dejar de corresponder a las tablas.

#### 19. ¿Qué significa `related_name` en una relación Django?
> **Respuesta:** Define el nombre de acceso inverso desde el objeto relacionado. Por ejemplo, `area.cursos` permite recorrer los cursos de un área. Si se quita o cambia, ese acceso inverso y las consultas que lo usan tendrían que actualizarse.

#### 20. ¿Por qué `Decimal` para precios y no `float`?
> **Respuesta:** `Decimal` representa cantidades decimales monetarias con precisión fija; los `float` pueden acumular errores binarios de redondeo. Si se usara `float`, el total podría no coincidir exactamente con los precios guardados.

#### 21. ¿Qué es un UUID y qué identificadores usan las matrículas?
> **Respuesta:** Es un identificador único de 128 bits. El sistema asigna uno a la transacción y otro a cada ticket para poder identificarlos de forma única. Si se quitaran esos campos, no se dispondría de esos códigos únicos del negocio.

#### 22. ¿Qué significa que un endpoint sea de solo lectura?
> **Respuesta:** Permite consultar recursos, pero no crear, modificar ni borrar. `MatriculaViewSet` usa `ReadOnlyModelViewSet` para que coordinación consulte órdenes; el cambio de estado se ofrece aparte mediante un endpoint PATCH con permiso específico.

#### 23. ¿Qué validaciones hace el serializador de curso?
> **Respuesta:** Revisa que la fecha de inicio no sea posterior a la fecha de término y que los cupos disponibles no superen los cupos totales. Si se quitan esas comprobaciones, la API podría guardar programas con cronología o inventario incoherentes.

#### 24. ¿Qué diferencia hay entre una plantilla y una vista?
> **Respuesta:** La vista decide qué datos obtener y qué respuesta devolver; la plantilla define cómo se presenta el HTML al usuario. Si se elimina la plantilla, esa vista no podrá renderizar esa página; si se elimina la vista/ruta, el HTML no se servirá.

#### 25. ¿Cómo probarías que el último cupo no se vende dos veces?
> **Respuesta:** Revisaría el test de checkout sin cupos y haría una prueba de concurrencia con PostgreSQL: dos transacciones intentan comprar el último cupo y solo una debe confirmarlo. `select_for_update()` es parte de la protección. Una prueba secuencial valida el caso funcional, pero no demuestra por sí sola toda la concurrencia real.

#### 26. ¿Qué es Swagger y por qué ayuda?
> **Respuesta:** Es una interfaz para explorar el esquema OpenAPI, leer endpoints y probar solicitudes. Ayuda a entender cómo consumir la API sin revisar toda la implementación. Si se quita, la API todavía podría funcionar, pero se pierde esa documentación interactiva.

#### 27. ¿Cómo carga datos de demostración el proyecto?
> **Respuesta:** Con el comando personalizado `py manage.py poblar_datos`, que usa `get_or_create` para crear o reutilizar usuarios, áreas y cursos. Si se quita ese comando, hay que crear los datos manualmente o usar otro método.

#### 28. ¿Qué diferencia hay entre un código HTTP 400, 401 y 403?
> **Respuesta:** 400 indica que la solicitud es inválida para la operación; 401 que falta autenticación válida; 403 que el usuario identificado no tiene permiso. Si se confunden, la API comunicaría mal si debe corregirse el contenido, iniciar sesión o cambiar de rol.

#### 29. ¿El sistema procesa un pago bancario real?
> **Respuesta:** No. El checkout implementa la lógica académica de confirmar, registrar estado, descontar cupos y emitir tickets, pero no contacta una pasarela financiera. Para producción habría que integrar un proveedor, validar sus notificaciones y actualizar el estado solo tras una confirmación verificada.

#### 30. Si una matrícula tiene varios cursos, ¿por qué guardar detalles separados?
> **Respuesta:** `Matricula` representa la orden completa y `DetalleMatricula` representa cada curso incluido, con su precio histórico y ticket individual. Así se conserva qué se compró y cuánto costaba en ese momento. Sin detalles, solo se tendría el total y no el desglose por curso.

### Plantilla para responder cualquier pregunta técnica
> “Esto sirve para **[propósito]**. Está implementado en **[archivo/clase/método]**. Funciona así: **[paso o ejemplo concreto]**. Si se quitara, **[consecuencia verificable]**. Lo puedo comprobar con **[prueba, endpoint o comando]**.”
