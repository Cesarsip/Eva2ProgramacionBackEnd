import django_filters  # Importa los tipos de filtro; al quitarlo las declaraciones de filtros fallarían.
from .models import Curso, Area, Matricula  # Importa los modelos que se consultan; al quitarlo no se podrían mapear filtros a tablas.

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
    # Cada filtro convierte un parámetro URL en condición ORM; si se elimina, ese criterio dejará de filtrar el catálogo.
    titulo = django_filters.CharFilter(  # Define la búsqueda textual del título; si se elimina, ?titulo= dejará de buscar.
        field_name='titulo',  # Selecciona la columna a consultar; si se cambia, se filtrará otro dato o fallará.
        lookup_expr='icontains',  # Busca texto parcial sin distinguir mayúsculas; si se quita, se aplicaría la comparación predeterminada.
        label='Buscar por Título'  # Nombra el filtro en formularios/documentación; si se quita, la API funciona pero pierde esa etiqueta legible.
    )
    area = django_filters.NumberFilter(  # Acepta el ID numérico del área; si se elimina, no se podrá filtrar por área_id.
        field_name='area_id',  # Filtra la FK por su columna ID; si se quita, no se vinculará con el área correcta.
        label='ID del Área de Conocimiento'  # Describe el parámetro en interfaces/documentación; quitarlo solo afecta su rótulo.
    )
    area_nombre = django_filters.CharFilter(  # Permite buscar por nombre del área relacionada; si se quita, solo quedará el filtro numérico.
        field_name='area__nombre',  # Sigue la relación Curso.area hasta Area.nombre; si se cambia, se consultará otro atributo.
        lookup_expr='icontains',  # Permite coincidencia parcial sin mayúsculas; al quitarlo se restringe la comparación.
        label='Nombre del Área'  # Proporciona una etiqueta legible; su eliminación no cambia la consulta.
    )
    modalidad = django_filters.ChoiceFilter(  # Restringe el parámetro a modalidades permitidas; si se elimina, no se filtra por modalidad.
        field_name='modalidad',  # Indica el campo de Curso; si se cambia, se filtra otro campo.
        choices=Curso.ModalidadChoices.choices,  # Limita opciones a las del modelo; si se quita, se pierde validación de opciones.
        label='Modalidad (BOOTCAMP, CURSO, TALLER)'  # Explica los valores válidos en la documentación; quitarlo solo afecta la etiqueta.
    )
    precio_min = django_filters.NumberFilter(  # Declara el límite inferior de precio; si se quita, no se podrá filtrar el precio mínimo.
        field_name='costo_matricula',  # Apunta al importe; si se cambia, el rango usa otra columna.
        lookup_expr='gte',  # Incluye precios mayores o iguales; al quitarlo cambia la comparación predeterminada.
        label='Precio Mínimo de Matrícula'  # Describe el límite; su eliminación afecta solo la presentación.
    )
    precio_max = django_filters.NumberFilter(  # Declara el límite superior de precio; si se quita, no se podrá filtrar el precio máximo.
        field_name='costo_matricula',  # Apunta al importe; si se cambia, el rango consulta otra columna.
        lookup_expr='lte',  # Incluye precios menores o iguales; al quitarlo cambia la comparación predeterminada.
        label='Precio Máximo de Matrícula'  # Describe el límite; su eliminación solo afecta la presentación.
    )
    fecha_inicio = django_filters.DateFilter(  # Permite filtrar desde una fecha; si se elimina, ese criterio no estará disponible.
        field_name='fecha_inicio',  # Apunta al inicio del curso; si se cambia, se consulta otra fecha.
        lookup_expr='gte',  # Incluye cursos que comienzan en la fecha indicada o después; si se quita cambia el umbral.
        label='Disponible a partir de fecha'  # Explica el campo al cliente; quitarlo solo afecta la etiqueta.
    )
    con_cupo = django_filters.BooleanFilter(  # Acepta true/false para filtrar disponibilidad; si se elimina, no existe ?con_cupo=.
        method='filter_con_cupo',  # Enlaza el valor con la lógica inferior; si se quita, no se ejecutará la condición personalizada.
        label='Solo Cursos con Cupos Disponibles'  # Describe el control en la API; quitarlo no altera la lógica del filtro.
    )

    agotado = django_filters.BooleanFilter(
        method='filter_agotado',
        label='Solo Cursos Agotados'
    )

    class Meta:
        model = Curso  # Vincula los filtros con la tabla Curso; al quitarlo el FilterSet no sabría qué datos filtrar.
        fields = ['titulo', 'area', 'area_nombre', 'modalidad', 'precio_min', 'precio_max', 'fecha_inicio', 'con_cupo', 'agotado']  # Publica los filtros admitidos; al quitarlo el conjunto de criterios dejaría de estar definido.

    def filter_con_cupo(self, queryset, name, value):
        if value:
            return queryset.filter(cupos_disponibles__gt=0)  # Excluye cursos agotados cuando el valor es True; al quitarlo ?con_cupo=true no aplicaría.
        return queryset  # Conserva todos los cursos si el filtro está apagado; al quitarlo el caso False podría devolver None.

    def filter_agotado(self, queryset, name, value):
        # El catálogo usa ?agotado=true para pedir solo cursos con cero cupos.
        if value:
            return queryset.filter(cupos_disponibles=0)
        return queryset


class AreaFilter(django_filters.FilterSet):
    """
    Filtro para consultar Áreas de Conocimiento.
    Permite filtrar por nombre y estado activo.
    """
    nombre = django_filters.CharFilter(  # Define búsqueda parcial de áreas por nombre; si se elimina, se pierde este parámetro.
        field_name='nombre',  # Consulta la columna nombre; cambiarlo afecta la columna consultada.
        lookup_expr='icontains',  # Ignora mayúsculas y acepta coincidencias parciales; al quitarlo la comparación cambia.
        label='Nombre del Área'  # Muestra una etiqueta legible; quitarla afecta documentación, no consulta.
    )
    activo = django_filters.BooleanFilter(  # Permite incluir/excluir áreas activas; al quitarlo no se puede filtrar por estado.
        field_name='activo',  # Consulta el indicador activo; si se cambia se filtra otro atributo.
        label='Área Activa'  # Explica el filtro; quitarla solo afecta su rótulo.
    )

    class Meta:
        model = Area  # Define la entidad consultada; al quitarlo el filtro no conocería su modelo.
        fields = ['nombre', 'activo']  # Expone búsqueda por nombre y estado; al quitarlo no se declararían esos parámetros.


class MatriculaFilter(django_filters.FilterSet):
    """
    Filtro para las Órdenes de Matrícula (utilizado por Coordinación).
    Permite filtrar por estado de la transacción (PENDIENTE, PAGADO, CANCELADO)
    y rango de fechas.
    """
    estado = django_filters.ChoiceFilter(  # Filtra por estado de matrícula; sin él coordinación no puede segmentar estados.
        field_name='estado',  # Apunta a la columna del estado; si se cambia, consulta otro dato.
        choices=Matricula.EstadoMatriculaChoices.choices,  # Valida los estados definidos en el modelo; si se quita, se aceptan valores ajenos al conjunto.
        label='Estado de la Transacción'  # Hace claro el criterio en la API; quitarlo solo cambia la presentación.
    )
    estudiante = django_filters.CharFilter(  # Permite encontrar matrículas por estudiante; si se elimina, se pierde esa búsqueda.
        field_name='estudiante__username',  # Sigue la FK estudiante hasta username; cambiarlo consulta otro dato relacionado.
        lookup_expr='icontains',  # Busca parcialmente sin distinguir mayúsculas; al quitarlo la coincidencia será más estricta.
        label='Username del Estudiante'  # Explica el parámetro; quitarlo afecta solo la presentación.
    )
    fecha_desde = django_filters.DateFilter(  # Define el límite inferior de fechas de matrícula; si se quita, no se filtra desde fecha.
        field_name='fecha_creacion__date',  # Convierte la fecha/hora a fecha para comparar; cambiarlo altera la columna.
        lookup_expr='gte',  # Incluye ese día y posteriores; si se quita cambia la comparación.
        label='Fecha de Transacción Desde'  # Explica el límite; quitarlo afecta solo la etiqueta.
    )
    fecha_hasta = django_filters.DateFilter(  # Define el límite superior de fechas; si se quita, no se filtra hasta una fecha.
        field_name='fecha_creacion__date',  # Usa la fecha de creación; si se cambia, se consulta otro atributo.
        lookup_expr='lte',  # Incluye el día indicado y anteriores; al quitarlo cambia el límite.
        label='Fecha de Transacción Hasta'  # Explica el límite; quitarla solo afecta la presentación.
    )

    class Meta:
        model = Matricula  # Define la entidad de órdenes filtrada; al quitarlo el FilterSet no sabría qué consultar.
        fields = ['estado', 'estudiante', 'fecha_desde', 'fecha_hasta']  # Expone criterios de coordinación; al quitarlo esos filtros no estarían disponibles.
