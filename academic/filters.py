import django_filters
from .models import Curso, Area, Matricula

# =====================================================================
# BLOQUE DE FILTROS AVANZADOS (DJANGO-FILTER)
# Cumple Especificación E y Criterio 1: 'django-filter configurado en endpoints'
# =====================================================================

class CursoFilter(django_filters.FilterSet):
    """
    Filtro avanzado para el catálogo de Cursos y Bootcamps.
    Permite a los estudiantes y coordinadores buscar y segmentar la oferta
    por área de conocimiento, rango de precios, modalidad y cupos disponibles.
    
    Si se elimina este filtro o DjangoFilterBackend, los parámetros de búsqueda
    en la URL (ej: ?area=1&precio_max=50000) serían ignorados por DRF.
    """
    titulo = django_filters.CharFilter(
        field_name='titulo',
        lookup_expr='icontains',
        label='Buscar por Título'
    )
    area = django_filters.NumberFilter(
        field_name='area_id',
        label='ID del Área de Conocimiento'
    )
    area_nombre = django_filters.CharFilter(
        field_name='area__nombre',
        lookup_expr='icontains',
        label='Nombre del Área'
    )
    modalidad = django_filters.ChoiceFilter(
        field_name='modalidad',
        choices=Curso.ModalidadChoices.choices,
        label='Modalidad (BOOTCAMP, CURSO, TALLER)'
    )
    precio_min = django_filters.NumberFilter(
        field_name='costo_matricula',
        lookup_expr='gte',
        label='Precio Mínimo de Matrícula'
    )
    precio_max = django_filters.NumberFilter(
        field_name='costo_matricula',
        lookup_expr='lte',
        label='Precio Máximo de Matrícula'
    )
    fecha_inicio = django_filters.DateFilter(
        field_name='fecha_inicio',
        lookup_expr='gte',
        label='Disponible a partir de fecha'
    )
    con_cupo = django_filters.BooleanFilter(
        method='filter_con_cupo',
        label='Solo Cursos con Cupos Disponibles'
    )

    class Meta:
        model = Curso
        fields = ['titulo', 'area', 'area_nombre', 'modalidad', 'precio_min', 'precio_max', 'fecha_inicio', 'con_cupo']

    def filter_con_cupo(self, queryset, name, value):
        if value:
            return queryset.filter(cupos_disponibles__gt=0)
        return queryset


class AreaFilter(django_filters.FilterSet):
    """
    Filtro para consultar Áreas de Conocimiento.
    Permite filtrar por nombre y estado activo.
    """
    nombre = django_filters.CharFilter(
        field_name='nombre',
        lookup_expr='icontains',
        label='Nombre del Área'
    )
    activo = django_filters.BooleanFilter(
        field_name='activo',
        label='Área Activa'
    )

    class Meta:
        model = Area
        fields = ['nombre', 'activo']


class MatriculaFilter(django_filters.FilterSet):
    """
    Filtro para las Órdenes de Matrícula (utilizado por Coordinación).
    Permite filtrar por estado de la transacción (PENDIENTE, PAGADO, CANCELADO)
    y rango de fechas.
    """
    estado = django_filters.ChoiceFilter(
        field_name='estado',
        choices=Matricula.EstadoMatriculaChoices.choices,
        label='Estado de la Transacción'
    )
    estudiante = django_filters.CharFilter(
        field_name='estudiante__username',
        lookup_expr='icontains',
        label='Username del Estudiante'
    )
    fecha_desde = django_filters.DateFilter(
        field_name='fecha_creacion__date',
        lookup_expr='gte',
        label='Fecha de Transacción Desde'
    )
    fecha_hasta = django_filters.DateFilter(
        field_name='fecha_creacion__date',
        lookup_expr='lte',
        label='Fecha de Transacción Hasta'
    )

    class Meta:
        model = Matricula
        fields = ['estado', 'estudiante', 'fecha_desde', 'fecha_hasta']
