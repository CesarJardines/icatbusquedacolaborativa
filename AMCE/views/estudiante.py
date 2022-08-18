from pickle import FALSE
from pyexpat import ParserCreate
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..forms import *
from django.contrib.auth import authenticate, login
from django.template import RequestContext
from django.contrib.auth.models import User
from django.views.generic import (CreateView, UpdateView, DeleteView)
from django.views.generic.edit import FormView
from ..models import *
from ..decorators import student_required
from django.urls import reverse
#se importa para aumentar el contador de votos en feed
from django.db.models import F
from django.conf import settings
from django.core.mail import send_mail
import datetime
#Para obtener el max de votos en una pregunta inicial
from django.db.models import Max
#para la bíusqueda de fuentes del paso 2
import requests
#redirect
from django.urls import reverse_lazy
from js.momentjs import moment
from django.utils.decorators import method_decorator
#para harcordear el json
import json


class EstSignup(CreateView):
	model = User
	form_class = EstSignupForm
	template_name = 'registration/signup_form.html'
	
	def get_context_data(self, **kwargs):
		kwargs['user_type'] = 'Estudiante'
		return super().get_context_data(**kwargs)

	def form_valid(self, form):
		user = form.save()
		login(self.request, user)
		return redirect('AMCE:EstMisGrupos')
		

@student_required
def vistaAlumno(request):
	current_user = get_object_or_404(User, pk=request.user.pk)
	#Comento esta linea porque me daba error sin saber el por qué
	#grupos_inscritos = Estudiante.objects.filter(user_estudiante=current_user.id).values_list('grupos_inscritos', flat=True)

	#Se agregan estas lineas con el fin de sustituir la linea de arriba 
	estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
	#Consultamos todos grupos a los cual el usuario estudiante está inscrito y los mostramos
	grupos_inscritos = estudiante.grupos_inscritos.all()

	return render(request,"estudiante/MisGrupos.html", {'grupos_inscritos':grupos_inscritos})

@student_required
@login_required
def EstInscribirGrupo(request):
	'''
	Función para que un usuario alumno pueda inscribir una matería dado un código de clase
	por parte del profesor 
	'''
	current_user = get_object_or_404(User, pk=request.user.pk)
	grupos_inscritos = Estudiante.objects.filter(user_estudiante=request.user.pk)
	
	if request.method == 'POST':
		form = FormInscribirGrupo(request.POST)
		if form.is_valid():
			repetido = Estudiante.objects.filter(user_estudiante=current_user.id, grupos_inscritos=form.cleaned_data['codigo'])
			codigo = form.cleaned_data['codigo']
			try:
				if repetido.exists():
					messages.success(request, 'Ya estás inscrito en el grupo con código ' + codigo)
					return redirect(to="AMCE:EstMisGrupos")
				else:
					grupo = Grupo.objects.get(id_grupo=codigo)
					grupo_a_inscribir= Estudiante(user_estudiante_id=current_user.id)
					grupo_a_inscribir.grupos_inscritos.add(grupo.id_grupo)
					grupo_a_inscribir.save()
					messages.success(request, 'Grupo inscrito')
					return redirect(to="AMCE:EstMisGrupos")
			except Grupo.DoesNotExist:
				messages.error(request, 'El código de grupo que ingresaste no es válido')
				return redirect(to="AMCE:EstMisGrupos")
	else:
		form = FormInscribirGrupo()

	return render(request, 'estudiante/InscribirGrupo.html', {'form': form})

@student_required
@login_required
def EstMisGrupos(request):
	'''
	Función la cual muestra al usuario alumno los grupos a los cuales está inscrito  
	'''
	current_user = get_object_or_404(User, pk=request.user.pk)
	#Obtenemos el objeto estudiante actual
	estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
	#Consultamos todos grupos a los cual el usuario estudiante está inscrito y los mostramos
	grupos_inscritos = estudiante.grupos_inscritos.all()

	return render(request,"estudiante/MisGrupos.html",{'grupos_inscritos':grupos_inscritos})

@student_required
@login_required
def EstPaginaGrupo(request, id_grupo):
	'''
	Función la cual muestra los temas asignados al equipo del usuario.
	Un usuario debe de tener un equipo pero este puede ser diferente para cada tema, lo que se hace es que 
	se haga una búsqueda que llegue hasta la tabla Asignar, la cual muestra que equipos (id) tienen el tema (id)
	Args:
		id_grupo (char): código de la materia 
	'''
	#Se verifica que el usuario tenga equipo
	try:
		current_user = get_object_or_404(User, pk=request.user.pk)
		#Se obtiene el objeto Equipo de nuestro actual estudiante
		print("current_user", current_user)
		equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
		print("equipo", equipo)
		#Consultamos los temas asigandos que tiene el equipo del usuario y los filtramos por materia 
		temas_asignados = equipo.temas_asignados.filter()
		print("temas_asignados", temas_asignados[0].id_tema)
		#Consultamos e identificamos el grupo actual para mostrar los datos de grupo y materia en el header 
		grupo = Grupo.objects.filter(id_grupo = id_grupo)
	#De no tener equipo se le notifica que aún no tiene equipo
	except Equipo.DoesNotExist:
		messages.error(request, 'Aún no tienes equipo, espera a que tu profesor te asigne uno.')
		return redirect('AMCE:EstMisGrupos')
	

	return render(request, 'estudiante/PaginaGrupo.html', {'grupo':grupo.first(),'id_grupo':id_grupo ,'temas_asignados':temas_asignados})	

@student_required
@login_required
def AvisoNoContinuar(request, id_tema, id_grupo):
	'''
	Funcion para mostrar el aviso de que el equipo aún no acaba esta parte
	'''
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#obtengo todos los integrantes del equipo con ese id_equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo).values_list('estudiantes', flat=True)
	#Se consulta el equipo actual del usuario para pasarselo como parámetro en defProbPreguntaQuery
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema

	#Por cada integrante del equipo se va a buscar su participación de la PI
	for i in integrantesEquipo:
		#Si se encuentra la participación de un usuario no pasa nada
		try:
			obj = Pregunta.objects.get(id_pregunta__estudiante_part=i, definirProb_pregunta_id=defProbPreguntaQuery, tipo_pregunta=1)
		#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
		except Pregunta.DoesNotExist:
			#Obtenemos el id para posteriormente usar el nombre del usuario en el cuerpo del mensaje
			obj2 = User.objects.get(id=i)
			send_mail(
    		'Aviso, Faltas tu!',
    		f'Hola {obj2.first_name}, tu equipo ya realizó la actividad de formular la pregunta inicial del tema {temaNombre}, faltas tu! Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.',
    		settings.EMAIL_HOST_USER,
    		[obj2.email],
    		fail_silently=False,
			)
	
	return render(request, 'estudiante/AvisoNoContinuar.html', {'id_tema':id_tema, 'id_grupo':id_grupo})

@student_required
@login_required
def postPreguntaInicial(request, id_tema ,id_grupo):
	'''
	Función la cual habilita que un usuario pueda ingresar una función principal mediante un form.

	Args:
		tema (string): El tema asignado de la pregunta inicial

		codigo (string): codigo de la materia 
	
	'''
	#Consulta para obtener el tema de la actividad asignada y mostrarla en el template, así como usarla en defProbPreguntaQuery
	temaPreguntaInicial = Tema.objects.get(id_tema=id_tema)
	current_user = get_object_or_404(User, pk=request.user.pk)
	#Se consulta el equipo actual del usuario para pasarselo como parámetro en defProbPreguntaQuery
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = temaPreguntaInicial.id_tema)
	#Obtenemos todas las participaciones del equipo de nuestro actual usuario (AGREGAR CÓMO PARÁMETRO 1 COMO PREGUNTA INICIAL)
	numTotalPartici = Pregunta.objects.filter(definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo_pregunta=1)
	#Obtenemos los integrantes del  equipo (ARREGLAR ESTO)
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)

	#Se obtienen los ids del usuario actual 
	idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)
	#Se obtienen los id's de id_pregunta del numTotalPartici que asocia al equipo del actual estudiante y el del tema asignado
	idsUsuarioPregunta = numTotalPartici.values_list('id_pregunta', flat=True)
	#Verificamos para ver en qué paso se encuentra el equipo y redireccionarlo a la función correspondiente
	if defProbPreguntaQuery.paso == 1:
		#Se pregunta si el numero total de particiapciones con id_definirProb del equipo es igual al número de integrantes
		if numTotalPartici.count() == integrantesEquipo.count():
			#Si el numero de integrantes coincide con el número de participaciones entonces pasamos al siguente paso
			return redirect('AMCE:AnalisisPreguntaInicial',id_grupo=id_grupo, id_tema=id_tema)
			#Si no lo mandamos al modal de aviso 
		else:
			#Verificamos si hay una intersección entre los ids de participaciones del usuario con los ids de las preguntas asociadas a un id de DefinirPregunta
			if bool(set(idsUsuarioParticipacion)&set(idsUsuarioPregunta)):
				#Si hay un elemento en comun quiere decir que ya tiene su participación
				return redirect('AMCE:AvisoNoContinuar' , id_grupo=id_grupo, id_tema=id_tema)
			#Si no hay participación previa del usuario en este paso, quiere decir que no hay hecho este paso y se le permite hacerlo
			else:
				#Validación del forms de PreguntaInicial
				if request.method == 'POST':
					#Se captura la información proporcionada en el form del template
					form = PreguntaInicial(request.POST)
					if form.is_valid():
						#Creamos un elemento para nuestra tabla de actividad 
						nuevaParticipacion = ParticipacionEst(contenido = form.cleaned_data['contenido'],
													estudiante_part_id = current_user.id)
						messages.success(request, 'Pregunta inicial guardada')
						nuevaParticipacion.save()
						#De igual menera creamos un elemento del modelo Pregunta con el id_actividad que se acabó de crear con la variable nuevaParticipacion
						nuevoCampoPregunta = Pregunta(id_pregunta_id=nuevaParticipacion.id_actividad, tipo_pregunta=1, definirProb_pregunta_id=defProbPreguntaQuery.id_definirProb)
						nuevoCampoPregunta.save()

						#Participación actual del estudiante del tema actual para verificar si es la uñtima participación que el equipo necesita para continuar con el sig paso
						par = Pregunta.objects.get(id_pregunta__estudiante_part_id = current_user.id ,definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo_pregunta=1)
						#Entero el cual define la ultima participación del equipo
						ultimaParticipacion = integrantesEquipo.count()-1
						try:
							#Si la participación que hizo el estudiante es la ultima participación que se espera, manda el correo
							if par == numTotalPartici[ultimaParticipacion]:
								print('manda correo')
								#Se les notifica a los integrantes del equipo que todos han acabado
								for i in integrantesEquipo:
									nombreUsuario = User.objects.get(id=i)
									send_mail(
									'Tu equipo ya acabó de formular la pregunta inicial!',
									f'Hola {nombreUsuario.first_name}, el último integrante de tu equipo ha terminado de formular la pregunta inicial del tema {temaPreguntaInicial.nombre_tema}. Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.',
									settings.EMAIL_HOST_USER,
									[nombreUsuario.email],
									fail_silently=False,
									)
						#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
						except IndexError:
							print('no se manda correo correo')
						#Se redirige a la pregunta inicial para que se valide si puede avanzar o no al siguente paso
						return redirect('AMCE:PreguntaInicial',id_grupo=id_grupo, id_tema=id_tema)
				else:
					form = PreguntaInicial()
	#Redireccionamos si el sistema encuentra que está en el paso dos
	if defProbPreguntaQuery.paso == 2:
		return redirect('AMCE:seleccionFuentes',id_grupo=id_grupo, id_tema=id_tema)
	return render(request, 'estudiante/PreguntaInicial.html', {'id_tema':id_tema,'id_grupo':id_grupo ,'temaPreguntaInicial':temaPreguntaInicial, 'form': form})

@student_required
@login_required
def AnalisisPreguntaInicial(request, id_tema ,id_grupo):
	#corroborar si ya comentaron las preguntas iniciales
	temaPreguntaInicial = Tema.objects.get(id_tema=id_tema)
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = temaPreguntaInicial.id_tema)
	numTotalPartici = Pregunta.objects.filter(definirProb_pregunta=defProbPreguntaQuery.id_definirProb)
	#integrantesEquipo = Equipo.objects.filter(estudiantes__grupos_inscritos=equipo.grupo_equipo_id, temas_asignados__id_tema=id_tema)
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)

	comentariosPregunta = ComentariosPreguntaInicial.objects.filter(pregunta__definirProb_pregunta = defProbPreguntaQuery).values_list('participacionEst_id', flat=True)
	#Se obtienen los ids del usuario actual 
	idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)
	#Si todos los integrantes retrolimentaron la pregunta inicial se redirecciona al siguente paso
	if comentariosPregunta.count() == integrantesEquipo.count():
		#Redireccionamos al usuario a la pantalla Definición de la Pregunta inicial
		return redirect('AMCE:defPreguntaInicial', id_grupo=id_grupo, id_tema=id_tema)
	else:
		print('ir a analisis pregunta inicial')
		#Se corrobora si ya tiene participación en la actividad
		if bool(set(idsUsuarioParticipacion)&set(comentariosPregunta)):
			#Si ya tiene una retroalimentación se le redireciona a la pantalla de No continuar
			return redirect('AMCE:AvisoNoContinuarAnalisis' , id_grupo=id_grupo, id_tema=id_tema)
	return render(request,"estudiante/Actividad.html", {'id_tema':id_tema, 'id_grupo':id_grupo})

@student_required
@login_required
def feedPIHecha(request, id_tema ,id_grupo):
	'''
	Esta es una de las dos funciones semejantes que se tienen en el views de estudiante, la unica diferencia que tienen 
	es que regresan un template diferente. Las funciones cuentan los integrantes del equipo del usuario actual relacionado al tema 
	de la pregunta inicial 
		Args:
		id_tema (string): El tema asignado de la pregunta inicial

		id_grupo (string): codigo de la materia 
	'''
	temaPreguntaInicial = Tema.objects.get(id_tema=id_tema)
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = temaPreguntaInicial.id_tema)
	numTotalPartici = Pregunta.objects.filter(definirProb_pregunta=defProbPreguntaQuery.id_definirProb)
	#integrantesEquipo = Equipo.objects.filter(estudiantes__grupos_inscritos=equipo.grupo_equipo_id, temas_asignados__id_tema=id_tema)
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	#Se hace una consulta para input text del template con atributo comentario, esto devuelve la lista con lo
	comentario = request.POST.getlist('comentario')
	#Se quitan los caracteres vacios
	respuesta = "".join(string for string in comentario if len(string) > 0)

	#Se obtienen los ids del usuario actual 
	idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)

	#Se obtienen los id's de ComentariosPreguntaInicial asociados al tema asignado y equipo del usuario. Sacamos las participacionEst_id y aplicamos intersección para revisar si ya hay una participación previa 
	preguntasIniUsuario = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, tipo_pregunta=1).values_list('id_pregunta', flat=True)
	#comentariosPregunta = ComentariosPreguntaInicial.objects.filter(pregunta__definirProb_pregunta = defProbPreguntaQuery).values_list('participacionEst_id', flat=True)


	#Se obtienen los id's de ComentariosPreguntaInicial asociados al tema asignado y equipo del usuario. Sacamos las participacionEst_id y aplicamos intersección para revisar si ya hay una participación previa 
	comentariosPregunta = ComentariosPreguntaInicial.objects.filter(pregunta__definirProb_pregunta = defProbPreguntaQuery).values_list('participacionEst_id', flat=True)
	print(comentariosPregunta)

	#Se verifica que numero total de comentarios con los ids de participaciones estudiantes sean las mismas a los integrantes, de serlo es porque todos comentarno una PI
	if comentariosPregunta.count() == integrantesEquipo.count():
		print(comentariosPregunta)
		print(integrantesEquipo.count())
		#Redireccionamos al usuario a la pantalla Definición de la Pregunta inicial
		return redirect('AMCE:defPreguntaInicial', id_grupo=id_grupo, id_tema=id_tema)
	else:
		#----------------------
		#Si faltan integrantes por retroalimentar la pregunta inicial, se verifica si ya retroalimentó anteriormente 
		if bool(set(idsUsuarioParticipacion)&set(comentariosPregunta)):
			#Si ya tiene una retroalimentación se le redireciona a la pantalla de No continuar
			return redirect('AMCE:AvisoNoContinuarAnalisis' , id_grupo=id_grupo, id_tema=id_tema)
		else:
			#Si no hay retroalimentación previa, se le permite entrar para que haga su retroalimentación
			if request.method == 'POST':
				#se captura el nombre de usuario por el cual se está votando
				voto = request.POST.get("voto")
				#comentario = request.POST.get("comentario")
				print(respuesta)
				print(voto)
				nuevaParticipacion = ParticipacionEst(contenido = respuesta,
														estudiante_part_id = current_user.id)
				nuevaParticipacion.save()
				id_PreguntaAsociadaAUsuario = Pregunta.objects.filter(id_pregunta__estudiante_part_id=voto, definirProb_pregunta=defProbPreguntaQuery).values_list('id_pregunta', flat=True)

				nuevoComentario = ComentariosPreguntaInicial(participacionEst_id = nuevaParticipacion.id_actividad, pregunta_id = id_PreguntaAsociadaAUsuario)
				nuevoComentario.save()
				#Se agrega voto y se agrega comentario a las respectivas celdas de la Bade de Datos
				voto_sumar = Pregunta.objects.filter(id_pregunta__estudiante_part_id=voto, definirProb_pregunta=defProbPreguntaQuery).update(votos=F('votos')+1)

				contador = 0
				for i in integrantesEquipo:
					try:
						#Obtenemos los usuarios que aún les falta su participación y se les manda correo
						if bool(set(idsParticipacionUsuarioN)&set(comentariosPregunta)):
							print()
					#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
					except:
						#Obtenemos el id para posteriormente usar el nombre del usuario en el cuerpo del mensaje
						print('todo está bien')
					#para cada integrante del equipo se verifican sus participaciones
					idsParticipacionUsuarioN = ParticipacionEst.objects.filter(estudiante_part=i).values_list('id_actividad', flat=True)
					print(idsParticipacionUsuarioN)
					print(comentariosPregunta)
					if bool(set(idsParticipacionUsuarioN)&set(comentariosPregunta)):
						print('entré al if')
						contador = contador + 1
						print('usuario')
						print(i)
						print('contador')
						print(contador)
		
					if contador == integrantesEquipo.count():
						print('se manda correo')
				messages.success(request, 'Comentario y voto guardado correctamente')
				return redirect('AMCE:feedPIHecha', id_grupo=id_grupo, id_tema=id_tema)
	return render(request, 'estudiante/FeedPreguntaInicialHecha.html', {'temaPreguntaInicial':temaPreguntaInicial, 'numTotalPartici':numTotalPartici})

@student_required
@login_required
def AvisoNoContinuarAnalisis(request, id_tema, id_grupo):
	'''
	Esta es una de las dos funciones semejantes que se tienen en el views de estudiante, la unica diferencia que tienen 
	es que regresan un template diferente. Las funciones cuentan los integrantes del equipo del usuario actual relacionado al tema 
	de la pregunta inicial 
		Args:
		tema (string): El tema asignado de la pregunta inicial

		codigo (string): codigo de la materia 
	'''
	current_user = get_object_or_404(User, pk=request.user.pk)
	#Se consulta el equipo actual del usuario para pasarselo como parámetro en defProbPreguntaQuery
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#obtengo todos los integrantes del equipo con ese id_equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo).values_list('estudiantes', flat=True)
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo, tema_definirProb_id = id_tema)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema

	#Se obtienen los ids del usuario actual 
	idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)
	#Se obtienen los id's de ComentariosPreguntaInicial asociados al tema asignado y equipo del usuario. Sacamos las participacionEst_id y aplicamos intersección para revisar si ya hay una participación previa 
	comentariosPregunta = ComentariosPreguntaInicial.objects.filter(pregunta__definirProb_pregunta = defProbPreguntaQuery).values_list('participacionEst_id', flat=True)
	
	#Por cada integrante del equipo se va a buscar su participación de la PI
	for i in integrantesEquipo:
		nombreUsuario = User.objects.get(id=i)
		#Si se encuentra la participación de un usuario no pasa nada
		#Se consulta integrante x integrante para ver si tiene participación 
		integranteN = ParticipacionEst.objects.filter(estudiante_part=i).values_list('id_actividad', flat=True)
		try:
			#Obtenemos los usuarios que aún les falta su participación y se les manda correo
			if not(bool(set(integranteN)&set(comentariosPregunta))):
				print('Manda correo a los que no han hecho la actividad')
				send_mail(
				'Aviso, Faltas tu!',
				f'Hola {nombreUsuario.first_name}, tu equipo ya terminó de evaluar la pregunta inicial del tema {temaNombre}, faltas tu! Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.',
				settings.EMAIL_HOST_USER,
				[nombreUsuario.email],
				fail_silently=False,
				)
		#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
		except:
			#Obtenemos el id para posteriormente usar el nombre del usuario en el cuerpo del mensaje
			print('todo está bien')
	#envioCorreo = envioCorreoAvisoNoContinuar()
	return render(request, 'estudiante/AnalisisAviso.html', {'id_tema':id_tema, 'id_grupo':id_grupo})

@student_required
@login_required
def defPreguntaInicial(request,  id_tema, id_grupo):
	'''
	Función que muestra el avance hasta el paso de evaluar la pregunta inicial, se regresa como contexto la pregunta inicial que más fue votada y 
	los comentarios a esa pregunta inicial más votada
		Args:
		id_tema (string): El id del tema asignado de la pregunta inicial

		id_grupo (string): El código de la materia 
	'''
	temaPreguntaInicial = Tema.objects.get(id_tema=id_tema)
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#obtenemos el equiopo y tema a los cuales se asocian 
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = temaPreguntaInicial.id_tema)

	#Preguntas iniciales del equipo
	pregunta = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery)

	#Obtenemos todas las participaciones del equipo de nuestro actual usuario 
	numTotalPartici = Pregunta.objects.filter(definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo_pregunta=2)

	#Se obtienen los ids de las participaciones del usuario actual 
	idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)
	#Se obtienen las preguntas secundarias para ver si se le redirecciona al paso de no continuar o seguir la actividad
	preguntasSecUsuario = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, tipo_pregunta=2).values_list('id_pregunta', flat=True)
	#Obtenemos los integrantes del  equipo 
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	#Comprobamos si tienen preguntas secundarias ya hechas
	noPreguntasSec = DefinirProblema.objects.get(equipo_definirProb_id= equipo.id_equipo, tema_definirProb_id =id_tema).preguntas_secundarias

	#Se obtienen los id's de ComentariosPreguntaInicial asociados al tema asignado y equipo del usuario. Sacamos las participacionEst_id y aplicamos intersección para revisar si ya hay una participación previa 
	preguntasIniUsuario = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, tipo_pregunta=1).values_list('id_pregunta', flat=True)
	print(preguntasIniUsuario)

	#Se pregunta si el numero total de particiapciones con id_definirProb del equipo es igual al número de integrantes
	if numTotalPartici.count() == (integrantesEquipo.count() * noPreguntasSec):
		#Si el numero de integrantes coincide con el número de participaciones entonces pasamos al siguente paso
		return redirect('AMCE:EvaluacionPS', id_grupo=id_grupo, id_tema=id_tema)
		#Si no lo mandamos al modal de aviso 
	else:
		#Si faltan integrantes por retroalimentar la pregunta inicial, se verifica si ya retroalimentó anteriormente 
		if bool(set(idsUsuarioParticipacion)&set(preguntasSecUsuario)):
			#Si ya tiene una retroalimentación se le redireciona a la pantalla de No continuar
			return redirect('AMCE:PSAvisoNoContinuar' , id_grupo=id_grupo, id_tema=id_tema)
		else:
			#Buscamos cual es la pregunta inicial con más votos, como lo ordena en orden ascendente, si por alguna razón hay un empate en votos de las PI se tomará la primera
			masVotada = pregunta.order_by('-votos')[0]
			#Actualizamos el campo ganadora a True a la pregunta inicial más votada
			preguntaGanadora = Pregunta.objects.filter(id_pregunta_id=masVotada.id_pregunta_id).update(ganadora=True)
			preguntaSel = Pregunta.objects.get(id_pregunta_id=masVotada.id_pregunta_id, definirProb_pregunta = defProbPreguntaQuery, ganadora=True)

			#Se obtienen los comentarios de la pregunta ganadora para mostrarlos en la pantalla de definición de la pregunta inicial
			comentariosPregunta = ComentariosPreguntaInicial.objects.filter(pregunta_id = masVotada)	
			

	return render(request, "estudiante/DefinicionPreguntaIncial.html",{'id_tema': id_tema, 'id_grupo':id_grupo, 'preguntaSel':preguntaSel, 'comentariosPregunta':comentariosPregunta})

@student_required
@login_required
def PreguntasSecundarias(request,  id_tema, id_grupo):
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	#Obtenemos todas las participaciones del equipo de nuestro actual usuario 
	numTotalPartici = Pregunta.objects.filter(definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo_pregunta=2)

	#Obtenemos los integrantes del  equipo
	integrantesEquipo = Equipo.objects.filter(estudiantes__grupos_inscritos=equipo.grupo_equipo_id, temas_asignados__id_tema=id_tema)

	#Se obtienen los ids de las participaciones del usuario actual 
	idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)
	#Se obtienen los id's de ComentariosPreguntaInicial asociados al tema asignado y equipo del usuario. Sacamos las participacionEst_id y aplicamos intersección para revisar si ya hay una participación previa 
	preguntasSecUsuario = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, tipo_pregunta=2 ).values_list('id_pregunta', flat=True)
	#Consulta para obtener la pregunta inicial ganadora y mostrala en el template
	pregunta = Pregunta.objects.get(definirProb_pregunta = defProbPreguntaQuery, ganadora=True)
	#Consutlar los id de los integrantes del equipo para mandar correo
	integrantesEquipoCorreo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	#Obtenemos el número de preguntas secundarias que tiene el tema del equipo
	noPreguntasSec = DefinirProblema.objects.get(equipo_definirProb_id= equipo.id_equipo,tema_definirProb_id = id_tema).preguntas_secundarias

	#Se pregunta si el numero total de particiapciones con id_definirProb del equipo es igual al número de integrantes
	if numTotalPartici.count() == (integrantesEquipo.count() * noPreguntasSec):
		#Si el numero de integrantes coincide con el número de participaciones entonces pasamos al siguente paso
		print(numTotalPartici.count())
		print(integrantesEquipo.count() * noPreguntasSec)
		return redirect('AMCE:EvaluacionPS', id_grupo=id_grupo, id_tema=id_tema)
		#Si no lo mandamos al modal de aviso 
	else:
		#Si faltan integrantes por retroalimentar la pregunta inicial, se verifica si ya retroalimentó anteriormente 
		if bool(set(idsUsuarioParticipacion)&set(preguntasSecUsuario)):
			#Si ya tiene una retroalimentación se le redireciona a la pantalla de No continuar
			return redirect('AMCE:PSAvisoNoContinuar' , id_grupo=id_grupo, id_tema=id_tema)
		else:
			if request.method == 'POST':
				comentario = request.POST.getlist('preguntaSecundaria')

				for i in comentario:
					#Creamos un elemento para nuestra tabla de actividad 
					nuevaParticipacion = ParticipacionEst(contenido = i,
															estudiante_part_id = current_user.id)
					nuevaParticipacion.save()
					#De igual menera creamos un elemento del modelo Pregunta con el id_actividad que se acabó de crear con la variable nuevaParticipacion
					nuevoCampoPregunta = Pregunta(id_pregunta_id=nuevaParticipacion.id_actividad, tipo_pregunta=2, definirProb_pregunta_id=defProbPreguntaQuery.id_definirProb)
					nuevoCampoPregunta.save()
					#Se redirige a la pregunta inicial para que se valide si puede avanzar o no al siguente paso
				#Participación actual del estudiante del tema actual para verificar si es la uñtima participación que el equipo necesita para continuar con el sig paso
				par = Pregunta.objects.filter(id_pregunta__estudiante_part_id = current_user.id ,definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo_pregunta=2)
				#Entero el cual define la ultima participación del equipo
				ultimaParticipacion = (integrantesEquipo.count() * noPreguntasSec)-1
				try:
					#Si la participación que hizo el estudiante es la ultima participación que se espera, manda el correo
					if par[noPreguntasSec-1] == numTotalPartici[ultimaParticipacion]:
						print('manda correo')
						#Se les notifica a los integrantes del equipo que todos han acabado
						for i in integrantesEquipoCorreo:
							nombreUsuario = User.objects.get(id=i)
							send_mail(
							'Tu equipo ya acabó de formular las preguntas secundaria!',
							f'Hola {nombreUsuario.first_name}, el último integrante de tu equipo ha terminado de formular las preguntas secundarias del tema {temaNombre}. Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.',
							settings.EMAIL_HOST_USER,
							[nombreUsuario.email],
							fail_silently=False,
							)
				#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
				except IndexError:
					print('no se manda correo correo')
				messages.success(request, 'Preguntas secundarias guardadas correctamente')
				return redirect('AMCE:PreguntasSecundarias',  id_grupo=id_grupo, id_tema=id_tema)


	return render(request, "estudiante/PreguntasSecundarias.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'range': range(noPreguntasSec), 'temaNombre':temaNombre, 'pregunta':pregunta, 'noPreguntasSec':noPreguntasSec})

@student_required
@login_required
def PSAvisoNoContinuar(request,  id_tema, id_grupo):
	current_user = get_object_or_404(User, pk=request.user.pk)
	#Se consulta el equipo actual del usuario para pasarselo como parámetro en defProbPreguntaQuery
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	#Obtenemos todas las participaciones del equipo de nuestro actual usuario 
	numTotalPartici = Pregunta.objects.filter(definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo_pregunta=2)
	#Obtenemos los integrantes del  equipo
	integrantesEquipo = Equipo.objects.filter(estudiantes__grupos_inscritos=equipo.grupo_equipo_id, temas_asignados__id_tema=id_tema)
	#Consulta para obtener los integrantes de equipo para mandar correo
	integrantesEquipoCorreo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Mandar correo a los que aún no tienen su participación de pregunta secundaria
	noPreguntasSec = DefinirProblema.objects.get(tema_definirProb_id = id_tema).preguntas_secundarias
	#Se pregunta si el numero total de particiapciones con id_definirProb del equipo es igual al número de integrantes
	if numTotalPartici.count() == (integrantesEquipo.count() * noPreguntasSec):
		#Si el numero de integrantes coincide con el número de participaciones entonces pasamos al siguente paso
		return redirect('AMCE:EvaluacionPS', id_grupo=id_grupo, id_tema=id_tema)
		#Si no lo mandamos al modal de aviso 

	print(integrantesEquipoCorreo)
	for i in integrantesEquipoCorreo:
		#Si se encuentra la participación de un usuario no pasa nada
		try:
			obj = Pregunta.objects.filter(id_pregunta__estudiante_part=i, definirProb_pregunta_id=defProbPreguntaQuery, tipo_pregunta=2)
			if not obj:
				#Obtenemos el id para posteriormente usar el nombre del usuario en el cuerpo del mensaje
				obj2 = User.objects.get(id=i)
				send_mail(
    			'Aviso, Faltas tu!',
    			f'Hola {obj2.first_name}, tu equipo ya realizó la actividad de formular las preguntas secundarias del tema {temaNombre}, faltas tu! Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.',
    			settings.EMAIL_HOST_USER,
    			[obj2.email],
    			fail_silently=False,
				)
		#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
		except Pregunta.DoesNotExist:
			print('se atrapó la excepción')
		
	return render(request, "estudiante/PSAvisoNoContinuar.html", {'id_tema':id_tema, 'id_grupo':id_grupo})


@student_required
@login_required
def AvisoNoContinuarEvaPS(request, id_tema, id_grupo):
	'''
	Esta es una de las dos funciones semejantes que se tienen en el views de estudiante, la unica diferencia que tienen 
	es que regresan un template diferente. Las funciones cuentan los integrantes del equipo del usuario actual relacionado al tema 
	de la pregunta inicial 
		Args:
		tema (string): El tema asignado de la pregunta inicial

		codigo (string): codigo de la materia 
	'''
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#obtengo todos los integrantes del equipo con ese id_equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo).values_list('estudiantes', flat=True)
	#Se consulta el equipo actual del usuario para pasarselo como parámetro en defProbPreguntaQuery
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Por cada integrante del equipo se va a buscar su participación de la PI
	hora = datetime.datetime.now()

	for i in integrantesEquipo:
		#Si se encuentra la participación de un usuario no pasa nada
		try:
			#Consultamos si existe una paritcipación del usuario relacionada al tema actual
			obj = EvaPreguntaSecundarias.objects.get(estudiante=i ,id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb)
			print(obj)
		#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
		except EvaPreguntaSecundarias.DoesNotExist:
			#Obtenemos el id para posteriormente usar el nombre del usuario en el cuerpo del mensaje
			obj2 = User.objects.get(id=i)
			send_mail(
			'Aviso, Faltas tu!',
			f'Hola {obj2.first_name}, tu equipo ya realizó la actividad de evaluar las preguntas secundarias del tema {temaNombre}, faltas tu! Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.\n {hora}',
			settings.EMAIL_HOST_USER,
			[obj2.email],
			fail_silently=False,
			)
	return render(request, 'estudiante/EvPsAvisoNoContinuar.html', {'id_tema':id_tema, 'id_grupo':id_grupo})



@student_required
@login_required
def EvaluacionPS(request,  id_tema, id_grupo):
	#corroborar que el numero de integrantes sea el numero de filter con defquerry 
	temaPreguntaInicial = Tema.objects.get(id_tema=id_tema)
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = temaPreguntaInicial.id_tema)
	#identificamos si existe la participación de un usuario
	participacionPSusuario = EvaPreguntaSecundarias.objects.filter(estudiante=current_user ,id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb)
	#identificamos las participaciones totales del equipo con el 
	participacionPSEquipo = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb)
	#si el usuario ya tiene un campo en EvaPreguntaSecundarias asociado a un definirproblema_id entonces ya hizo ese paso
	#integrantesEquipo = Equipo.objects.filter(estudiantes__grupos_inscritos=equipo.grupo_equipo_id, temas_asignados__id_tema=id_tema)
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)

	numTotalPartici = Pregunta.objects.filter(definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo_pregunta=2)
	noPreguntasSec = DefinirProblema.objects.get(equipo_definirProb_id= equipo.id_equipo, tema_definirProb_id = id_tema).preguntas_secundarias

	print(numTotalPartici.count())
	print(integrantesEquipo.count() * noPreguntasSec)

	#corroboramos si existe participación
	if participacionPSusuario.exists():
		#si existe verificamos si el numero total de integrantes del equipo es el numero total de participaciones con el defProbPreguntaQuery_id del equipo
		if participacionPSEquipo.count() == integrantesEquipo.count():
			#redireccionar a pantalla de no continuar Evaluación preguntas seundarias
			return redirect('AMCE:PlanDeInvestigacion', id_grupo=id_grupo, id_tema=id_tema)
		else:
			return redirect('AMCE:AvisoNoContinuarEvaPS', id_grupo=id_grupo, id_tema=id_tema)

	return render(request, "estudiante/1EvaluacionPreguntasSecundarias.html", {'id_tema':id_tema, 'id_grupo':id_grupo})

@student_required
@login_required
def EvaluacionPreSec(request,  id_tema, id_grupo):
	current_user = get_object_or_404(User, pk=request.user.pk)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	#Consulta para obtener la pregunta inicial ganadora y mostrala en el template
	pregunta = Pregunta.objects.get(definirProb_pregunta = defProbPreguntaQuery, ganadora=True, tipo_pregunta=1)
	#Consulta que identifica las preguntas secundarias del equipo actual con el tema actual
	preguntasSec = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, tipo_pregunta=2)
	print(defProbPreguntaQuery)
	#verificamos si hay participación del usuario
	preSec = EvaPreguntaSecundarias.objects.filter(estudiante=current_user, id_definirProb_pregunta=defProbPreguntaQuery)
	participacionPSusuario = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb)
	integrantesEquipo = Equipo.objects.filter(estudiantes__grupos_inscritos=equipo.grupo_equipo_id, temas_asignados__id_tema=id_tema)
	#Consulta para obtener los integrantes de equipo para mandar correo
	integrantesEquipoCorreo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	if preSec.exists():
		if participacionPSusuario.count() == integrantesEquipo.count():
			#redireccionar a pantalla de no continuar Evaluación preguntas seundarias
			return redirect('AMCE:PlanDeInvestigacion', id_grupo=id_grupo, id_tema=id_tema)
		else:
			return redirect('AMCE:AvisoNoContinuarEvaPS', id_grupo=id_grupo, id_tema=id_tema)
	else:
		#permitirle hacer el 
		print('aún no tienes participación')
		#Se hace un request POST para identificar que botón(me gusta, no me gusta, no le entiendo) selecciona el usuario 
		if request.method == 'POST':
			#definimos el numero de iteración del foorloop que lleva como tag name de nuestra template, esto para indetificar el botón que se está seleccinoando con valor 1 o -1
			numBoton = 1
			#iteramos el número de preguntas secundarias que el equipo debe de tener 
			for i in preguntasSec:
				#obtenemos el valor del botón que el usuario selecciona
				option = request.POST.get("options%s" % numBoton)
				numBoton = numBoton + 1
				print(i.id_pregunta)
				if option == '3':
					#se actualiza el valor a +1 en el campo votos
					i.votos = F('votos')+3
					i.save(update_fields=['votos'])
				elif option == '-2':
					#se actualiza el valor a -1 en el campo votos
					i.votos = (F('votos')-2)
					i.save(update_fields=['votos'])
				elif option == '-1':
					#se actualiza el valor a -1 en el campo votos
					i.votos = (F('votos')-1)
					i.save(update_fields=['votos'])
			nuevaPartPS = EvaPreguntaSecundarias(estudiante=current_user, id_definirProb_pregunta=defProbPreguntaQuery)
			nuevaPartPS.save() 
			#Obtenemos todas las participaciones del equipo de nuestro actual usuario
			numTotalPartici = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb)
			#Participación actual del estudiante del tema actual para verificar si es la uñtima participación que el equipo necesita para continuar con el sig paso
			par = EvaPreguntaSecundarias.objects.get(estudiante=current_user, id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb)
			#Entero el cual define la ultima participación del equipo
			ultimaParticipacion = integrantesEquipo.count()-1
			try:
				#Si la participación que hizo el estudiante es la ultima participación que se espera, manda el correo
				if par == numTotalPartici[ultimaParticipacion]:
					print('manda correo')
					#Se les notifica a los integrantes del equipo que todos han acabado
					for i in integrantesEquipoCorreo:
						nombreUsuario = User.objects.get(id=i)
						send_mail(
							'Tu equipo ya acabó de evaluar las preguntas secundarias!',
							f'Hola {nombreUsuario.first_name}, el último integrante de tu equipo ha terminado de evaluar la pregunta inicial del tema {temaNombre}. Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.',
							settings.EMAIL_HOST_USER,
							[nombreUsuario.email],
							fail_silently=False,
						)
			#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
			except IndexError:
				print('no se manda correo correo')

			messages.success(request, 'Evaluación guardada correctamente')
			#redireccionar a la misma función para evaluar si sigue o no
			return redirect('AMCE:EvaluacionPreSec', id_grupo=id_grupo, id_tema=id_tema)
	return render(request, "estudiante/2EvaluacionPreguntasSecundarias.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'temaNombre':temaNombre, 'pregunta':pregunta, 'preguntasSec':preguntasSec})

@student_required
@login_required
def PlanDeInvestigacion(request,  id_tema, id_grupo):
	#Consulta para obtener la pregunta inicial ganadora y mostrala en el template
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	pregunta = Pregunta.objects.get(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=1)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	noFuentes = DefinirProblema.objects.get(equipo_definirProb_id= equipo.id_equipo,tema_definirProb_id = id_tema).fuentes
	#Obtenemos los integrantes del  equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	#preguntasSec = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, tipo_pregunta=2).order_by('votos')
	'''
	for i in preguntasSec:
		if i.votos >= 2:
			i.ganadora = True
			i.save(update_fields=['ganadora'])
	'''
	#Se hace la consulta de las preguntas con más votos de manera ascendente
	preguntasSecGanadas = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, tipo_pregunta=2).order_by('-votos')
	participacionPasoDosEquipo = FuentesSeleccionadas.objects.filter(id_defproblema= defProbPreguntaQuery.id_definirProb)
	participacionPasoDos = FuentesSeleccionadas.objects.filter(id_defproblema= defProbPreguntaQuery.id_definirProb, id_estudiante=current_user.id)
	if participacionPasoDos.exists():
		if participacionPasoDosEquipo.count() == integrantesEquipo.count() * noFuentes:
			print("Todo el equipo completó el paso 1 y se actualiza la variable paso a 2")
			actualizacionPaso = DefinirProblema.objects.filter(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema).update(paso=2)
		return redirect('AMCE:seleccionFuentes',id_grupo=id_grupo, id_tema=id_tema)
	else:
		print("Todo bien y se muestra la página de PlanDeInvestigación")
	return render(request, "estudiante/PlanDeInvestigacion.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'temaNombre':temaNombre, 'pregunta':pregunta, 'preguntasSecGanadas':preguntasSecGanadas})

@student_required
def seleccionaFuentes(request, id_tema, id_grupo):
	current_user = get_object_or_404(User, pk=request.user.pk)
	estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Se consulta el equipo del usuario 
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	#Se consulta el número de fuentes que el profesor definió para el equipo/tema
	noFuentes = DefinirProblema.objects.get(equipo_definirProb_id= equipo.id_equipo,tema_definirProb_id = id_tema).fuentes
	#Se obtienen las fuentes relacionadas a mostrar en el paso de Evaluar las fuentes
	fuentesRelacionadas = FuentesSeleccionadas.objects.filter(id_defproblema= defProbPreguntaQuery.id_definirProb, id_estudiante = current_user.id)
	fuentesRelacionadasEquipo = FuentesSeleccionadas.objects.filter(id_defproblema= defProbPreguntaQuery.id_definirProb)
	#Obtenemos los integrantes del  equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	#Obtenemos todas las participaciones del equipo de nuestro actual usuario 
	numTotalPartici = FuentesSeleccionadas.objects.filter(id_defproblema = defProbPreguntaQuery)
	

	#Corrroboramos que ya hayan realizado este paso, si se cumple redireccionamos al siguiente paso
	if fuentesRelacionadasEquipo.count() == integrantesEquipo.count() * noFuentes:
		return redirect('AMCE:instuccionesNuevaFuente',id_grupo=id_grupo, id_tema=id_tema)
	#Si no
	else:
		if fuentesRelacionadas.count() == noFuentes:
			print("fuentesRelacionadas", fuentesRelacionadas)
			return redirect('AMCE:AvisoNoContinuarEvaFuentes',id_grupo=id_grupo, id_tema=id_tema)
		else:
			fuentes_creadas = []
			for x in fuentesRelacionadas:
				''''
				print("fuente seleccionada", x)
				print("id_fuente seleccionada", x.id_fuente.id)
				print()
				'''
				#Se agrega el id de nuestras fuentes creadas
				fuentes_creadas.append(x.id_fuente)

			#fuentes_creadas = Fuente.objects.filter(estudiante=estudiante, definirProb_fuentes_id=defProbPreguntaQuery)
			#print("---- fuentes_creadasr ----")
			#print(fuentes_creadas)
			elegidas = fuentes_creadas
			for fuente in fuentes_creadas:
				fuente.type_resource = tipoFuente(fuente.tipo_fuente)
			# APIKEY del servicio de google
			search_items = []
			if request.method == 'GET':
				search_items = []
				print("tipo get")
				API_KEY = "AIzaSyBqnJ74Q3Dq_Myj0YHdek-_diI_3Qr-FTA"
				# ID del motor de búsqueda personal que hayamos creado
				SEARCH_ENGINE_ID = "0f56893eb6c3e0fb9"

				# La búsqueda
				query = "qué es " + temaNombre
				page = 1
				#no de resultados que se desean
				start = (page - 1) * 10 + 1
				#URL con la cual se permitirá buscar en google con los filtros correspondientes 
				url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}&start={start}"

				data = requests.get(url).json()
				#print(data)
				#Se obtiene la lista de la búsqueda de google con los filtros correspondientes 
				search_items = data.get("items")
				print("seleccionar fuentes")
				return render(request, "estudiante/SeleccionFuentes.html",  {'elegidas': elegidas, 'search_items':search_items, 'id_tema':id_tema, 'id_grupo':id_grupo, 'noFuentes':noFuentes, 'temaNombre':temaNombre, 'definirFuente':defProbPreguntaQuery.id_definirProb})
			
			#convertimos el json a un diccionario
			#a = type(search_items) 
			#se recibe petición cuando presionas boton continuar al siguiente paso
			if request.method == 'POST':
				print("---- se hace post ---")
				#datos de fuentes sugeridas a guardar
				fuentes_a_guardar = request.POST.get('fuentes-preparadas')
				#print("fuentes_a_guardar", fuentes_a_guardar)
				fuentes_a_guardar = eval(fuentes_a_guardar)
				#print("fuentes_a_guardar", fuentes_a_guardar)
				for item in fuentes_a_guardar:
					item = eval(item)
					#print("x", x)
					print(item['title'])
					try:
						titulo = item["pagemap"]["metatags"][0]["title"]
					except KeyError:
						titulo = item["title"]
					try:
						fecha_publi = item["pagemap"]["metatags"][0]["citation_publication_date"]
					except KeyError:
						fecha_publi = "N/A"
					try:						
						autor = item["pagemap"]["metatags"][0]["author"]
					except KeyError:
						autor = "N/A"
					link = item["link"]
					lugar = "N/A"
					print('exito')
					print("Title:", titulo)
					print("fecha publicación:", fecha_publi)
					print("autor:", autor)
					print("link:", link)
					print("------------")
					fuenteCreada = False
					#si existe no hay necesidad de crear el objeto porque ya existe uno 
					try:
						#verificamos si ya existe una fuente seleccionada con el mismo titulo
						verificaFuente = Fuente.objects.get(titulo=titulo, id_defproblema = defProbPreguntaQuery)
						
					except Fuente.DoesNotExist:
						fuenteCreada = True
						print("se crea la fuente")
						nuevaFuente = Fuente(titulo=titulo,
											autor=autor, 
											fecha_publicacion= None, 
											lugar=lugar, 
											tipo_fuente=3, 
											tipo_recurso=1,
											enlace = link,
											id_defproblema = defProbPreguntaQuery
											)
						nuevaFuente.save()

						variable = FuentesSeleccionadas.objects.create(
							id_estudiante = estudiante,
							id_defproblema = defProbPreguntaQuery,
							id_fuente = nuevaFuente
						)
						variable.save()

					except IndexError:
						print('se atrapó la excepción')
					#si existe la fuente verifica si ya existe en el equipo
					if not fuenteCreada:
						variable = FuentesSeleccionadas.objects.create(
							id_estudiante = estudiante,
							id_defproblema = defProbPreguntaQuery,
							id_fuente = verificaFuente
						)
						variable.save()
						
				#aqui verificamos si es el ultimo participante por hacer la actividad
				#Participación actual del estudiante del tema actual para verificar si es la uñtima participación que el equipo necesita para continuar con el sig paso
				par = FuentesSeleccionadas.objects.filter(id_estudiante = estudiante , id_defproblema = defProbPreguntaQuery)
				#Entero el cual define la ultima participación del equipo
				ultimaParticipacion = (integrantesEquipo.count() * noFuentes)-1
				try:
					#Si la participación que hizo el estudiante es la ultima participación que se espera, manda el correo
					if par[noFuentes-1] == numTotalPartici[ultimaParticipacion]:
						print('manda correo')
						#Se les notifica a los integrantes del equipo que todos han acabado
						for i in integrantesEquipo:
							nombreUsuario = User.objects.get(id=i)
							send_mail(
							'Tu equipo ya acabó de seleccionar las fuentes!',
							f'Hola {nombreUsuario.first_name}, el último integrante de tu equipo ha terminado de seleccionar las fuentes del tema {temaNombre}. Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.',
							settings.EMAIL_HOST_USER,
							[nombreUsuario.email],
							fail_silently=False,
							)
				except IndexError:
					print('no se manda correo correo')
				print("Estoy en redirect", id_grupo, id_tema)
				messages.success(request, 'Fuentes elegidas guardadas correctamente')
				return HttpResponse(status=200)
		
			

def tipoFuente(x):
    return {
        '0': 'LIBRO',
        '1': 'REVISTA',
		'2': 'PERIODICO',
		'3': 'SITIO WEB',
		'4': 'VIDEO',
		'5': 'IMAGEN',
    }[x]

def seleccionaTipoFuente(request):
	return render(request, "estudiante/TipoFuente.html")

DECORATORS = [student_required, login_required]

@method_decorator(DECORATORS, name='dispatch')
class FuenteCreateView(FormView):
	template_name = 'estudiante/NuevaFuente.html'
	form_class = NuevaFuenteForm

	def form_valid(self, form):
		#fuente = form.save(commit=False)
		#fuente.save()
		equipo = Equipo.objects.get(estudiantes=self.estudiante, grupo_equipo=self.id_grupo)
		defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = self.id_tema)

		fuente = Fuente.objects.create(
			titulo = form.cleaned_data['titulo'],
			autor = form.cleaned_data['autor'],
			fecha_publicacion = form.cleaned_data['fecha_publicacion'],
			lugar = form.cleaned_data['lugar'],
			tipo_fuente = form.cleaned_data['tipo_fuente'],
			tipo_recurso = form.cleaned_data['tipo_recurso'],
			enlace = form.cleaned_data['enlace'],
			id_defproblema = defProbPreguntaQuery
			
		)
		fuente.save()
		

		#crear una instancia de FuentesSeleccionadas
		variable = FuentesSeleccionadas.objects.create(
			id_estudiante = self.estudiante,
			id_defproblema = defProbPreguntaQuery,
			id_fuente = fuente
		)

		return super(FuenteCreateView, self).form_valid(form)

	def get_form_kwargs(self, *args, **kwargs):
		form_kwargs = super(FuenteCreateView, self).get_form_kwargs(*args, **kwargs)
		current_user = get_object_or_404(User, pk=self.request.user.pk)
		self.estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
		self.definirProbFuente =  self.kwargs['definirFuente'] 
		self.id_tema = self.kwargs['id_tema']
		self.id_grupo = self.kwargs['id_grupo']
		self.success_url = reverse_lazy('AMCE:seleccionFuentes', kwargs={'id_grupo': self.kwargs['id_grupo'] ,'id_tema':self.kwargs['id_tema']})
		return form_kwargs


@method_decorator(DECORATORS, name='dispatch')
class FuenteUpdateView(UpdateView):
	template_name = 'estudiante/NuevaFuente.html'
	model = Fuente
	form_class = EditFuenteForm

	def form_valid(self, form):
		fuente = form.save(commit=False)
		fuente.estudiante = self.estudiante
		if(fuente.tipo_recurso == '0'):
			element = self.request.FILES['resourceFile']
			fuente.enlace = element.name
		fuente.save()
		return super(FuenteUpdateView, self).form_valid(form)

	def get_form_kwargs(self, *args, **kwargs):
		form_kwargs = super(FuenteUpdateView, self).get_form_kwargs(*args, **kwargs)
		current_user = get_object_or_404(User, pk=self.request.user.pk)
		self.estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
		self.success_url = reverse_lazy('AMCE:seleccionFuentes', kwargs={'id_grupo': self.kwargs['id_grupo'] ,'id_tema':self.kwargs['id_tema']})
		return form_kwargs


@method_decorator(DECORATORS, name='dispatch')
class FuenteDeleteView(DeleteView):
	model = Fuente
	template_name = "estudiante/EliminarFuente.html"

	def get_success_url(self, **kwargs):
		current_user = get_object_or_404(User, pk=self.request.user.pk)
		self.estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
		return reverse_lazy('AMCE:seleccionFuentes', kwargs={'id_grupo': self.kwargs['id_grupo'] ,'id_tema':self.kwargs['id_tema']})

def instuccionesNuevaFuente(request, id_tema, id_grupo):
	current_user = get_object_or_404(User, pk=request.user.pk)
	estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Se consulta el equipo del usuario 
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	#Consultamos las evaluaciones totales del equipo por el tema que están trabajando
	evaluacionesFuentes = EvaluacionFuentesSel.objects.filter(id_defproblema=defProbPreguntaQuery)
	fuentesRelacionadas = FuentesSeleccionadas.objects.filter(id_defproblema= defProbPreguntaQuery.id_definirProb, id_estudiante = current_user.id)
	fuentesRelacionadasEquipo = FuentesSeleccionadas.objects.filter(id_defproblema= defProbPreguntaQuery.id_definirProb)
	#Se consulta el número de fuentes que el profesor definió para el equipo/tema
	noFuentes = DefinirProblema.objects.get(equipo_definirProb_id= equipo.id_equipo,tema_definirProb_id = id_tema).fuentes
	#corroborar si todo el equipo ya evaluó las fuentes
	if integrantesEquipo.count() == evaluacionesFuentes.count():
		#Si sí pasa al fin paso 2
		return redirect('AMCE:EvaluarFuentesPlanInvestigación', id_grupo=id_grupo, id_tema=id_tema)
	else:
		if fuentesRelacionadas.exists():
			if fuentesRelacionadasEquipo.count() != integrantesEquipo.count() * noFuentes:
				return redirect('AMCE:AvisoNoContinuarEvaFuentes',id_grupo=id_grupo, id_tema=id_tema)	
		try:
			participacionEvaluacionesFuentes = EvaluacionFuentesSel.objects.get(id_defproblema=defProbPreguntaQuery, id_estudiante = estudiante)
			return redirect('AMCE:AvisoNoContinuarEvaFuentes2', id_grupo=id_grupo, id_tema=id_tema)
		except EvaluacionFuentesSel.DoesNotExist:
			print("hola")
	# si ya tiene participación pero su equipo aún no acaba entonces redirecionar al paso  
	return render(request, "estudiante/InstruccionesEvaluarFuentes.html", {'id_tema':id_tema, 'id_grupo':id_grupo })

def evaluarFuentes(request, id_tema, id_grupo):
	current_user = get_object_or_404(User, pk=request.user.pk)
	estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Se consulta el equipo del usuario 
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	#se obtiene unicamente los id de las fuentes, y hacemos el filtro por equipo, despues obtenemos los elementos distintos
	fuentesAEvaluarTemp = FuentesSeleccionadas.objects.values('id_fuente').filter(id_defproblema = defProbPreguntaQuery).distinct()
	fuentesEquipoSel = FuentesSeleccionadas.objects.filter(id_defproblema = defProbPreguntaQuery)
	noFuentes = DefinirProblema.objects.get(id_definirProb=defProbPreguntaQuery.id_definirProb).fuentes
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	"""
	idFuentesAgregadas = []
	fuentesAEvaluar = []
	for x in fuentesAEvaluarTemp:
		#Se agrega la fuente
		if(x.id_fuente.id not in idFuentesAgregadas):
			fuentesAEvaluar.append(x.id_fuente)
			idFuentesAgregadas.append(x.id_fuente.id)
	"""		
	fuentesAEvaluar = []
	for x in fuentesAEvaluarTemp:
		#print("valor de x",  x['id_fuente'])
		fuentesAEvaluar.append(Fuente.objects.get(id = x['id_fuente']))

	#Se verifica que todo el equipo haya seleccionado sus fuentes
	if fuentesEquipoSel.count() == (integrantesEquipo.count() * noFuentes):
		#aqui va el back para votar por la fuente
		if request.method == 'POST':
			#se captura el nombre de usuario por el cual se está votando
			voto = request.POST.get("voto")
			form = EvaluarFuente(request.POST)
			obtenIdFuente = Fuente.objects.get(id=voto)
			if form.is_valid():
				print("se guardó el contenido", form.cleaned_data['contenido'])
				nuevaEvaluacion = EvaluacionFuentesSel(comentario=form.cleaned_data['contenido'],
									id_defproblema=defProbPreguntaQuery,
									id_estudiante=estudiante,
									id_fuente_id = obtenIdFuente.id
				)
				nuevaEvaluacion.save()
				nuevoVoto = Fuente.objects.filter(id=voto).update(votos=F('votos')+1)

				#Verificamos si el usuario es el último integrante del equipo que faltaba por terminar el paso
				#Consulta para verificar
				par = EvaluacionFuentesSel.objects.get(id_defproblema = defProbPreguntaQuery, id_estudiante=current_user.id)
				#Entero el cual define la ultima participación del equipo
				ultimaParticipacion = integrantesEquipo.count()
				numTotalPartici = EvaluacionFuentesSel.objects.filter(id_defproblema = defProbPreguntaQuery)
				try:
					#Si la participación que hizo el estudiante es la ultima participación que se espera, manda el correo
					if par == numTotalPartici[ultimaParticipacion-1]:
						print('manda correo')
						#Se les notifica a los integrantes del equipo que todos han acabado
						for i in integrantesEquipo:
							nombreUsuario = User.objects.get(id=i)
							send_mail(
							'Tu equipo ya acabó de evaluar las fuentes!',
							f'Hola {nombreUsuario.first_name}, el último integrante de tu equipo ha terminado de evaluar las fuentes del tema {temaNombre}. Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.',
							settings.EMAIL_HOST_USER,
							[nombreUsuario.email],
							fail_silently=False,
							)
				#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
				except IndexError:
					print('no se manda correo correo')
				messages.success(request, 'Voto y comentario guardado correctamente')
				return redirect('AMCE:EvaluarFuentesPlanInvestigación', id_grupo=id_grupo, id_tema=id_tema)
		else:
			form = EvaluarFuente()
	else:
		return redirect('AMCE:AvisoNoContinuarEvaFuentes',id_grupo=id_grupo, id_tema=id_tema)
	
	return render(request, "estudiante/EvaluarFuentes.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'fuentesAEvaluar':fuentesAEvaluar, 'temaNombre':temaNombre, 'form':form})

@student_required
@login_required
def AvisoNoContinuarEvaFuentes(request, id_tema, id_grupo):
	'''
	Esta es una de las dos funciones semejantes que se tienen en el views de estudiante, la unica diferencia que tienen 
	es que regresan un template diferente. Las funciones cuentan los integrantes del equipo del usuario actual relacionado al tema 
	de la pregunta inicial 
		Args:
		tema (string): El tema asignado de la pregunta inicial

		codigo (string): codigo de la materia 
	'''
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#obtengo todos los integrantes del equipo con ese id_equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo).values_list('estudiantes', flat=True)
	#Se consulta el equipo actual del usuario para pasarselo como parámetro en defProbPreguntaQuery
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Por cada integrante del equipo se va a buscar su participación de la PI
	hora = datetime.datetime.now()
	
	
	for i in integrantesEquipo:
		#Si se encuentra la seleccion de fuentes de un usuario no pasa nada
		try:
			#Consultamos si existe una paritcipación del usuario relacionada al tema actual
			obj = FuentesSeleccionadas.objects.filter(id_defproblema= defProbPreguntaQuery.id_definirProb, id_estudiante = i)
			if not obj:
				#Obtenemos el id para posteriormente usar el nombre del usuario en el cuerpo del mensaje
				obj2 = User.objects.get(id=i)
				send_mail(
				'Aviso, Faltas tu!',
				f'Hola {obj2.first_name}, tu equipo ya realizó la actividad de seleccionar las fuentes del tema {temaNombre}, faltas tu! Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.\n {hora}',
				settings.EMAIL_HOST_USER,
				[obj2.email],
				fail_silently=False,
				)
		#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
		except EvaPreguntaSecundarias.DoesNotExist:
			print("todo bien")
	
	return render(request, 'estudiante/EvFuentesAvisoNoContinuar.html', {'id_tema':id_tema, 'id_grupo':id_grupo})

@student_required
@login_required
def AvisoNoContinuarEvaFuentes2(request, id_tema, id_grupo):
	'''
	Esta es una de las dos funciones semejantes que se tienen en el views de estudiante, la unica diferencia que tienen 
	es que regresan un template diferente. Las funciones cuentan los integrantes del equipo del usuario actual relacionado al tema 
	de la pregunta inicial 
		Args:
		tema (string): El tema asignado de la pregunta inicial

		codigo (string): codigo de la materia 
	'''
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#obtengo todos los integrantes del equipo con ese id_equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo).values_list('estudiantes', flat=True)
	#Se consulta el equipo actual del usuario para pasarselo como parámetro en defProbPreguntaQuery
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Por cada integrante del equipo se va a buscar su participación de la PI
	hora = datetime.datetime.now()
	
	for i in integrantesEquipo:
		#Si se encuentra la participación de un usuario no pasa nada
		try:
			#Consultamos si existe una paritcipación del usuario relacionada al tema actual
			obj = EvaluacionFuentesSel.objects.get(id_defproblema=defProbPreguntaQuery, id_estudiante = i)
			print(obj)
		#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
		except EvaluacionFuentesSel.DoesNotExist:
			#Obtenemos el id para posteriormente usar el nombre del usuario en el cuerpo del mensaje
			obj2 = User.objects.get(id=i)
			send_mail(
			'Aviso, Faltas tu!',
			f'Hola {obj2.first_name}, tu equipo ya realizó la actividad de evaluar las fuentes del tema {temaNombre}, faltas tu! Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.\n {hora}',
			settings.EMAIL_HOST_USER,
			[obj2.email],
			fail_silently=False,
			)
	
	return render(request, 'estudiante/EvFuentesAvisoNoContinuar2.html', {'id_tema':id_tema, 'id_grupo':id_grupo})

def EvaluarFuentesPlanInvestigación(request, id_tema, id_grupo):
	current_user = get_object_or_404(User, pk=request.user.pk)
	estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Se consulta el equipo del usuario 
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	#Consultamos las evaluaciones totales del equipo por el tema que están trabajando
	evaluacionesFuentes = EvaluacionFuentesSel.objects.filter(id_defproblema=defProbPreguntaQuery)
	#corroborar si todo el equipo ya evaluó las fuentes
	if integrantesEquipo.count() == evaluacionesFuentes.count():
		#Si sí pasa al fin paso 2
		print("Todo bien!")
		fuentesEquipo = Fuente.objects.filter(id_defproblema=defProbPreguntaQuery)
		for i in fuentesEquipo:
			if i.votos >= 1:
				i.ganadora = True
				i.save(update_fields=['ganadora'])
		fuentesEquipoGanadoras = Fuente.objects.filter(id_defproblema=defProbPreguntaQuery, ganadora = True)
		fuentesEquipoGanadoras2 = Fuente.objects.filter(id_defproblema=defProbPreguntaQuery, ganadora = True).values_list('id', flat=True)
		print("fuentes ganadoras 2", fuentesEquipoGanadoras2)
		ejemplo = EvaluacionFuentesSel.objects.filter(id_defproblema=defProbPreguntaQuery)
		print('ejemplo', ejemplo)

		
		
	else:
		return redirect('AMCE:AvisoNoContinuarEvaFuentes2', id_grupo=id_grupo, id_tema=id_tema)
	
		
		
	return render(request, "estudiante/EvFuPlanInvestigación.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'fuentesEquipoGanadoras':fuentesEquipoGanadoras, 'ejemplo':ejemplo})