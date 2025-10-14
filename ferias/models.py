# ferias/models.py

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class Funcionario(models.Model):
    SETORES = (
        ('dev', 'Desenvolvimento'),
        ('rh', 'Recursos Humanos'),
        ('financeiro', 'Financeiro'),
        ('comercial', 'Comercial'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='funcionario')
    gestor = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='equipe')
    data_nomeacao = models.DateField(default=timezone.now)
    setor = models.CharField(max_length=20, choices=SETORES, default='dev')

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class PeriodoAquisitivo(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='periodos_aquisitivos')
    data_inicio = models.DateField()
    data_fim = models.DateField()
    saldo_dias = models.IntegerField(default=30)

    def __str__(self):
        return f"{self.funcionario.user.username} ({self.data_inicio.year}/{self.data_fim.year}) - Saldo: {self.saldo_dias}"

class SolicitacaoFerias(models.Model):
    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
    )

    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitacoes')
    data_inicio = models.DateField()
    data_fim = models.DateField()
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')
    aprovador = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='solicitacoes_aprovadas')
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    motivo_rejeicao = models.TextField(blank=True, null=True)
    dias_deduzidos = models.BooleanField(default=False)
    periodo_aquisitivo = models.ForeignKey(PeriodoAquisitivo, on_delete=models.PROTECT, related_name='solicitacoes_feitas')

    def __str__(self):
        return f"{self.solicitante.username} - {self.data_inicio} a {self.data_fim} ({self.status})"

    @property
    def total_dias(self):
        if self.data_inicio and self.data_fim:
            return (self.data_fim - self.data_inicio).days + 1
        return 0