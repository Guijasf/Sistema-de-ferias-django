# ferias/admin.py

from django.contrib import admin
from .models import PerfilUsuario, PeriodoAquisitivo, SolicitacaoFerias, DescontoFerias

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'matricula', 'cargo', 'secretaria', 'lotacao', 'gestor', 'data_contratacao', 'onboarding_completo')
    list_filter = ('secretaria', 'cargo', 'lotacao', 'onboarding_completo')
    search_fields = ('user__username', 'user__first_name', 'matricula', 'cargo')
    autocomplete_fields = ('user', 'gestor')
    
    # Faz o campo de gestor (que aponta para 'self') ser um dropdown de busca
    # muito mais rápido do que um dropdown padrão
    raw_id_fields = ('gestor',) 

@admin.register(PeriodoAquisitivo)
class PeriodoAquisitivoAdmin(admin.ModelAdmin):
    list_display = ('perfil', 'data_inicio_aquisitivo', 'data_fim_aquisitivo', 'dias_disponiveis', 'status')
    list_filter = ('status', 'perfil__secretaria')
    search_fields = ('perfil__user__username',)

@admin.register(SolicitacaoFerias)
class SolicitacaoFeriasAdmin(admin.ModelAdmin):
    list_display = ('solicitante', 'data_inicio', 'data_fim', 'status', 'aprovador_gestor')
    list_filter = ('status', 'solicitante__perfil__secretaria')
    search_fields = ('solicitante__username',)
    date_hierarchy = 'data_solicitacao'

@admin.register(DescontoFerias)
class DescontoFeriasAdmin(admin.ModelAdmin):
    list_display = ('solicitacao', 'periodo_aquisitivo', 'dias_descontados')