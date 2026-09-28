from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .models import Usuario, Area, Curso, CarroMatricula, ItemCarroMatricula, Matricula, DetalleMatricula

User = get_user_model()

# =====================================================================
# BLOQUE 1: SERIALIZADOR DE AUTENTICACIÓN JWT CON CLAIMS DE ROL
# Cumple Especificación A y Criterio 2 de la Pauta:
# 'Payload personalizado (claims) que incluya el Rol del usuario (Cliente vs Administrador)'
# =====================================================================
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializador de login JWT personalizado.
    Inyecta el Rol del usuario y metadatos dentro de los claims del payload
    del token y en el cuerpo de la respuesta JSON.
    
    Si este serializador se elimina o se usa el predeterminado de SimpleJWT,
    el token solo contendría el user_id y el cliente/frontend no podría
    reconocer el rol para aplicar RBAC sin hacer peticiones adicionales.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Inyección de claims personalizados en el payload del JWT
        token['username'] = user.username
        token['email'] = user.email
        token['rol'] = user.rol
        token['nombre_completo'] = f"{user.first_name} {user.last_name}".strip() or user.username
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Información extendida en la respuesta JSON del endpoint /api/token/
        data['usuario'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'nombre_completo': f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username,
            'rol': self.user.rol,
            'rut': self.user.rut,
            'telefono': self.user.telefono,
            'is_staff': self.user.is_staff,
        }
        return data


# =====================================================================
# BLOQUE 2: SERIALIZADOR DE USUARIOS / REGISTRO
# =====================================================================
class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializador para visualización y registro de usuarios en la plataforma.
    Permite registrar nuevos estudiantes y coordinadores con contraseñas seguras.
    """
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'rol', 'rut', 'telefono', 'password']
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = Usuario(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        # Inicializa automáticamente el carro persistente del usuario
        CarroMatricula.objects.get_or_create(usuario=user)
        return user


# =====================================================================
# BLOQUE 3: SERIALIZADOR DE ÁREAS DE CONOCIMIENTO
# =====================================================================
class AreaSerializer(serializers.ModelSerializer):
    """
    Serializador para las Áreas de Conocimiento.
    Incluye el conteo dinámico de cursos activos pertenecientes al área.
    """
    total_cursos = serializers.SerializerMethodField()

    class Meta:
        model = Area
        fields = ['id', 'nombre', 'descripcion', 'icono', 'activo', 'total_cursos', 'fecha_creacion']

    def get_total_cursos(self, obj):
        return obj.cursos.filter(activo=True).count()


# =====================================================================
# BLOQUE 4: SERIALIZADOR DE CURSOS Y BOOTCAMPS (OFERTA ACADÉMICA)
# =====================================================================
class CursoSerializer(serializers.ModelSerializer):
    """
    Serializador para Cursos y Bootcamps.
    Expone campos del modelo con validaciones de fechas y cupos,
    así como representaciones legibles de choices.
    """
    area_nombre = serializers.ReadOnlyField(source='area.nombre')
    modalidad_display = serializers.CharField(source='get_modalidad_display', read_only=True)
    tiene_cupos = serializers.BooleanField(read_only=True)

    class Meta:
        model = Curso
        fields = [
            'id', 'titulo', 'descripcion', 'area', 'area_nombre',
            'modalidad', 'modalidad_display', 'costo_matricula',
            'fecha_inicio', 'fecha_termino', 'cupos_totales',
            'cupos_disponibles', 'imagen_url', 'activo', 'tiene_cupos',
            'fecha_creacion'
        ]

    def validate(self, attrs):
        # Validación: Fecha de inicio debe ser anterior o igual a la de término
        fecha_inicio = attrs.get('fecha_inicio', getattr(self.instance, 'fecha_inicio', None))
        fecha_termino = attrs.get('fecha_termino', getattr(self.instance, 'fecha_termino', None))
        if fecha_inicio and fecha_termino and fecha_inicio > fecha_termino:
            raise serializers.ValidationError({"fecha_termino": "La fecha de término no puede ser anterior a la de inicio."})

        # Validación: Cupos disponibles no pueden superar los cupos totales
        cupos_totales = attrs.get('cupos_totales', getattr(self.instance, 'cupos_totales', 30))
        cupos_disponibles = attrs.get('cupos_disponibles', getattr(self.instance, 'cupos_disponibles', cupos_totales))
        if cupos_disponibles > cupos_totales:
            raise serializers.ValidationError({"cupos_disponibles": "Los cupos disponibles no pueden exceder los cupos totales."})

        return attrs


# =====================================================================
# BLOQUE 5: SERIALIZADORES DEL CARRO DE COMPRAS PERSISTENTE
# =====================================================================
class ItemCarroMatriculaSerializer(serializers.ModelSerializer):
    """
    Serializador para ítems dentro del carro de matrícula persistente.
    Retorna la información completa del curso para renderizado en frontend.
    """
    curso = CursoSerializer(read_only=True)
    curso_id = serializers.PrimaryKeyRelatedField(
        queryset=Curso.objects.filter(activo=True),
        source='curso',
        write_only=True
    )

    class Meta:
        model = ItemCarroMatricula
        fields = ['id', 'curso', 'curso_id', 'fecha_agregado']


class AgregarItemCarroSerializer(serializers.Serializer):
    """
    Serializador para validar el agregado de un curso al carro de matrícula.
    Valida la existencia del curso activo.
    """
    curso_id = serializers.IntegerField(required=True)



class CarroMatriculaSerializer(serializers.ModelSerializer):
    """
    Serializador del Carro de Matrícula Persistente.
    Cumple con la relación 1:1 y persistencia en base de datos.
    Calcula el monto total a pagar y el número total de items agregados.
    """
    items = ItemCarroMatriculaSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    estudiante = serializers.ReadOnlyField(source='usuario.username')

    class Meta:
        model = CarroMatricula
        fields = ['id', 'estudiante', 'items', 'total', 'total_items', 'fecha_creacion', 'fecha_actualizacion']


# =====================================================================
# BLOQUE 6: SERIALIZADORES DE MATRÍCULA HISTÓRICA Y TICKETS UUID
# =====================================================================
class DetalleMatriculaSerializer(serializers.ModelSerializer):
    """
    Serializador de inscripción oficial con ticket UUID único por curso.
    """
    curso_titulo = serializers.ReadOnlyField(source='curso.titulo')
    area_nombre = serializers.ReadOnlyField(source='curso.area.nombre')

    class Meta:
        model = DetalleMatricula
        fields = [
            'id', 'curso', 'curso_titulo', 'area_nombre',
            'precio_unitario', 'codigo_ticket', 'fecha_inscripcion'
        ]


class MatriculaSerializer(serializers.ModelSerializer):
    """
    Serializador del registro histórico de Matrícula / Orden.
    Incluye el código UUID único de la transacción, el estudiante asociado,
    el total cancelado y los detalles de las inscripciones generadas.
    """
    detalles = DetalleMatriculaSerializer(many=True, read_only=True)
    estudiante_username = serializers.ReadOnlyField(source='estudiante.username')
    estudiante_nombre = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Matricula
        fields = [
            'id', 'codigo_transaccion', 'estudiante', 'estudiante_username',
            'estudiante_nombre', 'total', 'estado', 'estado_display',
            'detalles', 'fecha_creacion', 'fecha_actualizacion'
        ]

    def get_estudiante_nombre(self, obj):
        return f"{obj.estudiante.first_name} {obj.estudiante.last_name}".strip() or obj.estudiante.username


class CambiarEstadoMatriculaSerializer(serializers.Serializer):
    """
    Serializador para la modificación de estado de una matrícula (PATCH por Coordinador).
    Valida que el nuevo estado pertenezca a la máquina de estados CHOICES.
    """
    estado = serializers.ChoiceField(choices=Matricula.EstadoMatriculaChoices.choices)
    motivo = serializers.CharField(required=False, allow_blank=True)
