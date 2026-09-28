from django.contrib import admin
from .models import Usuario, Area, Curso, CarroMatricula, ItemCarroMatricula, Matricula, DetalleMatricula

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'rol', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('rol', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'rut')


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'fecha_creacion')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')


class ItemCarroInline(admin.TabularInline):
    model = ItemCarroMatricula
    extra = 0


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'area', 'modalidad', 'costo_matricula', 'cupos_disponibles', 'cupos_totales', 'fecha_inicio', 'activo')
    list_filter = ('modalidad', 'area', 'activo')
    search_fields = ('titulo', 'descripcion')


@admin.register(CarroMatricula)
class CarroMatriculaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'total_items', 'total', 'fecha_actualizacion')
    inlines = [ItemCarroInline]


class DetalleMatriculaInline(admin.TabularInline):
    model = DetalleMatricula
    extra = 0
    readonly_fields = ('codigo_ticket', 'fecha_inscripcion')


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ('codigo_transaccion', 'estudiante', 'total', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('codigo_transaccion', 'estudiante__username', 'estudiante__email')
    inlines = [DetalleMatriculaInline]
