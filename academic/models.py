import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

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
        ESTUDIANTE = 'ESTUDIANTE', 'Estudiante'
        COORDINADOR = 'COORDINADOR', 'Coordinador Académico'

    rol = models.CharField(
        max_length=20,
        choices=RolChoices.choices,
        default=RolChoices.ESTUDIANTE,
        verbose_name="Rol del Usuario",
        help_text="Define los permisos y nivel de acceso en la plataforma EdTech"
    )
    rut = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="RUT / Identificación"
    )
    telefono = models.CharField(
        max_length=25,
        blank=True,
        null=True,
        verbose_name="Teléfono de Contacto"
    )

    class Meta:
        db_table = 'edtech_usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.username} [{self.get_rol_display()}]"

    @property
    def is_estudiante(self):
        """Retorna True si el usuario tiene rol de Estudiante."""
        return self.rol == self.RolChoices.ESTUDIANTE

    @property
    def is_coordinador(self):
        """Retorna True si el usuario tiene rol de Coordinador Académico o es superusuario."""
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
    nombre = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Nombre del Área",
        help_text="Ej: Desarrollo Web & Cloud, Inteligencia Artificial, Ciberseguridad"
    )
    descripcion = models.TextField(
        blank=True,
        default='',
        verbose_name="Descripción del Área"
    )
    icono = models.CharField(
        max_length=50,
        default='bi-mortarboard',
        verbose_name="Ícono Bootstrap",
        help_text="Clase del ícono para renderizado frontend (ej. bi-code-slash, bi-shield-lock)"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Área Activa"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )

    class Meta:
        db_table = 'edtech_area'
        verbose_name = 'Área de Conocimiento'
        verbose_name_plural = 'Áreas de Conocimiento'
        ordering = ['nombre']

    def __str__(self):
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
        BOOTCAMP = 'BOOTCAMP', 'Bootcamp Intensivo'
        CURSO = 'CURSO', 'Curso Regular'
        TALLER = 'TALLER', 'Taller Especializado'

    titulo = models.CharField(
        max_length=200,
        verbose_name="Título del Curso / Bootcamp"
    )
    descripcion = models.TextField(
        verbose_name="Descripción del Programa y Objetivos"
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name='cursos',
        verbose_name="Área de Conocimiento"
    )
    modalidad = models.CharField(
        max_length=20,
        choices=ModalidadChoices.choices,
        default=ModalidadChoices.BOOTCAMP,
        verbose_name="Modalidad del Programa"
    )
    costo_matricula = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Costo de Matrícula ($CLP)"
    )
    fecha_inicio = models.DateField(
        verbose_name="Fecha de Inicio"
    )
    fecha_termino = models.DateField(
        verbose_name="Fecha de Término"
    )
    cupos_totales = models.PositiveIntegerField(
        default=30,
        verbose_name="Límite Máximo de Cupos por Cohorte"
    )
    cupos_disponibles = models.PositiveIntegerField(
        default=30,
        verbose_name="Cupos Disponibles para Reserva"
    )
    imagen_url = models.CharField(
        max_length=300,
        blank=True,
        default='',
        verbose_name="URL de Imagen o Banner"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Publicado en Catálogo"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Registro"
    )

    class Meta:
        db_table = 'edtech_curso'
        verbose_name = 'Curso / Bootcamp'
        verbose_name_plural = 'Cursos y Bootcamps'
        ordering = ['fecha_inicio', 'titulo']

    def __str__(self):
        return f"{self.titulo} - {self.get_modalidad_display()} (${self.costo_matricula})"

    @property
    def tiene_cupos(self):
        """Indica si el curso dispone de al menos un cupo libre."""
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
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carro_matricula',
        verbose_name="Estudiante Propietario"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )

    class Meta:
        db_table = 'edtech_carro_matricula'
        verbose_name = 'Carro de Matrícula'
        verbose_name_plural = 'Carros de Matrícula'

    def __str__(self):
        return f"Carro de {self.usuario.username} ({self.items.count()} cursos)"

    @property
    def total(self):
        """Calcula el costo acumulado de los cursos agregados al carro."""
        return sum(item.curso.costo_matricula for item in self.items.select_related('curso').all())

    @property
    def total_items(self):
        """Conteo de cursos agregados en el carro activo."""
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
    carro = models.ForeignKey(
        CarroMatricula,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Carro Asociado"
    )
    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name='items_en_carros',
        verbose_name="Curso / Bootcamp"
    )
    fecha_agregado = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha en que se agregó"
    )

    class Meta:
        db_table = 'edtech_item_carro'
        verbose_name = 'Ítem de Carro de Matrícula'
        verbose_name_plural = 'Ítems de Carro de Matrícula'
        unique_together = ('carro', 'curso')

    def __str__(self):
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
        PENDIENTE = 'PENDIENTE', 'Pendiente de Pago'
        PAGADO = 'PAGADO', 'Pagado'
        COMPLETADO = 'COMPLETADO', 'Completado'
        CANCELADO = 'CANCELADO', 'Cancelado'

    codigo_transaccion = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="Código Único de Transacción (UUID)"
    )
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='matriculas',
        verbose_name="Estudiante"
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Monto Total Pagado ($CLP)"
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoMatriculaChoices.choices,
        default=EstadoMatriculaChoices.PAGADO,
        verbose_name="Estado de la Transacción"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y Hora de Checkout"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización de Estado"
    )

    class Meta:
        db_table = 'edtech_matricula'
        verbose_name = 'Matrícula'
        verbose_name_plural = 'Matrículas'
        ordering = ['-fecha_creacion']

    def __str__(self):
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
    matricula = models.ForeignKey(
        Matricula,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Orden de Matrícula"
    )
    curso = models.ForeignKey(
        Curso,
        on_delete=models.PROTECT,
        related_name='inscripciones_oficiales',
        verbose_name="Curso Matriculado"
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio al Momento de la Compra"
    )
    codigo_ticket = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="Código de Ticket / Inscripción Única (UUID)"
    )
    fecha_inscripcion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha Oficial de Inscripción"
    )

    class Meta:
        db_table = 'edtech_detalle_matricula'
        verbose_name = 'Inscripción Oficial'
        verbose_name_plural = 'Inscripciones Oficiales'

    def __str__(self):
        return f"Ticket {self.codigo_ticket} - {self.curso.titulo} ({self.matricula.estudiante.username})"
