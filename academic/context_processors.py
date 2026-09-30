from django.conf import settings  # Permite leer la configuración global; al quitarlo no se obtendrían STUDENT_DATA desde settings.

def student_footer_context(request):
    """
    Context Processor para inyectar los datos del alumno en todas las plantillas HTML.
    Cumple con el Criterio 6 de la Pauta de Evaluación:
    'Pie de Página (Footer): Para aquellos endpoints o vistas HTML base utilizadas,
    se deben mantener visibles los datos del alumno: Nombre Completo, Sección y Año.'
    """
    # Toma los datos configurados y define valores de respaldo si la clave falta; al quitarlo las siguientes lecturas no tendrían fuente de datos.
    student_info = getattr(settings, 'STUDENT_DATA', {
        'NOMBRE_COMPLETO': 'CESAR ANTONIO AEDO ALVAREZ',
        'SECCION': 'IEC-N4-C2',
        'ANIO': '2026',
        'ASIGNATURA': 'Desarrollo Backend',
        'DOCENTE': 'Marcelo Alvarado',
        'PROYECTO': 'Plataforma de Reservas de Cursos y Bootcamps (EdTech)',
    })
    return {  # Entrega variables al contexto de todas las plantillas; al quitar el diccionario, el footer no recibiría estos datos.
        'student_data': student_info,  # Expone el conjunto completo; al quitarlo las plantillas perderían acceso a los demás datos del alumno.
        'ALUMNO_NOMBRE': student_info.get('NOMBRE_COMPLETO', 'CESAR ANTONIO AEDO ALVAREZ'),  # Publica el nombre con respaldo; al quitarlo el footer no podría mostrarlo.
        'ALUMNO_SECCION': student_info.get('SECCION', 'IEC-N4-C2'),  # Publica la sección con respaldo; al quitarlo no se mostraría en el footer.
        'ALUMNO_ANIO': student_info.get('ANIO', '2026'),  # Publica el año con respaldo; al quitarlo no se mostraría en el footer.
    }
