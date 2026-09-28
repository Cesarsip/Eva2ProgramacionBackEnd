from rest_framework import permissions

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
    message = "Acceso denegado: Se requiere rol de Estudiante para realizar esta acción."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.rol == 'ESTUDIANTE'
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
    message = "Acceso denegado: Se requiere rol de Coordinador Académico para realizar esta acción."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.rol == 'COORDINADOR' or request.user.is_staff or request.user.is_superuser)
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
    message = "Acceso denegado: La creación y modificación del catálogo requiere rol de Coordinador."

    def has_permission(self, request, view):
        # Lectura pública permitida para cualquier visitante
        if request.method in permissions.SAFE_METHODS:
            return True
        # Escritura restringida exclusivamente a Coordinadores
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.rol == 'COORDINADOR' or request.user.is_staff or request.user.is_superuser)
        )
