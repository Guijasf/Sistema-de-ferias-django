# ferias/admin.py

from django.contrib import admin
# ALTERADO: Importamos os nossos novos modelos
from .models import PerfilUsuario, PeriodoAquisitivo, SolicitacaoFerias, DescontoFerias

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    # ATUALIZADO: Mostrando os novos campos do Perfil
    list_display = ('user', 'matricula', 'cargo', 'secretaria', 'gestor', 'data_contratacao')
    list_filter = ('secretaria', 'cargo')
    search_fields = ('user__username', 'user__first_name', 'matricula', 'cargo')
    autocomplete_fields = ('user', 'gestor')

@admin.register(PeriodoAquisitivo)
class PeriodoAquisitivoAdmin(admin.ModelAdmin):
    # ATUALIZADO: Mostrando os novos campos do Período
    list_display = ('perfil', 'data_inicio_aquisitivo', 'data_fim_aquisitivo', 'dias_disponiveis', 'status')
    list_filter = ('status', 'perfil__secretaria')
    search_fields = ('perfil__user__username',)

@admin.register(SolicitacaoFerias)
class SolicitacaoFeriasAdmin(admin.ModelAdmin):
    # ATUALIZADO: Mostrando o novo fluxo de status
    list_display = ('solicitante', 'data_inicio', 'data_fim', 'status', 'aprovador_gestor', 'aprovador_rh')
    list_filter = ('status', 'solicitante__perfil__secretaria')
    search_fields = ('solicitante__username',)
    date_hierarchy = 'data_solicitacao'

@admin.register(DescontoFerias)
class DescontoFeriasAdmin(admin.ModelAdmin):
    # NOVO: Um admin para a nossa tabela de ligação (para a regra dos 45 dias)
    list_display = ('solicitacao', 'periodo_aquisitivo', 'dias_descontados')