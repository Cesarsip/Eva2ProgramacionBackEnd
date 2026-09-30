# Entregable de Inteligencia Artificial (prompts.md)
## Evaluación N°2: Desarrollo Backend con Django & PostgreSQL
**Asignatura:** Desarrollo Backend &middot; **Docente:** Marcelo Alvarado &middot; **Carrera:** Informática y Ciberseguridad
**Estudiante:** CESAR ANTONIO AEDO ALVAREZ &middot; **Sección:** IEC-N4-C2 &middot; **Año:** 2026

Este documento registra la interacción con la herramienta de Inteligencia Artificial (Gemini / Antigravity) de acuerdo con los criterios de evaluación y auditoría académica.

---

### Prompt: Implementación y Adaptación de la Interfaz Web Completa (EdTech)

**Prompt enviado:**
> "Actúa como un desarrollador Frontend y Backend senior experto en Python, Django y Django REST Framework (DRF).
>
> Necesito implementar y adaptar la interfaz web completa para el 'Proyecto 2: Plataforma de Reservas de Cursos y Bootcamps (EdTech)', asegurando que los templates HTML y las rutas cumplan estrictamente con las reglas de negocio y los requisitos técnicos de evaluación descritos a continuación.
>
> 1. REGLAS DE NEGOCIO DEL PROYECTO (EDTECH)
> - Roles: Estudiante y Coordinador Académico.
> - Coordinador Académico: Gestiona Áreas de Conocimiento y Cursos/Bootcamps (título, descripción, costo de matrícula, fechas de inicio/término, cupos máximos y disponibles).
> - Estudiante: Navega la oferta académica, agrega cursos a su Carro de Matrícula persistente en PostgreSQL (no permite duplicados) y realiza el checkout.
> - Control Transaccional de Cupos: La validación y descuento de cupos se realiza ÚNICAMENTE al confirmar la matrícula (estado PAGADO). Si una matrícula se actualiza a CANCELADO, el cupo se repone automáticamente al catálogo.
>
> 2. DISEÑO VISUAL Y PALETA DE COLORES (PROFESIONAL)
> - Paleta Dominante:
>   * Azul Marino / Azul Oscuro (#0f172a / #1e293b): Para la barra de navegación (navbar), cabeceras de tarjetas (login, registro) y elementos de marca.
>   * Verde Esmeralda / Corporativo (#10b981 / #059669): Para todos los botones de acción principal ('Filtrar', 'Ingresar', 'Crear cuenta', 'Agregar al carro', 'Confirmar matrícula'). NO utilizar tonos naranja o dorado.
> - Estilo: Tarjetas blancas con sombras ligeras (shadow-sm), bordes redondeados y un fondo general gris muy claro (#f8fafc) para mantener un diseño limpio y moderno.
>
> 3. ESPECIFICACIÓN DE VISTAS Y COMPONENTES
> - Catálogo y Filtros (index.html):
>   Panel superior con formulario de búsqueda por texto, filtro por Área/Categoría, rango de precios (mín/máx), disponibilidad de cupos y ordenamiento. Botones de acción 'Filtrar' (verde) y 'Limpiar' (secundario).
> - Formulario de Login (login.html):
>   Tarjeta centrada con cabecera en azul oscuro, campos limpios para usuario/correo, contraseña con botón interactivo (icono de ojo) para alternar visibilidad y enlace a registro.
> - Formulario de Registro (registro.html):
>   Formulario estructurado con datos personales (nombre, apellido, correo, usuario, teléfono, contraseña, confirmación) y un selector desplegable de Rol de usuario (Estudiante vs Coordinador Académico).
> - Footer Institucional Obligatorio (en base.html):
>   Pie de página fijo con estilo oscuro que muestre exactamente los siguientes datos:
>   * Estudiante: CESAR ANTONIO AEDO ALVAREZ
>   * Sección: IEC-N4-C2
>
> 4. ENRUTAMIENTO, SIN ADMIN Y REDIRECCIÓN CATCH-ALL (urls.py)
> - Sin interfaz de administración (NO incluir 'admin/'). Si se intenta ingresar a `/admin` o cualquier ruta no definida, el sistema debe redirigir automáticamente a la portada principal sin mostrar pantallas de error 404 de Django.
> - Implementar la expresión regular catch-all al final del urlpatterns:
>   re_path(r'^.*$', redirect_to_home)
>
> 5. ENTREGABLES REQUERIDOS
> Genera el código completo archivo por archivo con COMENTARIOS EN BLOQUE EXPLICATIVOS detallando la función de cada sección:
> 1. base.html (Plantilla base con CSS en bloque, Bootstrap 5, iconos y footer)
> 2. index.html (Catálogo de la oferta académica con panel de filtros)
> 3. login.html (Interfaz de autenticación con toggle de contraseña)
> 4. registro.html (Registro de usuario con selector de roles)
> 5. urls.py (Configuración de rutas web, endpoints REST API y redirección re_path sin admin)
> 6. Registro de Prompts (Bloque Markdown listo para copiar en prompts.md con el prompt enviado y el resumen de la solución)"

---

### Resumen de la Solución Técnica Implementada

1. **Arquitectura Visual y Paleta:**
   - **Navbar y Cabeceras:** Azul marino oscuro `#0f172a` (Slate 900) y `#1e293b` (Slate 800) proporcionando contraste institucional y elegancia.
   - **Botones de Acción:** Verde Esmeralda `#10b981` y `#059669` en todos los componentes interactivos principales.
   - **Estructura:** Fondo gris claro `#f8fafc` con tarjetas blancas `#ffffff` de bordes redondeados y sombras suaves `shadow-sm`.

2. **Panel de Filtros y Catálogo (`index.html`):**
   - Panel superior integrado con búsqueda por coincidencia parcial (`icontains`), desplegable dinámico de Áreas/Categorías, filtros numéricos de precio mínimo y máximo, selector de disponibilidad de cupos y ordenamiento.
   - Consumo asíncrono con JavaScript Fetch contra `/api/cursos/` respetando los filtros de `django-filter`.

3. **Autenticación con Interfaz Limpia (`login.html`):**
   - Tarjeta centrada con cabecera azul marino `#0f172a`, campos limpios, botón de ojo interactivo que alterna `type="password"` y `type="text"`, botón de acceso verde `#10b981` y enlaces de navegación fluidos.

4. **Registro con Asignación de Roles (`registro.html`):**
   - Formulario estructurado para recolección de datos personales y credenciales con validación mínima de 8 caracteres.
   - Selector desplegable de Roles (Estudiante vs Coordinador Académico) con texto contextual explicativo. Endpoint backend `POST /api/registro/` que encripta la contraseña con `set_password` e inicializa automáticamente el carro persistente.

5. **Footer Institucional Obligatorio (`base.html`):**
   - Barra inferior fija en tono oscuro `#0f172a` con los datos institucionales:
     - **Estudiante: CESAR ANTONIO AEDO ALVAREZ**
     - **Sección: IEC-N4-C2**

---

### Prompt 2: Seguridad, Eliminación de Accesos Inseguros, Carro Anónimo y Cumplimiento 100% Rúbrica EVA-2

**Prompt enviado:**
> "Actúa como un desarrollador Backend y Frontend Senior experto en Django REST Framework (DRF) y PostgreSQL.
> 
> Necesito que revises y ajustes la implementación del 'Proyecto 2: Plataforma de Reservas de Cursos y Bootcamps (EdTech)' para que cumpla rigurosamente al 100% con la Rúbrica de Evaluación EVA-2.
> 
> 1. SEGURIDAD Y LIMPIEZA DE INTERFAZ (ELIMINAR ACCESOS INSEGUROS)
> - Elimina completamente cualquier botón o sección de 'Acceso Rápido para Defensa' o inicio de sesión automático sin contraseña en el template login.html.
> - Todo inicio de sesión DEBE ser real, seguro y validado por DRF mediante autenticación JWT (POST /api/token/), retornando tokens de acceso y refresh con claims de rol personalizados ('Estudiante' o 'Coordinador Académico').
> 
> 2. LÓGICA DE CARRO PERSISTENTE (ANÓNIMO + AUTENTICADO)
> - Usuario Anónimo (Sin Inicio de Sesión):
>   Permite al visitante agregar cursos a su carro de matrícula guardando temporalmente los datos en el navegador (usando JavaScript y localStorage). El usuario debe poder ver sus productos agregados en la interfaz sin necesidad de estar logueado.
> - Usuario Autenticado (Con Cuenta):
>   Al momento de Iniciar Sesión o Registrarse, realiza un merge/sincronización automática de los ítems del localStorage hacia la base de datos PostgreSQL mediante el endpoint (POST /api/carro-matricula/). 
> - Cumplimiento de Rúbrica:
>   El backend DEBE mantener la relación 1 a 1 entre el Usuario y su CarroMatricula en PostgreSQL. Una vez autenticado, sus productos deben persistir en la base de datos aun tras un logout o cambio de dispositivo.
> 
> 3. CUMPLIMIENTO RIGUROSO DE LA MATRIZ DE PERMISOS EVA-2
> Aplica las siguientes restricciones en DRF usando permission_classes:
> - PÚBLICO (AllowAny): GET /api/cursos/, GET /api/areas/
> - ESTUDIANTE (IsAuthenticated): GET/POST/DELETE /api/carro-matricula/, POST /api/matriculas/confirmar/, GET /api/mis-matriculas/
> - COORDINADOR (IsAdminUser / EsCoordinador): POST/PUT/DELETE /api/cursos/, PATCH /api/matriculas/{id}/estado/
> 
> 4. CONTROL TRANSACCIONAL DE CUPOS
> - El descuento de cupos NO se realiza al agregar al carro.
> - En el endpoint de checkout (POST /api/matriculas/confirmar/), dentro de un bloque @transaction.atomic:
>   1. Valida que cada curso del carro tenga al menos 1 cupo disponible. Si no hay stock, la transacción se RECHAZA.
>   2. Al pasar la orden a estado PAGADO, descuenta 1 cupo por cada curso y liquida el carro en PostgreSQL.
> - Si una matrícula en estado PAGADO es modificada por un Coordinador a CANCELADO, el cupo debe reponerse automáticamente al catálogo.
> 
> 5. REQUERIMIENTOS DE ENTREGA Y REDIRECCIÓN
> - Pie de página (Footer) obligatorio en base.html:
>   * Estudiante: CESAR ANTONIO AEDO ALVAREZ
>   * Sección: IEC-N4-C2
> - En urls.py: No incluir la interfaz admin de Django. Agrega al final la redirección catch-all re_path(r'^.*$', redirect_to_home) para que cualquier ruta inexistente o no autorizada lleve a la portada sin mostrar errores 404.
> - Documenta todo el código con bloques explicativos claros para la defensa oral ante el docente."

---

### Resumen de la Solución Técnica Implementada (Ajustes de Seguridad y Carro)

1. **Eliminación de Accesos Inseguros en `login.html`:**
   - Se removió por completo el bloque visual `ACCESO RÁPIDO PARA DEFENSA:` junto con los botones de un clic y la función JavaScript `rellenarDemo`.
   - Se garantizó que todo inicio de sesión se realice a través de credenciales reales ingresadas en el formulario, procesadas por `POST /api/token/` con emisión de tokens JWT seguros.
   - En `CustomTokenObtainPairSerializer`, se enriquecieron los claims del payload del token y la respuesta JSON con `rol` ('ESTUDIANTE' / 'COORDINADOR') y `rol_display` ('Estudiante' / 'Coordinador Académico').

2. **Carro Híbrido: Persistencia Anónima (`localStorage`) y en Base de Datos (`PostgreSQL`):**
   - **Visitante Anónimo:** El usuario no autenticado puede agregar programas académicos al carro directamente desde el catálogo. Los ítems se almacenan en `localStorage` mediante `CartStorage`. El contador de la barra de navegación se actualiza dinámicamente y la vista `/carro/` permite revisar los ítems seleccionados, calcular subtotales y eliminar cursos sin estar logueado.
   - **Merge / Sincronización Automática:** Al iniciar sesión (`login.html`) o registrarse (`registro.html`), el sistema invoca la función asíncrona `sincronizarCarroAnonimo(token)` que envía por lotes los IDs (`cursos_ids`) al endpoint `POST /api/carro-matricula/`.
   - **Persistencia PostgreSQL (1 a 1):** El backend vincula cada `ItemCarroMatricula` con el `CarroMatricula` único del usuario en PostgreSQL. Los cursos persisten tras cerrar sesión (`logout`) y cambio de dispositivo.

3. **Matriz de Permisos RBAC en DRF:**
   - **Público (AllowAny):** `GET /api/cursos/` y `GET /api/areas/` mediante `IsCoordinadorOrReadOnly`.
   - **Estudiante (IsAuthenticated + IsEstudiante):** `GET/POST/DELETE /api/carro-matricula/`, `POST /api/matriculas/confirmar/`, `GET /api/mis-matriculas/`.
   - **Coordinador (IsAuthenticated + IsCoordinador):** `POST/PUT/DELETE /api/cursos/`, `PATCH /api/matriculas/<pk>/estado/`, `GET /api/matriculas/`.

4. **Control Transaccional de Cupos y Stock:**
   - El descuento de cupos **no** se ejecuta al agregar al carro.
   - En `POST /api/matriculas/confirmar/`, dentro de `transaction.atomic()` con bloqueo de concurrencia `select_for_update()`, se valida que cada curso tenga `cupos_disponibles >= 1`. Si no hay cupos, la transacción se aborta con error HTTP 400.
   - Al confirmarse el pago (`PAGADO`), se descuenta 1 cupo por cada curso en el catálogo, se generan registros históricos de `Matricula` y `DetalleMatricula` con tickets UUID, y se vacía el carro persistente.
   - En `PATCH /api/matriculas/<pk>/estado/`, si una matrícula en estado `PAGADO` es transicionada a `CANCELADO` por un Coordinador, los cupos se reponen automáticamente al catálogo.

5. **Suite de Pruebas Automatizadas:**
   - Se ejecutaron 13 pruebas unitarias con `py manage.py test`, certificando un 100% de éxito (**OK**).


---

## Prompt 3

### Prompt Enviado

```
Actúa como un desarrollador Backend y Frontend Senior experto en Django REST Framework (DRF) y PostgreSQL.

Ajusta la implementación del "Proyecto 2: Plataforma de Reservas de Cursos y Bootcamps (EdTech)" para que cumpla
estrictamente con la Rúbrica EVA-2, asegurando el flujo de registro de Estudiantes y la seguridad del sistema.

=== 1. FLUJO DE REGISTRO Y ROLES (PÚBLICO Y ADMINISTRATIVO) ===
- Registro Público de Estudiantes (registro.html):
  MANTENER el formulario de registro en la página web pública. Todo usuario que cree su cuenta desde la web se
  registrará AUTOMÁTICAMENTE con el rol "Estudiante".
- Eliminación de Selección de Rol en Web:
  Elimina el menú desplegable que permitía elegir el rol de Coordinador en la web pública.
- Cuentas de Coordinador:
  Los usuarios con rol Coordinador Académico (is_staff=True) se crearán exclusivamente por consola/backend.
- Sección en README.md:
  Crea una sección de "Credenciales de Prueba para Evaluación" detallando usuario y contraseña para ingresar como
  "Estudiante" y como "Coordinador Académico".

=== 2. PROMPTS.MD ===
Genera obligatoriamente una sección final en formato Markdown lista para copiar en el archivo prompts.md,
detallando el prompt enviado y el resumen técnico de la solución generada.
```

### Resumen Técnico de la Solución Implementada

#### Archivos Modificados

| Archivo | Cambio | Justificación |
|---------|--------|---------------|
| `templates/academic/registro.html` | Eliminado `<select id="reg-rol">` (opciones ESTUDIANTE / COORDINADOR), eliminada función JS `actualizarDescripcionRol()`, eliminado campo `rol` del payload enviado al backend. Añadido badge informativo verde sobre el rol automático. | Previene que usuarios malintencionados se auto-asignen el rol COORDINADOR desde la interfaz pública. |
| `academic/views.py` — `RegistroAPIView.post` | Añadida copia mutable de `request.data` con `data['rol'] = 'ESTUDIANTE'` antes de pasar al serializador, junto con bloque de comentario de seguridad. | Garantiza a nivel de backend que ningún valor externo (ni siquiera una llamada directa a la API con `curl`) pueda crear un Coordinador a través del endpoint `/api/registro/`. |
| `README.md` | Eliminada línea del Panel Django Admin (`/admin/`). Añadida sección `## 🔑 Credenciales de Prueba para Evaluación` con tabla de tres filas: Coordinador, Estudiante 1 y Estudiante 2. Añadida nota sobre cómo crear coordinadores adicionales. | Cumple requerimiento explícito de la rúbrica EVA-2 de documentar credenciales para el proceso de evaluación. |

#### Detalles de Seguridad Implementados

1. **Eliminación del selector de rol en la web pública (`registro.html`):**
   - Se reemplazó el `<select id="reg-rol">` por un badge informativo estático que indica que el registro es
     exclusivamente para Estudiantes.
   - El payload JavaScript ya no incluye el campo `rol`, eliminando la posibilidad de manipular el formulario
     desde las DevTools del navegador.

2. **Forzado de rol en el backend (`RegistroAPIView`):**
   - Se usa `request.data.copy()` (necesario ya que `QueryDict` es inmutable) y se sobreescribe `data['rol']`
     con `'ESTUDIANTE'` antes de crear el serializador.
   - Esto actúa como capa de seguridad doble: aunque un atacante envíe `rol=COORDINADOR` directamente a
     `POST /api/registro/` mediante cURL o Postman, el servidor lo ignorará y creará un Estudiante.
   - El endpoint `/api/registro/` usa `permissions.AllowAny` (público) pero protege el rol mediante esta lógica.

3. **Coordinadores solo por consola:**
   - El comando `py manage.py poblar_datos` crea `coordinador/admin123` con `is_staff=True` y `rol=COORDINADOR`.
   - Alternativa: `py manage.py createsuperuser`.
   - Documentado explícitamente en el README con advertencia de seguridad.

4. **Resultados de pruebas automatizadas:**
   - Se ejecutaron **13 pruebas** con `py manage.py test`.
   - Resultado: **13/13 OK** — ninguna prueba falló tras los cambios implementados.
   - `test_registro_usuario_con_rol` valida que el rol asignado sea el correcto en el flujo de registro.

---

### Prompt: Validación de cursos duplicados y transiciones transaccionales de matrículas

**Prompt enviado:**
> "Actúa como desarrollador Backend y Frontend Senior en Django REST Framework y PostgreSQL. Corrige la validación de cursos repetidos para que un estudiante no pueda agregar al carro ni comprar nuevamente un curso que ya tiene en una matrícula PAGADO o COMPLETADO. La regla debe validarse al añadir al carro y volver a validarse en el checkout, respondiendo HTTP 400 con un mensaje comprensible. Revisa además el modal y el endpoint PATCH /api/matriculas/{id}/estado/ para que coordinación pueda seleccionar PENDIENTE, PAGADO, COMPLETADO y CANCELADO. Usa una transacción con bloqueos de filas: al activar una matrícula desde PENDIENTE/CANCELADO valida y descuenta cupos; al salir de PAGADO/COMPLETADO libera los cupos reservados una sola vez. Envía la petición con el JWT Bearer, agrega pruebas y comenta los bloques modificados."

**Cambios realizados:**
- `academic/serializers.py`: el serializador de alta al carro valida curso activo, duplicado en el carro y matrícula vigente previa.
- `academic/views.py`: el lote se valida completo antes de insertar; el checkout revalida matrículas previas mientras mantiene bloqueados los cursos. El cambio de estado coordina validación/reposición del stock dentro de `transaction.atomic()` y permite reactivar con cupos disponibles, salvo que el estudiante ya se haya matriculado en esos cursos en otra boleta.
- `templates/academic/matriculas.html`: el modal ofrece los cuatro estados y muestra errores de cupo; las peticiones continúan usando `API.fetch`, que adjunta el token JWT como Bearer.
- `academic/tests.py`: cubre cursos ya matriculados, carro obsoleto, reactivación de boleta, cupos agotados y CRUD de áreas.
- `prompts.md`: conserva la solicitud y el resumen de implementación para auditoría académica.
- Verificación: 20 pruebas aprobadas, plantillas compiladas y `makemigrations --check --dry-run` sin cambios pendientes.

---

### Prompt: Navegación y matrículas adaptadas al rol

**Prompt enviado:**
> "Actúa como desarrollador Frontend y Backend Senior en Django REST Framework. Ajusta el navbar para que el estudiante tenga Catálogo, Carro de Matrícula y Mis Matrículas, y el coordinador (rol COORDINADOR o is_staff) no vea el carro y vea Gestión de Matrículas. En esa vista el coordinador debe ver todas las matrículas y poder cambiar su estado; el estudiante solo sus propias inscripciones. Adapta base.html e index.html a los claims de rol/is_staff del JWT o a request.user.is_staff, comenta el RBAC y documenta la corrección."

**Cambios realizados:**
- `templates/academic/base.html`: centraliza la detección de coordinación con `rol`, `is_staff` e `is_superuser`; oculta el carro y cambia la etiqueta del enlace al panel global para coordinación. Los estudiantes conservan el acceso a su carro e historial.
- `templates/academic/index.html`: mantiene público el catálogo, pero deshabilita la acción de agregar al carro para coordinación y conserva la operación para estudiantes/visitantes.
- `templates/academic/matriculas.html`: muestra el panel administrativo, el endpoint global y el botón de cambio de estado para coordinación; estudiantes consultan el endpoint filtrado por su usuario.
- `academic/tests.py`: verifica que `is_staff=True` autorice el listado global incluso si el rol no dice COORDINADOR, y que el endpoint del estudiante solo incluya sus matrículas.
- Los endpoints DRF siguen aplicando RBAC en backend; ocultar enlaces no sustituye la autorización del servidor.

---

### Prompt: Acceso y sincronización del carro para visitantes

**Prompt enviado:**
> "Corrige el flujo del usuario anónimo: permite que vea en la barra de navegación y en el catálogo el enlace al Carro de Matrícula con contador; en la vista del carro, muestra los cursos guardados en localStorage, subtotal y total. Ofrece iniciar sesión o registrarse para confirmar la matrícula y, después de autenticarse, sincroniza automáticamente los cursos con `POST /api/carro-matricula/`. Conserva el carro local si falla la sincronización, añade comentarios explicativos y documenta los cambios."

**Cambios realizados:**
- `templates/academic/base.html`: hace visible el enlace global del carro para visitantes y estudiantes, mantiene oculto el acceso a coordinación y actualiza el contador local o persistido. La sincronización conserva los datos locales cuando la API responde con error y reporta el fallo.
- `templates/academic/index.html`: incorpora un acceso contextual al carro con contador junto al encabezado del catálogo; la coordinación no lo ve.
- `templates/academic/carro.html`: permite al visitante consultar, eliminar o vaciar los elementos guardados en `localStorage`, muestra subtotales informativos y ofrece iniciar sesión o registrarse con retorno al carro. Al iniciar sesión, vuelve a intentar la sincronización si fuera necesario.
- `templates/academic/login.html` y `templates/academic/registro.html`: tras autenticar/registrar, respetan un destino local seguro; así el usuario vuelve al carro y el flujo existente sincroniza su selección con la API.
- El navegador solo conserva una selección temporal; la matrícula y el precio definitivos se validan en el servidor. El checkout y la reserva de cupos continúan requiriendo una cuenta de estudiante autenticada.
