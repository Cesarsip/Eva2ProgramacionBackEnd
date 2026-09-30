# Plataforma de Reservas de Cursos y Bootcamps (EdTech) &middot; EVA-2 Backend
## Asignatura: Desarrollo Backend &middot; Docente: Marcelo Alvarado &middot; INACAP
### Estudiante: CESAR ANTONIO AEDO ALVAREZ &middot; Sección: IEC-N4-C2 &middot; Año: 2026


Este repositorio contiene la solución completa e integral a la **Evaluación N°2: Desarrollo Backend con Django REST Framework & PostgreSQL** (Ponderación 25%), correspondiente al **Proyecto 2: Plataforma de Reservas de Cursos y Bootcamps (EdTech)**.

---

## 📋 Checklist de Cumplimiento Técnico (Pauta de Cotejo)

| Elemento | Requerimiento Técnico | Estado | Implementación en Código |
| :--- | :--- | :---: | :--- |
| **Base de Datos** | Conexión activa a PostgreSQL en `settings.py` | **✓ Logrado** | `django.db.backends.postgresql` nativo en `settings.py` |
| **Documentación** | Swagger / OpenAPI operativo en `/api/docs/` | **✓ Logrado** | `drf-yasg` operativo en `/api/docs/`, `/swagger/` y `/swagger.json` |
| **Comentarios** | Código documentado en bloques explícitos | **✓ Logrado** | Bloques explicativos en modelos, vistas, serializadores y filtros |
| **Datos Alumno** | Nombre, Sección y Año presentes en la vista/footer base | **✓ Logrado** | Inyectado vía Context Processor en `templates/academic/base.html` |
| **Modelos** | Atributo con `CHOICES` definido | **✓ Logrado** | `RolChoices`, `ModalidadChoices` y `EstadoMatriculaChoices` |
| **Filtros** | `django-filter` configurado en endpoints de consulta | **✓ Logrado** | `CursoFilter` con filtros por área, precio, modalidad y cupos |
| **Autenticación** | Login JWT retornando tokens y claims de rol | **✓ Logrado** | SimpleJWT con claim `rol` (`ESTUDIANTE` vs `COORDINADOR`) |
| **Carro** | Persistencia post-logout en PostgreSQL | **✓ Logrado** | Relación 1:1 en BD entre Usuario y `CarroMatricula`; no duplica |
| **Stock / Cupos**| Validación y descuento atómico al cambiar a PAGADO | **✓ Logrado** | `select_for_update()` atómico; reposición automática al CANCELAR |

---

## 🏛️ Matriz de Roles y Permisos de la API

| Rol | Método HTTP | Endpoint | Descripción de la Operación |
| :--- | :--- | :--- | :--- |
| **PÚBLICO** | `GET` | `/api/cursos/` | Consulta pública del catálogo con `django-filter` |
| **PÚBLICO** | `GET` | `/api/areas/` | Listado de áreas de conocimiento activas |
| **ESTUDIANTE**| `GET` | `/api/carro-matricula/` | Consulta del carro persistente del usuario autenticado |
| **ESTUDIANTE**| `POST` | `/api/carro-matricula/` | Agrega curso al carro (valida no duplicidad en el carro) |
| **ESTUDIANTE**| `DELETE` | `/api/carro-matricula/` | Vacía el carro o elimina un ítem específico (`?item_id=X`) |
| **ESTUDIANTE**| `POST` | `/api/matriculas/confirmar/` | Checkout: valida cupos, descuenta inventario y emite UUID |
| **ESTUDIANTE**| `GET` | `/api/mis-matriculas/` | Historial de matrículas y tickets UUID del estudiante |
| **COORDINADOR**| `POST/PUT/DELETE` | `/api/cursos/` | Creación, actualización y eliminación de cursos |
| **COORDINADOR**| `POST/PUT/DELETE` | `/api/areas/` | Administración de áreas de conocimiento |
| **COORDINADOR**| `GET` | `/api/matriculas/` | Auditoría y visualización de todas las matrículas del sistema |
| **COORDINADOR**| `PATCH` | `/api/matriculas/{id}/estado/`| Cambio de estado; **si se CANCELA, repone el stock** |

---

## 🚀 Guía de Instalación y Puesta en Marcha

### 1. Clonar el repositorio y configurar el entorno
```powershell
git clone https://github.com/Cesarsip/Eva2ProgramacionBackEnd.git
cd Eva2ProgramacionBackEnd

py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

### 2. Configurar la Base de Datos PostgreSQL
Crear la base de datos `edtech_db` en PostgreSQL (ej. mediante `psql` o pgAdmin con `init_db.sql`):
```sql
CREATE DATABASE edtech_db;
```

> **Nota para evaluación rápida o ejecución sin servidor PostgreSQL activo:**
> El proyecto cuenta con detección automática: si no se especifica PostgreSQL o se ejecutan las pruebas, opera de forma transparente con SQLite local para garantizar que el servidor y los tests funcionen inmediatamente.

### 3. Aplicar migraciones y cargar datos de prueba iniciales
```powershell
py manage.py migrate
py manage.py poblar_datos
```

El comando `poblar_datos` crea automáticamente:
- **Coordinador Académico:** `coordinador` / `admin123` (Rol: `COORDINADOR`)
- **Estudiante 1:** `estudiante1` / `estudiante123` (Rol: `ESTUDIANTE`, con curso precargado en su carro)
- **Estudiante 2:** `estudiante2` / `estudiante123` (Rol: `ESTUDIANTE`)
- 4 Áreas de conocimiento tecnológicas.
- 5 Cursos y Bootcamps con fechas, precios y cupos asignados.

### 4. Ejecutar el servidor de desarrollo
```powershell
py manage.py runserver
```

### 5. Rutas de Acceso Disponibles
- **Plataforma Web (Inicio):** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Catálogo de Cursos & Bootcamps:** [http://127.0.0.1:8000/cursos/](http://127.0.0.1:8000/cursos/)
- **Carro de Matrícula Persistente:** [http://127.0.0.1:8000/carro/](http://127.0.0.1:8000/carro/)
- **Historial de Matrículas e Inscripciones:** [http://127.0.0.1:8000/mis-matriculas/](http://127.0.0.1:8000/mis-matriculas/)
- **Documentación Swagger / OpenAPI:** [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- **Swagger UI Alternativo:** [http://127.0.0.1:8000/swagger/](http://127.0.0.1:8000/swagger/)
- **Especificación OpenAPI (JSON):** [http://127.0.0.1:8000/api/swagger.json](http://127.0.0.1:8000/api/swagger.json)

> **Nota:** El proyecto **no incluye** el panel `/admin/` de Django de forma intencional.
> Los coordinadores y datos de prueba se gestionan exclusivamente por consola (`py manage.py poblar_datos`).

---

## 🔑 Credenciales de Prueba para Evaluación

Ejecutar `py manage.py poblar_datos` antes de iniciar sesión para asegurarse de que los usuarios existen en la base de datos.

| Rol | Usuario | Contraseña | Permisos |
|-----|---------|------------|----------|
| **Coordinador Académico** | `coordinador` | `admin123` | Gestión de cursos, áreas, cambio de estado de matrículas |
| **Estudiante** | `estudiante1` | `estudiante123` | Catálogo, carro de matrícula, confirmar inscripción, historial |
| **Estudiante 2** | `estudiante2` | `estudiante123` | Catálogo, carro de matrícula, confirmar inscripción, historial |

> **Importante:** Las cuentas de Coordinador Académico (`is_staff=True`) se crean **exclusivamente desde la consola/backend**.
> El formulario de registro web (`/registro/`) asigna el rol **Estudiante** de forma automática e inamovible.
> Para crear un coordinador adicional: `py manage.py createsuperuser` o agregar el usuario al comando `poblar_datos`.

---



## 🧪 Ejecución de Pruebas Automatizadas

El proyecto incluye **11 pruebas unitarias y de integración** que cubren el 100% de los requisitos:
```powershell
py manage.py test
```

---

## 📡 Ejemplos de Consumo de la API con cURL / Postman

### 1. Obtener Token JWT con Claims de Rol (Login)
```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "estudiante1", "password": "estudiante123"}'
```

### 2. Consultar Carro Persistente (Estudiante)
```bash
curl -X GET http://127.0.0.1:8000/api/carro-matricula/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### 3. Agregar Curso al Carro (Estudiante)
```bash
curl -X POST http://127.0.0.1:8000/api/carro-matricula/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"curso_id": 1}'
```

### 4. Confirmar Matrícula (Checkout Atómico)
```bash
curl -X POST http://127.0.0.1:8000/api/matriculas/confirmar/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### 5. Cancelar Matrícula y Reponer Cupos (Coordinador)
```bash
curl -X PATCH http://127.0.0.1:8000/api/matriculas/1/estado/ \
  -H "Authorization: Bearer <ACCESS_TOKEN_COORDINADOR>" \
  -H "Content-Type: application/json" \
  -d '{"estado": "CANCELADO"}'
```

---

## 🧑‍💻 Datos del Alumno para la Evaluación
- **Nombre Completo:** CESAR ANTONIO AEDO ALVAREZ
- **Sección:** IEC-N4-C2
- **Año:** 2026
- **Asignatura:** Desarrollo Backend (EVA-2)
- **Docente:** Marcelo Alvarado
- **Guía de Defensa Oral:** Consultar el archivo [DEFENSA_EVA2.md](./DEFENSA_EVA2.md)

