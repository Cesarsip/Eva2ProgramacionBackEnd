from rest_framework import permissions  # Importa las clases base de permisos; sin esto no se podrían declarar permisos DRF.

# =====================================================================
# BLOQUE DE PERMISOS BASADOS EN ROLES (RBAC EN DJANGO REST FRAMEWORK)
# Cumple el Requerimiento 1: Autenticación & Autorización JWT y Roles
# =====================================================================

class IsEstudiante(permissions.BasePermission):
    """
    Permiso que autoriza únicamente a usuarios autenticados con Rol ESTUDIANTE.
    Utilizado en los endpoints:
    - GET/POST/DELETE /api/carro-matricula/
    - POST /api/matriculas/confirmar/
    - GET /api/mis-matriculas/
    
    Si se elimina o no se valida el rol, cualquier usuario o anónimo
    podría realizar operaciones exclusivas de los alumnos.
    """
    message = "Acceso denegado: Se requiere rol de Estudiante para realizar esta acción."  # Define el mensaje de rechazo; al quitarlo DRF mostraría su mensaje genérico.

    def has_permission(self, request, view):
        # Agrupa las condiciones en un booleano para permitir o rechazar la solicitud; sin este método se heredaría el permiso base.
        return bool(
            request.user and  # Comprueba que exista un usuario en la solicitud; al quitarlo se dependería de evaluar atributos de un usuario anónimo.
            request.user.is_authenticated and  # Exige inicio de sesión; al quitarlo visitantes anónimos podrían llegar a la comprobación del rol.
            request.user.rol == 'ESTUDIANTE'  # Limita el acceso al rol estudiante; al quitarlo cualquier usuario autenticado pasaría.
        )


class IsCoordinador(permissions.BasePermission):
    """
    Permiso que autoriza únicamente a usuarios autenticados con Rol COORDINADOR
    o administradores (is_staff / is_superuser).
    Utilizado en los endpoints:
    - POST/PUT/DELETE /api/cursos/
    - POST/PUT/DELETE /api/areas/
    - PATCH /api/matriculas/{id}/estado/
    - GET /api/matriculas/
    
    Si se elimina, usuarios con rol Estudiante podrían alterar cupos,
    cancelar órdenes ajenas o modificar el catálogo de cursos.
    """
    message = "Acceso denegado: Se requiere rol de Coordinador Académico para realizar esta acción."  # Explica el rechazo; al quitarlo se vería un mensaje genérico.

    def has_permission(self, request, view):
        # Devuelve True solo a coordinadores o personal administrativo; quitar el método dejaría de aplicar esta regla.
        return bool(
            request.user and  # Confirma que hay un usuario asociado; al quitarlo podría evaluarse una solicitud sin identidad.
            request.user.is_authenticated and  # Requiere autenticación; al quitarlo el control de acceso perdería una condición explícita.
            (request.user.rol == 'COORDINADOR' or request.user.is_staff or request.user.is_superuser)  # Acepta coordinador o administrador; al quitarlo estudiantes podrían gestionar datos académicos.
        )


class IsCoordinadorOrReadOnly(permissions.BasePermission):
    """
    Permiso dual para el catálogo público y gestión administrativa:
    - Métodos seguros (GET, HEAD, OPTIONS) están abiertos a TODO PÚBLICO (anónimos y clientes).
    - Métodos de escritura (POST, PUT, PATCH, DELETE) requieren Rol COORDINADOR.
    
    Aplica a:
    - /api/cursos/
    - /api/areas/
    """
    message = "Acceso denegado: La creación y modificación del catálogo requiere rol de Coordinador."  # Aclara por qué se rechaza escritura; al quitarlo DRF responde con su texto predeterminado.

    def has_permission(self, request, view):
        # Lectura pública permitida para cualquier visitante
        if request.method in permissions.SAFE_METHODS:
            return True  # Permite GET/HEAD/OPTIONS sin iniciar sesión; al quitarlo también se bloquearía la consulta pública del catálogo.
        # Escritura restringida exclusivamente a Coordinadores
        # La respuesta booleana decide si se autoriza la modificación; al quitarla el método quedaría sin decisión de acceso.
        return bool(
            request.user and  # Comprueba que la solicitud tenga usuario; al quitarlo se pierde una guarda explícita para anónimos.
            request.user.is_authenticated and  # Exige sesión/token válido; al quitarlo no se exigiría autenticación completa.
            (request.user.rol == 'COORDINADOR' or request.user.is_staff or request.user.is_superuser)  # Restringe cambios a coordinación/admin; al quitarlo un estudiante podría alterar el catálogo.
        )
