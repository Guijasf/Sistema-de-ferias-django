# ferias/urls.py

from django.urls import path
from . import views

app_name = 'ferias' # Garante que o 'ferias:ver_perfil' funcione

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    path('perfil/', views.ver_perfil, name='ver_perfil'),
    
    # A LINHA QUE FALTAVA (E CAUSOU O ERRO):
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    
    path('solicitar/', views.solicitar_ferias, name='solicitar_ferias'),
    path('gestao/', views.dashboard_gestor, name='dashboard_gestor'),
    path('gestao/aprovar/<int:pk>/', views.aprovar_solicitacao, name='aprovar_solicitacao'),
    path('gestao/rejeitar/<int:pk>/', views.rejeitar_solicitacao, name='rejeitar_solicitacao'),
    path('tema/<str:tema>/', views.definir_tema, name='definir_tema'),
    path('api/eventos/', views.api_eventos_ferias, name='api_eventos'),
    path('calendario/', views.calendario_ferias, name='calendario'),
]