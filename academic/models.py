import uuid  # Genera identificadores globalmente únicos para transacciones y tickets.
from decimal import Decimal  # Mantiene precisión decimal en montos monetarios.
from django.db import models  # Provee campos, relaciones y metadatos de los modelos.
from django.contrib.auth.models import AbstractUser  # Conserva autenticación y campos estándar de Django.
from django.conf import settings  # Permite referenciar el modelo de usuario configurable del proyecto.

# =====================================================================
# BLOQUE 1: MODELO DE USUARIO PERSONALIZADO Y CONTROL DE ROLES (RBAC)
# =====================================================================
class Usuario(AbstractUser):
    """
    Modelo de Usuario Custom que hereda de AbstractUser.
    Implementa el control de acceso basado en roles (RBAC) exigido por la pauta:
    - Rol ESTUDIANTE: Puede consultar catálogo, gestionar su carro y confirmar matrículas.
    - Rol COORDINADOR: Puede administrar áreas, cursos y modificar estados de matrículas.
    
    Si este bloque se elimina o se usa el modelo default de Django, no sería posible
    incluir el claim 'rol' dentro del token JWT ni aplicar los permisos específicos por rol.
    """
    class RolChoices(models.TextChoices):
        # Las opciones limitan el rol a perfiles admitidos y ofrecen etiquetas legibles en formularios.
        ESTUDIANTE = 'ESTUDIANTE', 'Estudiante'
        COORDINADOR = 'COORDINADOR', 'Coordinador Académico'

    # Rol requerido por permisos y autenticación; quitarlo eliminaría el dato persistente usado para autorizar.
    rol = models.CharField(
        max_length=20,
        choices=RolChoices.choices,
        default=RolChoices.ESTUDIANTE,
        verbose_name="Rol del Usuario",
        help_text="Define los permisos y nivel de acceso en la plataforma EdTech"
    )
    # Identificación opcional; quitarlo impediría almacenar el RUT asociado al usuario.
    rut = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="RUT / Identificación"
    )
    # Contacto opcional; quitarlo impediría guardar el teléfono en el perfil.
    telefono = models.CharField(
        max_length=25,
        blank=True,
        null=True,
        verbose_name="Teléfono de Contacto"
    )

    class Meta:
        # Nombre explícito de tabla usado por la base de datos y las migraciones.
        db_table = 'edtech_usuario'
        # Etiquetas visibles en la administración de Django.
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        # Incluye el rol mostrado al identificar usuarios en la administración y registros.
        return f"{self.username} [{self.get_rol_display()}]"

    @property
    def is_estudiante(self):
        """Indica si el rol es estudiante; los consumidores pierden esta comprobación legible si se elimina."""
        return self.rol == self.RolChoices.ESTUDIANTE

    @property
    def is_coordinador(self):
        """Incluye coordinadores y personal privilegiado de Django; quitarla elimina esta comprobación unificada."""
        return self.rol == self.RolChoices.COORDINADOR or self.is_staff or self.is_superuser


# =====================================================================
# BLOQUE 2: ÁREA DE CONOCIMIENTO (GESTIÓN DEL COORDINADOR)
# =====================================================================
class Area(models.Model):
    """
    Entidad Área de Conocimiento.
    Permite organizar los cursos y bootcamps en especialidades tecnológicas
    (ej: Desarrollo Web, Ciberseguridad, Data Science, Cloud & DevOps).
    El Coordinador es el único autorizado para crear, editar o eliminar áreas.
    
    Si este modelo se elimina, se pierde la categorización y la integridad
    referencial de los cursos ofertados.
    """
    # Nombre único para evitar áreas duplicadas y servir como etiqueta principal.
    nombre = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Nombre del Área",
        help_text="Ej: Desarrollo Web & Cloud, Inteligencia Artificial, Ciberseguridad"
    )
    # Descripción opcional; default vacío permite crear áreas sin texto descriptivo.
    descripcion = models.TextField(
        blank=True,
        default='',
        verbose_name="Descripción del Área"
    )
    # Clase de icono consumida por la interfaz; el valor por defecto evita áreas sin icono configurado.
    icono = models.CharField(
        max_length=50,
        default='bi-mortarboard',
        verbose_name="Ícono Bootstrap",
        help_text="Clase del ícono para renderizado frontend (ej. bi-code-slash, bi-shield-lock)"
    )
    # Permite ocultar o desactivar el área sin borrarla ni romper referencias históricas.
    activo = models.BooleanField(
        default=True,
        verbose_name="Área Activa"
    )
    # Se asigna una sola vez al crear el registro; quitarlo elimina la fecha de alta persistida.
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )

    class Meta:
        # Conserva el nombre de tabla esperado por el esquema existente.
        db_table = 'edtech_area'
        # Nombres singulares y plurales para la administración.
        verbose_name = 'Área de Conocimiento'
        verbose_name_plural = 'Áreas de Conocimiento'
        # Ordena listados por nombre; quitarlo deja el orden de consulta sin definir aquí.
        ordering = ['nombre']

    def __str__(self):
        # Usa el nombre como representación legible de un área.
        return self.nombre


# =====================================================================
# BLOQUE 3: CURSOS Y BOOTCAMPS (OFERTA ACADÉMICA Y CONTROL DE CUPOS)
# =====================================================================
class Curso(models.Model):
    """
    Entidad Curso / Bootcamp.
    Representa los programas educativos ofrecidos a los estudiantes.
    Cada curso cuenta con:
    - Costo de matrícula (precio)
    - Fechas de inicio y término
    - Cupos totales (límite máximo por cohorte)
    - Cupos disponibles (inventario atómico descontado solo al PAGAR)
    
    Si se elimina choices en modalidad, no se podría restringir el tipo de curso.
    Si se elimina cupos_disponibles, no existiría base de datos para la lógica
    transaccional de inventario exigida en la pauta.
    """
    class ModalidadChoices(models.TextChoices):
        # Valores almacenados y etiquetas de presentación de las modalidades permitidas.
        BOOTCAMP = 'BOOTCAMP', 'Bootcamp Intensivo'
        CURSO = 'CURSO', 'Curso Regular'
        TALLER = 'TALLER', 'Taller Especializado'

    # Título requerido y visible en el catálogo; quitarlo elimina la identificación textual del curso.
    titulo = models.CharField(
        max_length=200,
        verbose_name="Título del Curso / Bootcamp"
    )
    # Presenta el contenido y los objetivos del programa; al quitarlo se pierde esa información persistida.
    descripcion = models.TextField(
        verbose_name="Descripción del Programa y Objetivos"
    )
    # Cada curso pertenece a un área; CASCADE elimina cursos al borrar el área y related_name habilita area.cursos.
    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name='cursos',
        verbose_name="Área de Conocimiento"
    )
    # Restringe la modalidad a las opciones declaradas y define el valor inicial para cursos nuevos.
    modalidad = models.CharField(
        max_length=20,
        choices=ModalidadChoices.choices,
        default=ModalidadChoices.BOOTCAMP,
        verbose_name="Modalidad del Programa"
    )
    # Importe de matrícula almacenado con precisión decimal; quitarlo elimina el precio del curso.
    costo_matricula = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Costo de Matrícula ($CLP)"
    )
    # Inicio del curso, necesario para mostrar y ordenar la oferta por fecha.
    fecha_inicio = models.DateField(
        verbose_name="Fecha de Inicio"
    )
    # Término del curso; quitarlo impide conservar la duración planificada.
    fecha_termino = models.DateField(
        verbose_name="Fecha de Término"
    )
    # Capacidad máxima de la cohorte; no equivale al inventario disponible.
    cupos_totales = models.PositiveIntegerField(
        default=30,
        verbose_name="Límite Máximo de Cupos por Cohorte"
    )
    # Inventario de cupos libres consultado por la lógica de reserva y pago.
    cupos_disponibles = models.PositiveIntegerField(
        default=30,
        verbose_name="Cupos Disponibles para Reserva"
    )
    # URL opcional del banner; el valor vacío evita exigir una imagen para publicar.
    imagen_url = models.CharField(
        max_length=300,
        blank=True,
        default='',
        verbose_name="URL de Imagen o Banner"
    )
    # Publica u oculta el curso sin eliminarlo ni sus relaciones.
    activo = models.BooleanField(
        default=True,
        verbose_name="Publicado en Catálogo"
    )
    # Fecha de creación automática; quitarla elimina la marca temporal de registro.
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Registro"
    )

    class Meta:
        # Nombre explícito de tabla para el esquema de la aplicación.
        db_table = 'edtech_curso'
        # Etiquetas de administración.
        verbose_name = 'Curso / Bootcamp'
        verbose_name_plural = 'Cursos y Bootcamps'
        # Orden cronológico y luego alfabético en consultas sin orden explícito.
        ordering = ['fecha_inicio', 'titulo']

    def __str__(self):
        # Muestra título, modalidad legible y costo al representar un curso.
        return f"{self.titulo} - {self.get_modalidad_display()} (${self.costo_matricula})"

    @property
    def tiene_cupos(self):
        """Señala disponibilidad positiva; quitarla elimina el acceso uniforme a esta regla."""
        return self.cupos_disponibles > 0


# =====================================================================
# BLOQUE 4: CARRO DE MATRÍCULA PERSISTENTE (RELACIÓN 1 A 1 CON USUARIO)
# =====================================================================
class CarroMatricula(models.Model):
    """
    Carro de Matrícula Persistente en Base de Datos.
    Cumple con el Criterio 2 y Especificación C de la pauta:
    - Relación 1 a 1 entre el Usuario y su Carro activo en BD.
    - Persiste en PostgreSQL aun cuando el estudiante cierre sesión (logout)
      o ingrese desde otro navegador/dispositivo.
    - NO descuenta cupos al agregar cursos; únicamente reserva intención de compra.
    
    Si este modelo no existiera o se usaran cookies de sesión, los ítems se
    perderían al expirar la sesión del navegador.
    """
    # Un usuario posee como máximo un carro; CASCADE elimina el carro al eliminar al propietario.
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carro_matricula',
        verbose_name="Estudiante Propietario"
    )
    # Marca la creación automática del carro.
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    # Actualiza la marca temporal en cada guardado; quitarla impide conocer la última modificación.
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )

    class Meta:
        # Nombre estable de tabla en la base de datos.
        db_table = 'edtech_carro_matricula'
        # Etiquetas visibles en la administración.
        verbose_name = 'Carro de Matrícula'
        verbose_name_plural = 'Carros de Matrícula'

    def __str__(self):
        # Identifica al dueño y el número actual de cursos del carro.
        return f"Carro de {self.usuario.username} ({self.items.count()} cursos)"

    @property
    def total(self):
        """Suma los precios actuales de los cursos; no reserva cupos ni congela precios."""
        return sum(item.curso.costo_matricula for item in self.items.select_related('curso').all())

    @property
    def total_items(self):
        """Cuenta los ítems del carro; quitarla elimina este acceso directo al conteo."""
        return self.items.count()


class ItemCarroMatricula(models.Model):
    """
    Ítem individual dentro del carro de matrícula persistente.
    Cumple la regla de negocio estricta:
    'El sistema no permite agregar el mismo curso dos veces al mismo carro activo'.
    Se implementa mediante restricción unique_together = ('carro', 'curso').
    
    Si se eliminara unique_together, un estudiante podría duplicar matrículas
    del mismo curso en su carro.
    """
    # Cada ítem depende de un carro; al borrarlo se eliminan sus ítems y related_name expone carro.items.
    carro = models.ForeignKey(
        CarroMatricula,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Carro Asociado"
    )
    # Referencia el curso; CASCADE elimina el ítem al borrar el curso, y related_name permite consultar carros.
    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name='items_en_carros',
        verbose_name="Curso / Bootcamp"
    )
    # Registra automáticamente cuándo se incorporó el curso al carro.
    fecha_agregado = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha en que se agregó"
    )

    class Meta:
        # Nombre de tabla usado por el esquema de persistencia.
        db_table = 'edtech_item_carro'
        # Etiquetas de administración.
        verbose_name = 'Ítem de Carro de Matrícula'
        verbose_name_plural = 'Ítems de Carro de Matrícula'
        # Restricción de base de datos: impide repetir un curso en el mismo carro.
        unique_together = ('carro', 'curso')

    def __str__(self):
        # Expone qué curso y propietario corresponden a este ítem.
        return f"{self.curso.titulo} en carro de {self.carro.usuario.username}"


# =====================================================================
# BLOQUE 5: MATRÍCULA HISTÓRICA, ESTADOS Y CONTROL TRANSACCIONAL
# =====================================================================
class Matricula(models.Model):
    """
    Registro histórico de la Orden de Matrícula / Transacción.
    Cumple el Criterio D y Criterio 4 de la pauta:
    - Generada al realizar el Checkout desde el carro.
    - Estados explícitos mediante propiedad CHOICES:
      PENDIENTE -> PAGADO -> COMPLETADO (o CANCELADO).
    - Descuento de inventario: El stock o cupo NO se descuenta al agregar al carro,
      sino exactamente al pasar a PAGADO.
    - Reposición automática: Si la matrícula se actualiza a CANCELADO,
      el cupo se devuelve inmediatamente al catálogo para que otro estudiante pueda inscribirse.
    - Emisión de código único de transacción mediante UUID.
    
    Si se eliminara la propiedad CHOICES, se permitirían estados inconsistentes
    violando las reglas de la máquina de estados.
    """
    class EstadoMatriculaChoices(models.TextChoices):
        # Estados admitidos por el campo estado y sus etiquetas legibles.
        PENDIENTE = 'PENDIENTE', 'Pendiente de Pago'
        PAGADO = 'PAGADO', 'Pagado'
        COMPLETADO = 'COMPLETADO', 'Completado'
        CANCELADO = 'CANCELADO', 'Cancelado'

    # Identificador aleatorio no editable y único; quitar unique permitiría colisiones entre órdenes.
    codigo_transaccion = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="Código Único de Transacción (UUID)"
    )
    # Propietario de la orden; CASCADE elimina sus matrículas al borrar el usuario.
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='matriculas',
        verbose_name="Estudiante"
    )
    # Total monetario de la orden; Decimal y dos decimales evitan errores binarios de punto flotante.
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Monto Total Pagado ($CLP)"
    )
    # Limita los estados y fija el estado inicial al crear órdenes sin valor explícito.
    estado = models.CharField(
        max_length=20,
        choices=EstadoMatriculaChoices.choices,
        default=EstadoMatriculaChoices.PAGADO,
        verbose_name="Estado de la Transacción"
    )
    # Marca la fecha automática de creación de la orden.
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y Hora de Checkout"
    )
    # Se renueva al guardar cambios; permite rastrear actualizaciones del estado.
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización de Estado"
    )

    class Meta:
        # Nombre explícito de tabla.
        db_table = 'edtech_matricula'
        # Etiquetas de administración.
        verbose_name = 'Matrícula'
        verbose_name_plural = 'Matrículas'
        # Presenta primero las matrículas recientes en consultas sin orden propio.
        ordering = ['-fecha_creacion']

    def __str__(self):
        # Resume código, estudiante y estado legible de la transacción.
        return f"Matrícula {self.codigo_transaccion} - {self.estudiante.username} [{self.get_estado_display()}]"


# =====================================================================
# BLOQUE 6: INSCRIPCIONES OFICIALES Y TICKETS CON UUID ÚNICO
# =====================================================================
class DetalleMatricula(models.Model):
    """
    Inscripción oficial del estudiante a cada curso adquirido.
    Genera un ticket o entrada única mediante UUID para cada curso matriculado,
    cumpliendo con el requerimiento de la defensa oral:
    'emisión de entradas únicas (UUID)'.
    
    Si este modelo se elimina, no se tendría detalle de qué cursos formaron
    parte de una matrícula histórica consolidada.
    """
    # Orden que agrupa esta inscripción; CASCADE elimina sus detalles al borrar la matrícula.
    matricula = models.ForeignKey(
        Matricula,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Orden de Matrícula"
    )
    # Curso inscrito; PROTECT impide borrar cursos referenciados por inscripciones históricas.
    curso = models.ForeignKey(
        Curso,
        on_delete=models.PROTECT,
        related_name='inscripciones_oficiales',
        verbose_name="Curso Matriculado"
    )
    # Conserva el precio cobrado en esta compra aunque luego cambie el precio del curso.
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio al Momento de la Compra"
    )
    # Ticket no editable con identificador UUID globalmente único para cada inscripción.
    codigo_ticket = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="Código de Ticket / Inscripción Única (UUID)"
    )
    # Fecha automática de formalización de la inscripción.
    fecha_inscripcion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha Oficial de Inscripción"
    )

    class Meta:
        # Nombre estable de tabla en el esquema.
        db_table = 'edtech_detalle_matricula'
        # Etiquetas de administración.
        verbose_name = 'Inscripción Oficial'
        verbose_name_plural = 'Inscripciones Oficiales'

    def __str__(self):
        # Identifica ticket, curso y estudiante para facilitar su lectura.
        return f"Ticket {self.codigo_ticket} - {self.curso.titulo} ({self.matricula.estudiante.username})"
