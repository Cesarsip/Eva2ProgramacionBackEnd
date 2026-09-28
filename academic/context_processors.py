from django.conf import settings

def student_footer_context(request):
    """
    Context Processor para inyectar los datos del alumno en todas las plantillas HTML.
    Cumple con el Criterio 6 de la Pauta de Evaluación:
    'Pie de Página (Footer): Para aquellos endpoints o vistas HTML base utilizadas,
    se deben mantener visibles los datos del alumno: Nombre Completo, Sección y Año.'
    """
    student_info = getattr(settings, 'STUDENT_DATA', {
        'NOMBRE_COMPLETO': 'César Silva',
        'SECCION': 'Sección D1 - Desarrollo Backend',
        'ANIO': '2026',
        'ASIGNATURA': 'Desarrollo Backend',
        'DOCENTE': 'Marcelo Alvarado',
        'PROYECTO': 'Plataforma de Reservas de Cursos y Bootcamps (EdTech)',
    })
    return {
        'student_data': student_info,
        'ALUMNO_NOMBRE': student_info.get('NOMBRE_COMPLETO'),
        'ALUMNO_SECCION': student_info.get('SECCION'),
        'ALUMNO_ANIO': student_info.get('ANIO'),
    }
