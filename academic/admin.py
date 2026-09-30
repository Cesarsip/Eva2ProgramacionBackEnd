from django.contrib import admin
from .models import Usuario, Area, Curso, CarroMatricula, ItemCarroMatricula, Matricula, DetalleMatricula

# Registra y adapta los modelos para su gestión desde el sitio administrativo;
# sin estos registros dejarían de estar disponibles en el panel de Django.
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    # Columnas, filtros y búsquedas permiten localizar y revisar cuentas sin
    # abrir cada registro manualmente; al quitarlos se pierde esa navegación.
    list_display = ('username', 'email', 'rol', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('rol', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'rut')


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    # Facilita administrar áreas y encontrar las activas o sus descripciones.
    list_display = ('nombre', 'activo', 'fecha_creacion')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')


class ItemCarroInline(admin.TabularInline):
    # Muestra los cursos del carro dentro de su ficha; sin el inline habría que
    # gestionar los ítems por separado en el panel.
    model = ItemCarroMatricula
    extra = 0


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    # Expone datos clave del catálogo y filtros para mantener cursos publicados.
    list_display = ('titulo', 'area', 'modalidad', 'costo_matricula', 'cupos_disponibles', 'cupos_totales', 'fecha_inicio', 'activo')
    list_filter = ('modalidad', 'area', 'activo')
    search_fields = ('titulo', 'descripcion')


@admin.register(CarroMatricula)
class CarroMatriculaAdmin(admin.ModelAdmin):
    # Permite inspeccionar carros y sus ítems relacionados desde una sola vista.
    list_display = ('usuario', 'total_items', 'total', 'fecha_actualizacion')
    inlines = [ItemCarroInline]


class DetalleMatriculaInline(admin.TabularInline):
    # Los detalles se consultan junto con la matrícula y sus identificadores se
    # protegen de edición manual; sin esto se pierde esa revisión integrada.
    model = DetalleMatricula
    extra = 0
    readonly_fields = ('codigo_ticket', 'fecha_inscripcion')


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    # Presenta y filtra transacciones para la gestión académica desde el admin.
    list_display = ('codigo_transaccion', 'estudiante', 'total', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('codigo_transaccion', 'estudiante__username', 'estudiante__email')
    inlines = [DetalleMatriculaInline]
