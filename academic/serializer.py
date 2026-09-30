"""Serializadores legados de Teacher/Student/Course, separados de la aplicación EdTech actual.
Se conservan para no romper importadores externos; el flujo actual usa academic.serializers (plural)."""

from rest_framework import serializers  # Importa la API de serialización de DRF; al quitarlo, las clases serializer no existirían.
from .models import Teacher, Course, Student, StudentCourse  # Importa modelos heredados de otro esquema; al quitarlo, sus serializadores no podrían referenciarlos.

# =====================================================================
# SERIALIZADORES DJANGO REST FRAMEWORK (serializers.py)
# Cumple Criterio 6: Mapeo de entidades a formato JSON y viceversa
# =====================================================================

class TeacherSerializer(serializers.ModelSerializer):
    """Serializador para la entidad Teacher (Docentes)."""
    class Meta:
        model = Teacher  # Asocia el serializador al modelo docente; quitarlo impide su generación automática.
        fields = ['id', 'first_name', 'last_name']  # Limita la salida a estos datos; al quitar un campo deja de exponerse.


class CourseSerializer(serializers.ModelSerializer):
    """
    Serializador para la entidad Course (Asignaturas).
    Incluye el nombre del profesor asignado para facilitar el consumo del frontend.
    """
    teacher_name = serializers.SerializerMethodField(read_only=True)  # Calcula un nombre visible del docente; quitarlo elimina ese dato de respuesta.

    class Meta:
        model = Course  # Vincula la salida con el modelo Course; sin esto DRF no conoce el modelo.
        fields = ['id', 'name', 'teacher', 'teacher_name']  # Define los atributos JSON; quitar uno evita devolverlo.

    def get_teacher_name(self, obj):
        if obj.teacher:  # Comprueba si hay docente asignado; quitarlo intentaría leer atributos de una referencia vacía.
            return f"Prof. {obj.teacher.first_name} {obj.teacher.last_name}"
        return "Sin profesor asignado"  # Da una etiqueta cuando falta docente; al quitarla el método no tendría respuesta para ese caso.


class StudentSerializer(serializers.ModelSerializer):
    """Serializador para la entidad Student (Estudiantes)."""
    enrolled_courses = serializers.SerializerMethodField(read_only=True)  # Añade una lista calculada de cursos; sin ella no se exponen inscripciones.

    class Meta:
        model = Student  # Vincula la respuesta al estudiante; al quitarlo DRF no sabrá de qué modelo serializar.
        fields = ['id', 'first_name', 'last_name', 'enrolled_courses']  # Define los campos JSON; quitarlos los oculta de la API.

    def get_enrolled_courses(self, obj):
        # Obtener los nombres de los cursos en los que está inscrito el estudiante
        return [sc.course.name for sc in obj.student_courses.all()]  # Recorre sus inscripciones y devuelve nombres; quitarlo elimina el contenido calculado.


class StudentCourseSerializer(serializers.ModelSerializer):
    """Serializador para la entidad intermedia StudentCourse (Inscripciones)."""
    student_name = serializers.SerializerMethodField(read_only=True)  # Agrega el nombre del estudiante; quitarlo impide mostrarlo en esta respuesta.
    course_name = serializers.SerializerMethodField(read_only=True)  # Agrega el nombre del curso; quitarlo impide mostrarlo en esta respuesta.

    class Meta:
        model = StudentCourse  # Asocia el serializador a la inscripción; al quitarlo no se genera la representación automáticamente.
        fields = ['id', 'student', 'course', 'student_name', 'course_name']  # Selecciona datos expuestos; quitar un campo lo elimina del JSON.

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"  # Une nombre y apellido; al quitarlo no se puede calcular student_name.

    def get_course_name(self, obj):
        return obj.course.name  # Obtiene el nombre relacionado; al quitarlo no se calcula course_name.
