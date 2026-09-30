from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .models import Usuario, Area, Curso, CarroMatricula, ItemCarroMatricula, Matricula, DetalleMatricula

# Obtiene la clase de usuario configurada por el proyecto en Django.
User = get_user_model()

# =====================================================================
# BLOQUE 1: SERIALIZADOR DE AUTENTICACIÓN JWT CON CLAIMS DE ROL
# Cumple Especificación A y Criterio 2 de la Pauta:
# 'Payload personalizado (claims) que incluya el Rol del usuario (Cliente vs Administrador)'
# =====================================================================
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Personaliza el inicio de sesión JWT y expone el perfil básico del usuario.

    Los claims username/email identifican al usuario; rol y rol_display dan su
    rol interno y etiqueta; nombre_completo ofrece el nombre con fallback al
    username; is_staff/is_superuser indican privilegios. validate agrega
    ``usuario`` con id, username, email, nombre_completo, rol, rol_display,
    rut, telefono e is_staff. Quitar esta clase restaura el comportamiento de
    SimpleJWT y elimina dichos datos adicionales del token y la respuesta.
    """
    @classmethod
    def get_token(cls, user):
        """Construye el token base y añade claims; quitarla omite esos claims."""
        token = super().get_token(user)

        # username/email identifican la cuenta; rol/rol_display exponen el rol
        # interno y su etiqueta; nombre_completo incluye un fallback al username.
        # is_staff/is_superuser comunican flags de privilegio. Quitar cada línea
        # elimina ese dato del payload sin alterar el resto del token.
        token['username'] = user.username
        token['email'] = user.email
        token['rol'] = user.rol
        token['rol_display'] = user.get_rol_display()
        token['nombre_completo'] = f"{user.first_name} {user.last_name}".strip() or user.username
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        return token

    def validate(self, attrs):
        """Valida credenciales y añade ``usuario``; quitarla omite ese perfil."""
        data = super().validate(attrs)

        # id identifica el registro; username/email identifican la cuenta;
        # nombre_completo presenta el nombre; rol/rol_display describen permisos;
        # rut/telefono aportan datos de perfil e is_staff comunica el flag.
        # Quitar una clave suprime ese dato del objeto sin cambiar los tokens.
        data['usuario'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'nombre_completo': f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username,
            'rol': self.user.rol,
            'rol_display': self.user.get_rol_display(),
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
    Representa usuarios y permite crearlos con contraseña segura.

    ``password`` es opcional, solo de escritura y nunca se devuelve. Meta
    limita la representación a id, username, email, nombres, rol, RUT, teléfono
    y password; ``id`` es de solo lectura. Quitar este serializador elimina
    este contrato de registro/representación y su inicialización del carro.
    """
    # No devolver nunca la contraseña; al ser opcional se admiten cuentas sin
    # contraseña utilizable cuando el flujo de creación así lo requiere.
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        """Campos: id (identificador), username/email (cuenta), first_name/
        last_name (nombre), rol (perfil), rut/telefono (contacto) y password
        (entrada de contraseña). Quitar cualquiera lo excluye del contrato;
        model indica el modelo que se crea o representa.
        """
        model = Usuario
        # Quitar un campo de esta lista lo omite de entrada y/o salida del API;
        # incluir campos no listados podría exponer datos que no son parte del contrato.
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'rol', 'rut', 'telefono', 'password']
        # El cliente puede leer el identificador, pero no asignarlo al crear.
        read_only_fields = ['id']

    def create(self, validated_data):
        """Crea el usuario, almacena la contraseña de forma segura y crea su carro."""
        password = validated_data.pop('password', None)
        user = Usuario(**validated_data)
        if password:
            # set_password aplica el hash de Django; asignar password directamente
            # dejaría la contraseña sin el tratamiento seguro del framework.
            user.set_password(password)
        else:
            # Impide que una cuenta creada sin contraseña pueda autenticarse con
            # una contraseña vacía o accidentalmente definida.
            user.set_unusable_password()
        user.save()
        # El carro 1:1 queda disponible desde el primer uso; quitarlo obliga a
        # crearlo en otro flujo y puede dejar endpoints sin un carro asociado.
        CarroMatricula.objects.get_or_create(usuario=user)
        return user


# =====================================================================
# BLOQUE 3: SERIALIZADOR DE ÁREAS DE CONOCIMIENTO
# =====================================================================
class AreaSerializer(serializers.ModelSerializer):
    """
    Expone id, nombre, descripción, icono, estado, fecha de creación y
    ``total_cursos`` para un área. Quitar la clase elimina esta representación;
    omitir un campo de Meta.fields lo quita del contrato de entrada/salida.
    """
    # Campo calculado de solo lectura: evita guardar un conteo desactualizado.
    # Si se quita, el cliente deja de recibir la cantidad de cursos activos.
    total_cursos = serializers.SerializerMethodField()

    class Meta:
        """Campos: id identifica el área; nombre, descripcion e icono la
        describen; activo indica disponibilidad; total_cursos informa cursos
        activos; fecha_creacion registra su alta. Quitar un campo lo excluye
        de la API; model selecciona el modelo representado.
        """
        model = Area
        fields = ['id', 'nombre', 'descripcion', 'icono', 'activo', 'total_cursos', 'fecha_creacion']

    # Calcula el conteo al serializar para que refleje los cursos activos actuales.
    # Sin este método, total_cursos no tendría el valor calculado que entrega la API.
    def get_total_cursos(self, obj):
        return obj.cursos.filter(activo=True).count()


# =====================================================================
# BLOQUE 4: SERIALIZADOR DE CURSOS Y BOOTCAMPS (OFERTA ACADÉMICA)
# =====================================================================
class CursoSerializer(serializers.ModelSerializer):
    """
    Expone los datos del curso/bootcamp y valida coherencia de fechas y cupos.

    Meta.fields incluye id, título, descripción, área y su nombre, modalidad
    y su etiqueta, costo, fechas, cupos, imagen, estado, disponibilidad
    calculada y fecha de creación. Si se quita la clase se pierde el contrato
    de cursos; si se quita un campo de Meta.fields, deja de viajar por el API.
    """
    # Nombre relacionado de solo lectura para evitar que el cliente duplique
    # o modifique el nombre del área al escribir un curso.
    area_nombre = serializers.ReadOnlyField(source='area.nombre')
    # Etiqueta legible de la opción de modalidad; sin ella solo queda el código.
    modalidad_display = serializers.CharField(source='get_modalidad_display', read_only=True)
    # Indicador calculado del modelo y solo de salida; quitarlo oculta si quedan cupos.
    tiene_cupos = serializers.BooleanField(read_only=True)

    class Meta:
        """id identifica; titulo/descripcion describen; area y area_nombre
        identifican el área; modalidad/modalidad_display muestran tipo y
        etiqueta; costo_matricula informa el precio; fecha_inicio y
        fecha_termino marcan el período; cupos_totales y cupos_disponibles
        describen capacidad; imagen_url aporta la imagen; activo indica
        publicación; tiene_cupos resume disponibilidad; fecha_creacion registra
        el alta. Quitar un campo lo excluye de la API; model enlaza Curso.
        """
        model = Curso
        fields = [
            'id', 'titulo', 'descripcion', 'area', 'area_nombre',
            'modalidad', 'modalidad_display', 'costo_matricula',
            'fecha_inicio', 'fecha_termino', 'cupos_totales',
            'cupos_disponibles', 'imagen_url', 'activo', 'tiene_cupos',
            'fecha_creacion'
        ]

    def validate(self, attrs):
        """Valida fechas y cupos considerando también valores previos en PATCH.

        Sin esta validación se podrían guardar cursos con término anterior al
        inicio o con más cupos disponibles que totales; quitarla elimina ambas
        reglas en creación y actualización. Quitar la comparación de fechas
        permite rangos invertidos; quitar el control de cupos permite que los
        disponibles superen el total.
        """
        # En una actualización parcial los campos ausentes se toman de la instancia.
        fecha_inicio = attrs.get('fecha_inicio', getattr(self.instance, 'fecha_inicio', None))
        fecha_termino = attrs.get('fecha_termino', getattr(self.instance, 'fecha_termino', None))
        if fecha_inicio and fecha_termino and fecha_inicio > fecha_termino:
            raise serializers.ValidationError({"fecha_termino": "La fecha de término no puede ser anterior a la de inicio."})

        # Los valores por defecto permiten evaluar campos omitidos al crear; sin
        # este control el inventario publicado podría exceder su capacidad.
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
    Representa un ítem del carro con id, curso y fecha de agregado.

    ``curso`` anida la representación completa del curso y es de solo lectura;
    ``curso_id`` acepta la clave primaria de un curso activo para escritura.
    Quitar la clase impide representar/agregar ítems con este contrato; quitar
    cualquiera de esos campos elimina, respectivamente, el detalle de salida
    o la vía de asignación del curso.
    """
    # El objeto anidado permite mostrar los datos del curso sin otra petición.
    curso = CursoSerializer(read_only=True)
    # Resuelve el identificador a una instancia válida y solo acepta cursos
    # activos. El source enlaza la entrada con el atributo de modelo ``curso``.
    curso_id = serializers.PrimaryKeyRelatedField(
        queryset=Curso.objects.filter(activo=True),
        source='curso',
        write_only=True
    )

    class Meta:
        """id identifica el ítem; curso contiene el curso anidado; curso_id
        acepta su clave al escribir; fecha_agregado registra cuándo se añadió.
        Quitar un campo elimina ese dato o vía de escritura; model enlaza el
        serializador con ItemCarroMatricula.
        """
        model = ItemCarroMatricula
        fields = ['id', 'curso', 'curso_id', 'fecha_agregado']


class AgregarItemCarroSerializer(serializers.Serializer):
    """
    Valida el dato de entrada para agregar un curso al carro.

    ``curso_id`` es obligatorio y debe ser entero. Este serializador no verifica
    que el curso exista o esté activo: esa comprobación no se añade aquí porque
    el campo conserva IntegerField. Quitar la clase elimina la validación
    tipada/obligatoria que este flujo aplica a la solicitud.
    """
    # required=True rechaza peticiones sin identificador; IntegerField rechaza
    # valores que no puedan validarse como enteros.
    curso_id = serializers.IntegerField(required=True)



class CarroMatriculaSerializer(serializers.ModelSerializer):
    """
    Expone el carro persistente, sus ítems y sus totales calculados.

    Los campos son id, estudiante (username del usuario), items, total,
    total_items y fechas de creación/actualización. Quitar el serializador
    elimina el formato de lectura del carro; quitar un campo suprime ese dato
    de la representación.
    """
    # Los ítems se anidan para devolver el contenido en una sola respuesta;
    # read_only evita modificar la colección directamente desde este campo.
    items = ItemCarroMatriculaSerializer(many=True, read_only=True)
    # Total monetario calculado por el modelo; DecimalField conserva dos decimales.
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    # Cantidad calculada de ítems, solo de salida.
    total_items = serializers.IntegerField(read_only=True)
    # Identidad legible del propietario sin exponer una entrada para cambiarlo.
    estudiante = serializers.ReadOnlyField(source='usuario.username')

    class Meta:
        """id identifica el carro; estudiante identifica su propietario;
        items contiene los cursos; total y total_items resumen su contenido;
        fecha_creacion/fecha_actualizacion registran su ciclo de vida. Quitar
        un campo lo elimina de la respuesta; model enlaza CarroMatricula.
        """
        model = CarroMatricula
        fields = ['id', 'estudiante', 'items', 'total', 'total_items', 'fecha_creacion', 'fecha_actualizacion']


# =====================================================================
# BLOQUE 6: SERIALIZADORES DE MATRÍCULA HISTÓRICA Y TICKETS UUID
# =====================================================================
class DetalleMatriculaSerializer(serializers.ModelSerializer):
    """
    Representa una inscripción individual con curso, precio, ticket y fecha.

    ``curso_titulo`` y ``area_nombre`` son datos relacionados de solo lectura.
    Quitar la clase elimina la representación de los detalles históricos; quitar
    esos campos elimina el dato correspondiente, sin afectar el registro modelo.
    """
    # Acceso legible al título sin permitir cambiarlo desde el detalle.
    curso_titulo = serializers.ReadOnlyField(source='curso.titulo')
    # El área se obtiene a través del curso; al quitarlo el cliente pierde esa
    # información contextual en la respuesta de matrícula.
    area_nombre = serializers.ReadOnlyField(source='curso.area.nombre')

    class Meta:
        """id identifica el detalle; curso referencia el curso; curso_titulo y
        area_nombre lo describen; precio_unitario guarda el precio histórico;
        codigo_ticket identifica el ticket; fecha_inscripcion registra el alta.
        Quitar un campo lo omite de la respuesta; model enlaza el detalle.
        """
        model = DetalleMatricula
        fields = [
            'id', 'curso', 'curso_titulo', 'area_nombre',
            'precio_unitario', 'codigo_ticket', 'fecha_inscripcion'
        ]


class MatriculaSerializer(serializers.ModelSerializer):
    """
    Representa una matrícula/orden histórica con datos del estudiante,
    estado, total, detalles y fechas. Meta.fields declara cada dato enviado;
    quitar un campo lo excluye de la API y quitar la clase elimina esta
    representación de la matrícula.
    """
    # Detalles anidados y de solo lectura: exponen inscripciones/tickets sin
    # permitir alterar el historial desde la matrícula.
    detalles = DetalleMatriculaSerializer(many=True, read_only=True)
    # Atributo relacionado de solo lectura para identificar al estudiante.
    estudiante_username = serializers.ReadOnlyField(source='estudiante.username')
    # Nombre legible calculado por get_estudiante_nombre.
    estudiante_nombre = serializers.SerializerMethodField()
    # Etiqueta humana del estado CHOICES; sin ella solo se devuelve su valor interno.
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        """id identifica la orden; codigo_transaccion identifica la operación;
        estudiante y estudiante_username identifican al titular;
        estudiante_nombre ofrece su nombre; total y estado guardan pago/estado;
        estado_display aporta la etiqueta; detalles contiene inscripciones;
        fechas registran creación y actualización. Quitar un campo lo omite de
        la API; model enlaza Matricula.
        """
        model = Matricula
        fields = [
            'id', 'codigo_transaccion', 'estudiante', 'estudiante_username',
            'estudiante_nombre', 'total', 'estado', 'estado_display',
            'detalles', 'fecha_creacion', 'fecha_actualizacion'
        ]

    def get_estudiante_nombre(self, obj):
        """Devuelve nombre y apellido, o username si no hay nombre registrado."""
        return f"{obj.estudiante.first_name} {obj.estudiante.last_name}".strip() or obj.estudiante.username


class CambiarEstadoMatriculaSerializer(serializers.Serializer):
    """
    Valida la entrada para cambiar el estado de una matrícula (PATCH).

    ``estado`` es obligatorio y debe pertenecer a las opciones del modelo;
    ``motivo`` es opcional y puede ser una cadena vacía. No persiste ni aplica
    el cambio por sí mismo: eso corresponde al flujo que consume los datos.
    Quitar la clase elimina esta validación; quitar ``estado`` deja sin
    validar la transición y quitar una opción impide solicitar ese estado.
    """
    # ChoiceField restringe la transición a los valores declarados en el modelo.
    estado = serializers.ChoiceField(choices=Matricula.EstadoMatriculaChoices.choices)
    # Campo opcional para acompañar el cambio con una explicación.
    motivo = serializers.CharField(required=False, allow_blank=True)
