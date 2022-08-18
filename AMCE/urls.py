from django.contrib import admin
from django.urls import include, path
from AMCE.forms import CustomAuthForm
from django.contrib.auth import views as auth_views

#se agrega para heroku
#from django.conf import settings 
#from django.conf.urls.static import static

# Views
import AMCE.views as views

app_name = "AMCE"
urlpatterns = [
#URLS CRECIÓN DE TIPOS DE USUARIOS
path('estudiante/vistaEstudiante/', views.vistaAlumno, name = 'vistaAlumno'),
path('profesor/vistaProfesor/', views.vistaProfesor, name = 'vistaProfesor'),
# URLS COMPARTIDAS
path('', views.index, name = 'index'),
path('registro/', views.signup, name = 'signup'),
path('registro/estudiante/', views.EstSignup.as_view(), name='EstSignup'),
path('registro/profesor/', views.ProfSignup.as_view(), name='ProfSignup'),
# URLS ESTUDIANTE
path('estudiante/MisGrupos/', views.EstMisGrupos, name = 'EstMisGrupos'),
path('estudiante/InscribirGrupo/', views.EstInscribirGrupo, name = 'EstInscribirGrupo'),
path('estudiante/Grupo/<str:id_grupo>/', views.EstPaginaGrupo, name = 'EstPaginaGrupo'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/actividad/aviso', views.AvisoNoContinuar, name = 'AvisoNoContinuar'),

path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/', views.AnalisisPreguntaInicial, name = 'AnalisisPreguntaInicial'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntaInicial/', views.postPreguntaInicial, name = 'PreguntaInicial'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntaInicial/actividad/aviso', views.AvisoNoContinuarAnalisis, name = 'AvisoNoContinuarAnalisis'), 
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntaInicial/FeedPreguntaInicial/', views.feedPIHecha, name = 'feedPIHecha'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntaInicial/DefiniciónPreguntaInicial/', views.defPreguntaInicial, name = 'defPreguntaInicial'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntasSecundarias/', views.PreguntasSecundarias, name = 'PreguntasSecundarias'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntasSecundarias/actividad/aviso', views.PSAvisoNoContinuar, name = 'PSAvisoNoContinuar'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntasSecundarias/evaluación', views.EvaluacionPS, name = 'EvaluacionPS'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntasSecundarias/evaluación/evaluacionsecundarias', views.EvaluacionPreSec, name = 'EvaluacionPreSec'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntasSecundarias/evaluación/aviso', views.AvisoNoContinuarEvaPS, name = 'AvisoNoContinuarEvaPS'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntasSecundarias/evaluación/actividad/plandeevaluación', views.PlanDeInvestigacion, name = 'PlanDeInvestigacion'),


# URLS ESTUDIANTE Paso 2
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/fuentes', views.seleccionaFuentes, name = "seleccionFuentes"),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/<str:definirFuente>/nueva-fuente', views.FuenteCreateView.as_view(), name = 'CrearFuenteView'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/editar-fuente/<pk>', views.FuenteUpdateView.as_view(), name = 'FuenteUpdateView'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/eliminar-fuente/<pk>', views.FuenteDeleteView.as_view(), name = 'FuenteDeleteView'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/instrucciones-evaluar-fuentes', views.instuccionesNuevaFuente, name = 'instuccionesNuevaFuente'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/EvaluarFuentes', views.evaluarFuentes, name = "evaluarFuentes"),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/EvaluarFuentes/aviso', views.AvisoNoContinuarEvaFuentes, name = "AvisoNoContinuarEvaFuentes"),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/EvaluarFuentes/aviso2', views.AvisoNoContinuarEvaFuentes2, name = "AvisoNoContinuarEvaFuentes2"),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/EvaluarFuentes/PlanDeInvestigaciónPaso2', views.EvaluarFuentesPlanInvestigación, name = "EvaluarFuentesPlanInvestigación"),

# URLS PROFESOR
path('profesor/MisGrupos/', views.ProfMisGrupos, name = 'ProfMisGrupos'),
path('profesor/CrearGrupo/', views.ProfCrearGrupo, name = 'ProfCrearGrupo'),
path('profesor/Grupo/<str:id_grupo>/', views.ProfPaginaGrupo, name = 'ProfPaginaGrupo'),
path('profesor/Grupo/<str:id_grupo>/CrearEquipo/', views.ProfCrearEquipo, name = 'ProfCrearEquipo'),
path('profesor/Grupo/<str:id_grupo>/Equipo/<int:id_equipo>/', views.ProfPaginaEquipo, name = 'ProfPaginaEquipo'),
path('profesor/Grupo/<str:id_grupo>/AsignarTema/', views.ProfAsignarTemaGrupo, name = 'ProfAsignarTemaGrupo'),
path('profesor/Grupo/<str:id_grupo>/Tema/<int:id_tema>/', views.ProfTemaAsignado, name = 'ProfTemaAsignado'),
path('profesor/Grupo/<str:id_grupo>/Tema/<int:id_tema>/ProgresoGrupo', views.ProfProgresoGrupo, name = 'ProfProgresoGrupo'),
path('profesor/Grupo/<str:id_grupo>/Tema/<int:id_tema>/Equipo/<int:id_equipo>', views.ProfProgresoEquipo, name = 'ProfProgresoEquipo'),
path('profesor/Grupo/<str:id_grupo>/Tema/<int:id_tema>/Equipo/<int:id_equipo>/<int:paso>', views.ProfRetro, name = 'ProfRetro'),
path('profesor/MisTemas/', views.ProfMisTemas, name = 'ProfMisTemas'),
path('profesor/CrearTema/', views.ProfCrearTema, name = 'ProfCrearTema')
]

