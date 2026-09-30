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

6. **Enrutamiento sin Admin y Redirección Catch-All (`urls.py`):**
   - Se removió `path('admin/', admin.site.urls)` del enrutador público.
   - Se configuró la expresión regular catch-all `re_path(r'^.*$', redirect_to_home)` al final de `urlpatterns` enlazada a `academic.views.redirect_to_home`, redirigiendo cualquier ruta desconocida o `/admin` directamente a la portada principal sin emitir errores 404.
