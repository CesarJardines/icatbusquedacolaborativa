from django.db import models
#se importan el modelo Usuario que viene por defecto en Django
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
#se importa la zona horaria 
from django.utils import timezone 

class User(AbstractUser):
	es_estudiante = models.BooleanField(default=False)
	es_profesor = models.BooleanField(default=False)

	def __str__(self):
		return '{} {}'.format(self.last_name, self.first_name)

class Profesor(models.Model):
	user_profesor = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

class Grupo(models.Model):
	id_grupo = models.CharField(max_length=10, primary_key=True)
	nombre_grupo = models.CharField(max_length=100)
	materia = models.CharField(max_length=100, null=True, blank=True)
	institucion = models.CharField(max_length=100, null=True, blank=True)

	profesor_grupo = models.ForeignKey(Profesor, on_delete=models.CASCADE)

	def __str__(self):
		return f'Nombre: {self.nombre_grupo} Código:{self.id_grupo}'

class Estudiante(models.Model):
	user_estudiante = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
	grupos_inscritos = models.ManyToManyField(Grupo, blank=True)

	def __str__(self):
		user = User.objects.get(id=self.user_estudiante.id)
		return '{} {}'.format(user.last_name, user.first_name)

class Tema(models.Model):
	id_tema = models.AutoField(primary_key=True)
	nombre_tema = models.CharField(max_length=100)

	profesor_tema = models.ForeignKey(Profesor, on_delete=models.CASCADE)

	def __str__(self):
		return '{}'.format(self.nombre_tema)

class Equipo(models.Model):
	id_equipo = models.AutoField(primary_key=True)
	nombre_equipo = models.CharField(max_length=100)

	grupo_equipo = models.ForeignKey(Grupo, on_delete=models.CASCADE)
	estudiantes = models.ManyToManyField(Estudiante, blank=True)
	temas_asignados = models.ManyToManyField(Tema, blank=True)

	def __str__(self):
		return '{}'.format(self.nombre_equipo)
		
class DefinirProblema(models.Model):
	id_definirProb = models.AutoField(primary_key=True)
	preguntas_secundarias = models.IntegerField(default=1)
	fuentes = models.IntegerField(default=1)

	retro_inicial = models.TextField(null=True)
	retro_secundarias = models.TextField(null=True)

	equipo_definirProb = models.ForeignKey(Equipo, on_delete=models.CASCADE)
	tema_definirProb = models.ForeignKey(Tema, on_delete=models.CASCADE)

	paso = models.IntegerField(default=1)


class ParticipacionEst(models.Model):
	id_actividad = models.AutoField(primary_key=True)
	fecha = models.DateTimeField(default = timezone.now)
	contenido = models.TextField(null=True)
	estudiante_part = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='post')

	def __str__(self):
		return '{}'.format(self.contenido)

class Pregunta(models.Model):
	id_pregunta = models.OneToOneField(ParticipacionEst, on_delete=models.CASCADE, primary_key=True)
	INICIAL = 1
	SECUNDARIA = 2
	OTRO = 10
	TIPOS_PREGUNTA = (
		(INICIAL, 'inicial'),
		(SECUNDARIA, 'secundaria'),
		(OTRO, 'otro')
	)
	tipo_pregunta = models.PositiveSmallIntegerField(choices=TIPOS_PREGUNTA, default=10)
	votos = models.IntegerField(default=0)
	ganadora = models.BooleanField(default=False)
	
	definirProb_pregunta = models.ForeignKey(DefinirProblema, on_delete=models.CASCADE)

class ComentariosPreguntaInicial(models.Model):
	participacionEst = models.ForeignKey(ParticipacionEst, on_delete=models.CASCADE,null=True)
	pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE,null=True)

class EvaPreguntaSecundarias(models.Model):
	estudiante = models.ForeignKey(User,  on_delete=models.CASCADE)
	id_definirProb_pregunta = models.ForeignKey(DefinirProblema, on_delete=models.CASCADE)


class Fuente(models.Model):
	""" Modelo para la tabla fuente """

	TIPO_FUENTE_CHOISES = (
        ('0', 'LIBRO'),
        ('1', 'REVISTA'),
        ('2', 'PERIODICO'),
        ('3', 'SITIO WEB'),
        ('4', 'VIDEO'),
        ('5', 'IMAGEN')
    )
	TIPO_RECURSO_CHOISES = (
        ('0', 'ARCHIVO'),
        ('1', 'ENLACE'),
    )

	titulo = models.CharField('Título', max_length=60)
	autor = models.CharField('Autor', max_length=60,null=True)
	fecha_publicacion = models.DateField(null=True)
	lugar = models.CharField('Lugar de Publicación', max_length=60,null=True)
	tipo_fuente = models.CharField('Tipo de Fuente', max_length=1, choices=TIPO_FUENTE_CHOISES)
	tipo_recurso = models.CharField('Tipo de Recurso', max_length=1, choices=TIPO_RECURSO_CHOISES)
	enlace = models.CharField('Enlace', max_length=120)
	#estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
	id_defproblema = models.ForeignKey(DefinirProblema, on_delete=models.CASCADE,null=True)
	votos = models.IntegerField(default=0)
	ganadora = models.BooleanField(default=False)
	def __str__(self):
		return str(self.titulo) + ' - ' + self.autor

class FuentesSeleccionadas(models.Model):
	id_estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='estudiante')
	id_defproblema = models.ForeignKey(DefinirProblema, on_delete=models.CASCADE, related_name='definirproblema')
	id_fuente = models.ForeignKey(Fuente, on_delete=models.CASCADE, related_name='fuente')

class EvaluacionFuentesSel(models.Model):
	comentario = models.TextField(null=True)
	id_fuente = models.ForeignKey(Fuente, on_delete=models.CASCADE,null=True)
	id_estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='estudianteEvFuente', null=True)
	id_defproblema = models.ForeignKey(DefinirProblema, on_delete=models.CASCADE, related_name='definirproblemaEvFuente',null=True)

