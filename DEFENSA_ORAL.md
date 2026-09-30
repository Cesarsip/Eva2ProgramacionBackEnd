# Guía de defensa oral — EVA-2 EdTech

Esta guía relaciona cada criterio de la pauta con su ubicación en el proyecto, una forma sencilla de explicarlo y una formulación técnica. Las rutas de archivos son relativas a la raíz del repositorio.

## Antes de la presentación: comprobaciones que no debes omitir

1. **Confirma PostgreSQL.** En `academic_project/settings.py`, `DATABASES['default']['ENGINE']` usa PostgreSQL por defecto. Si no detecta el servicio, el proyecto muestra un aviso y utiliza SQLite para desarrollo local; las pruebas también usan SQLite salvo que se defina `FORCE_POSTGRES=1`. No afirmes que probaste con PostgreSQL hasta iniciar el servicio, configurar las credenciales, ejecutar migraciones y confirmar el motor:

   ```powershell
   py manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['ENGINE'])"
   py manage.py migrate
   py manage.py test academic
   ```

   La salida del primer comando debe ser `django.db.backends.postgresql`. Si aparece `django.db.backends.sqlite3`, esa ejecución no cuenta como evidencia de cumplimiento de la pauta. Para exigir PostgreSQL en las pruebas, establece `$env:FORCE_POSTGRES = "1"` antes de ejecutar `py manage.py test academic`.

2. **Publica la versión final.** La pauta exige publicación en GitHub antes del plazo. Los cambios locales deben formar parte de un commit publicado; verifica que el commit que presentarás aparezca en `https://github.com/Cesarsip/Eva2ProgramacionBackEnd`.

3. **Suite de pruebas.** Se corrigió la prueba de bajas lógicas para consultar la oferta pública como visitante anónimo. Las 23 pruebas pasaron con una selección explícita de SQLite en memoria; eso valida reglas generales y respuestas HTTP, pero **no demuestra** conexión ni bloqueos concurrentes en PostgreSQL. Ejecuta y conserva también la suite con PostgreSQL antes de la defensa.

4. **Seguridad, fuera del alcance de la rúbrica funcional.** La clave de firma JWT y algunas credenciales de demostración están documentadas en el repositorio. Mantén el uso limitado a la evaluación y rótalas antes de desplegar o mantener público el proyecto.

## Criterio técnico 1 — Backend y lógica de negocio (30 puntos)

### Base de datos, modelos, relaciones y `CHOICES` (6 puntos)

- **Dónde:** bloque [`DATABASES`](academic_project/settings.py#L107); clases [`Usuario`](academic/models.py#L10), [`Curso`](academic/models.py#L131), [`CarroMatricula`](academic/models.py#L238), [`ItemCarroMatricula`](academic/models.py#L290), [`Matricula`](academic/models.py#L337) y [`DetalleMatricula`](academic/models.py#L416).
- **Qué mostrar:** `DATABASES['default']['ENGINE']`; `Usuario.RolChoices`, `Curso.ModalidadChoices`, `Matricula.EstadoMatriculaChoices`; `CarroMatricula.usuario` (`OneToOneField`); las claves foráneas; `unique_together` de carro y curso.
- **Respuesta sencilla:** “PostgreSQL guarda las cuentas, cursos, carros y matrículas. Un usuario tiene un solo carro, y una matrícula agrupa los cursos comprados. Los `CHOICES` limitan los roles, modalidades y estados a valores conocidos.”
- **Respuesta técnica:** “El ORM de Django mapea modelos a tablas. `OneToOneField` establece unicidad del carro por propietario; `ForeignKey` modela relaciones uno-a-muchos; `TextChoices` define enumeraciones persistidas con validación y etiquetas; la restricción de unicidad evita duplicar un curso en el mismo carro.”

### JWT y permisos según el rol (8 puntos)

- **Dónde:** [`CustomTokenObtainPairSerializer`](academic/serializers.py#L14); permisos [`IsEstudiante`](academic/permissions.py#L8), [`IsCoordinador`](academic/permissions.py#L30), [`IsCoordinadorOrReadOnly`](academic/permissions.py#L54); `permission_classes` en las vistas de [`academic/views.py`](academic/views.py#L289).
- **Qué mostrar:** `POST /api/token/` devuelve access, refresh y datos del usuario. El método `get_token` añade claims como `rol`; las clases de permiso verifican autenticación/rol en el servidor.
- **Respuesta sencilla:** “Al iniciar sesión recibo tokens. En cada operación protegida, la API valida el token y comprueba si el rol puede realizar esa acción. El menú de la web solo ayuda a navegar; no concede permisos.”
- **Respuesta técnica:** “SimpleJWT autentica el Bearer access token. Los claims personalizados incluyen el rol, mientras que las clases de permisos DRF autorizan cada request. El registro público fuerza el rol estudiante en el backend para evitar escalada de privilegios.”
- **Matriz rápida:** público puede consultar cursos y áreas; estudiantes administran su carro, checkout e historial propio; coordinación administra cursos/áreas y consulta/cambia matrículas.

### Carro persistente (8 puntos)

- **Dónde:** [`CarroMatricula`](academic/models.py#L238), [`ItemCarroMatricula`](academic/models.py#L290), [`CarroMatriculaAPIView`](academic/views.py#L289), [`AgregarItemCarroSerializer`](academic/serializers.py#L244), y el almacenamiento/sincronización del invitado en [`base.html`](templates/academic/base.html#L436) y [`carro.html`](templates/academic/carro.html#L175).
- **Qué mostrar:** `OneToOneField` usuario-carro, la relación de ítems, la restricción contra duplicados y `GET/POST/DELETE /api/carro-matricula/`.
- **Respuesta sencilla:** “El carro de un estudiante registrado vive en la base de datos, no en la sesión. Cerrar sesión no borra sus cursos. Un visitante sí usa un carro temporal del navegador que se sincroniza cuando inicia sesión.”
- **Respuesta técnica:** “El carro se recupera con `get_or_create` a partir de `request.user`, y no se acepta un identificador de propietario desde el cliente. El serializador valida cursos duplicados y matrículas previas; una restricción de base de datos protege la unicidad.”

### Checkout, transacciones, estados y cupos (8 puntos)

- **Dónde:** [`ConfirmarMatriculaAPIView.post`](academic/views.py#L459), [`CambiarEstadoMatriculaAPIView.patch`](academic/views.py#L682), [`Matricula`](academic/models.py#L337) y [`DetalleMatricula`](academic/models.py#L416).
- **Qué mostrar:** `POST /api/matriculas/confirmar/`; `transaction.atomic()`; `select_for_update()`; creación de matrícula y detalles; `codigo_transaccion` y `codigo_ticket` UUID; `PATCH /api/matriculas/{id}/estado/`.
- **Respuesta sencilla:** “Agregar al carro no reserva cupos. Al confirmar, el servidor vuelve a revisar disponibilidad; si hay cupos, los descuenta y crea la matrícula y sus tickets. Si algo falla, la transacción revierte los cambios.”
- **Respuesta técnica:** “El checkout bloquea las filas de cursos y valida el inventario dentro de una transacción atómica, reduciendo carreras concurrentes. `Decimal` conserva precisión monetaria. Los UUID identifican la orden y cada inscripción. Cambiar estado repone o vuelve a reservar cupos solo al cruzar estados que representan una matrícula vigente.”
- **Importante:** “El checkout actual simula el pago; no integra una pasarela bancaria.”

## Criterio técnico 2 — Defensa individual (70 puntos)

### 1. Arquitectura, configuración DB y modelos (12 puntos)

- **Archivos:** [`settings.py`](academic_project/settings.py#L107), [`models.py`](academic/models.py#L10).
- **Demostración:** explica motor activo, modelo de usuario, catálogo, carro, matrícula y detalle; dibuja `Usuario 1—1 Carro`, `Carro 1—N Item`, `Matrícula 1—N Detalle`, `Curso 1—N Detalle`.
- **Frase técnica:** “La integridad referencial está delegada al ORM y a las restricciones relacionales de la base; las reglas de valores discretos usan `TextChoices`.”

### 2. Flujo JWT, claims y permisos RBAC (12 puntos)

- **Archivos:** [`serializers.py`](academic/serializers.py#L14), [`permissions.py`](academic/permissions.py#L8), [`views.py`](academic/views.py#L143).
- **Demostración:** inicia sesión, inspecciona `rol` en la respuesta y prueba que un estudiante recibe rechazo al intentar crear un curso.
- **Frase técnica:** “Autenticación identifica al usuario; autorización decide si ese usuario puede ejecutar la acción. DRF verifica la segunda en el servidor.”

### 3. Carro persistente (12 puntos)

- **Archivos:** [`models.py`](academic/models.py#L238), [`views.py`](academic/views.py#L289), flujo de invitado en [`base.html`](templates/academic/base.html#L436) y [`carro.html`](templates/academic/carro.html#L120).
- **Demostración:** agrega un curso autenticado, cierra sesión y vuelve a entrar; luego muestra el carro. Diferencia ese flujo del carro anónimo en `localStorage`.
- **Frase técnica:** “La persistencia de cuenta está en PostgreSQL; `localStorage` es solo una selección temporal antes de autenticarse.”

### 4. Checkout y stock (12 puntos)

- **Archivo:** [`academic/views.py`](academic/views.py#L459), `ConfirmarMatriculaAPIView` y `CambiarEstadoMatriculaAPIView`.
- **Demostración:** confirma un curso, muestra la disminución de cupos y el ticket UUID; luego cancela como coordinación y muestra la reposición.
- **Frase técnica:** “La transición de inventario se realiza una sola vez al entrar o salir de estados con cupo reservado, dentro de una transacción.”

### 5. Filtros y OpenAPI (10 puntos)

- **Archivos:** [`CursoFilter`](academic/filters.py#L9), [`CursoViewSet`](academic/views.py#L233), [`SPECTACULAR_SETTINGS`](academic_project/settings.py#L177), [`urls.py`](academic_project/urls.py#L28); UI y parámetros en [`index.html`](templates/academic/index.html#L262).
- **Demostración:** prueba `/api/cursos/?area=1&precio_max=50000`, `?con_cupo=true` y `?agotado=true`; abre `/api/docs/`.
- **Frase técnica:** “`django-filter` enlaza parámetros de query string con condiciones del ORM. `drf-spectacular` genera el esquema OpenAPI desde rutas, serializadores y anotaciones de las operaciones.”

### 6. Calidad, comentarios y footer (12 puntos)

- **Archivos:** comentarios de dominio en [`models.py`](academic/models.py#L10), [`views.py`](academic/views.py#L459), [`serializers.py`](academic/serializers.py#L14) y [`filters.py`](academic/filters.py#L9); [`student_footer_context`](academic/context_processors.py#L3); [`base.html`](templates/academic/base.html#L310).
- **Demostración:** explica que el context processor inyecta los datos al contexto global y muestra nombre, sección y año en el footer.
- **Frase técnica:** “Los comentarios documentan propósito, regla de negocio y efecto de omitir bloques importantes. El context processor evita repetir los datos en cada vista.”

## Conceptos básicos que pueden preguntarte

| Concepto | Explicación simple | Cómo decirlo técnicamente |
|---|---|---|
| API REST | Una forma acordada de pedir y enviar datos por HTTP. | Recursos expuestos mediante endpoints y métodos HTTP; las representaciones se intercambian en JSON. |
| ORM | Permite consultar y guardar datos usando objetos Python. | Django traduce operaciones de modelos a consultas SQL y gestiona relaciones/migraciones. |
| Serializador | Convierte datos a JSON y revisa lo que llega. | Convierte instancias a representaciones primitivas y valida/normaliza payloads entrantes. |
| Permiso | Decide quién puede hacer algo. | Una política de autorización DRF que permite o rechaza una request después de autenticar. |
| Transacción | Hace varios cambios como una sola operación. | `transaction.atomic()` confirma todos los cambios o revierte el conjunto si ocurre un error. |
| UUID | Código único para identificar una orden o ticket. | Identificador de 128 bits generado con `UUIDField`, protegido por una restricción única. |
| Filtro | Limita los resultados con criterios. | Parámetros de query string transformados por `django-filter` en condiciones ORM. |
| `localStorage` | Memoria persistente dentro del navegador. | Almacenamiento cliente-origen; no reemplaza la persistencia de cuenta ni es fuente confiable para precios/cupos. |

## Preguntas de cierre que conviene practicar

1. **¿Qué ocurre si dos estudiantes compran el último cupo a la vez?**  
   “El checkout bloquea las filas y vuelve a validar dentro de la transacción. Solo una operación puede consumir el último cupo; la otra se rechaza si ya no hay disponibilidad. Este bloqueo debe probarse con PostgreSQL.”

2. **¿Por qué el frontend no decide el precio final ni los cupos?**  
   “Los datos del navegador pueden alterarse. La API consulta los valores actuales del curso y valida la disponibilidad antes de crear la matrícula.”

3. **¿Por qué usar `PROTECT` para el curso de un detalle histórico?**  
   “Para impedir borrar un curso que ya forma parte de una inscripción histórica y conservar la integridad de la matrícula.”

4. **¿Qué diferencia hay entre `PUT` y `PATCH`?**  
   “`PUT` reemplaza el recurso completo; `PATCH` actualiza solo los campos enviados. El cambio de estado usa `PATCH`.”

5. **¿Cómo demuestras que el estudiante solo ve su historial?**  
   “El endpoint filtra por el usuario autenticado en el servidor; el cliente no elige el propietario de la consulta.”

6. **¿Qué pendiente reconoces con transparencia?**  
   “Debo ejecutar y mostrar la suite con PostgreSQL real, verificar que el commit final esté publicado y actualizar la documentación que todavía tenga datos históricos incorrectos.”
