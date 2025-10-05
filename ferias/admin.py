# ferias/admin.py

from django.contrib import admin
from .models import Funcionario, PeriodoAquisitivo, SolicitacaoFerias

@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'gestor', 'setor', 'data_nomeacao')
    list_filter = ('setor',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    autocomplete_fields = ('user', 'gestor')

@admin.register(SolicitacaoFerias)
class SolicitacaoFeriasAdmin(admin.ModelAdmin):
    list_display = ('solicitante', 'data_inicio', 'data_fim', 'status', 'periodo_aquisitivo')
    list_filter = ('status', 'data_inicio', 'solicitante__funcionario__setor')
    search_fields = ('solicitante__username',)
    date_hierarchy = 'data_solicitacao'

@admin.register(PeriodoAquisitivo)
class PeriodoAquisitivoAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'data_inicio', 'data_fim', 'saldo_dias')
    search_fields = ('funcionario__user__username',)