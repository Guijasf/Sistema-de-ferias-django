# ferias/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from dateutil.relativedelta import relativedelta

# =========================================================================
# 1. PERFIL DO USUÁRIO (O ANTIGO 'Funcionario', AGORA COM SEUS NOVOS CAMPOS)
# =========================================================================
class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    matricula = models.CharField(max_length=20, unique=True, null=True, blank=True)
    secretaria = models.CharField(max_length=100, null=True, blank=True)
    cargo = models.CharField(max_length=100, null=True, blank=True)
    data_contratacao = models.DateField(default=timezone.now)
    gestor = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='equipe')
    foto_perfil = models.ImageField(upload_to='fotos_perfil/', null=True, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def idade(self):
        if self.data_nascimento:
            hoje = timezone.now().date()
            return relativedelta(hoje, self.data_nascimento).years
        return None

# =========================================================================
# 2. PERÍODO AQUISITIVO (Onde o saldo é guardado)
# =========================================================================
class PeriodoAquisitivo(models.Model):
    STATUS_CHOICES = (
        ('ABERTO', 'Aberto'),
        ('FECHADO', 'Fechado'),
        ('VENCIDO', 'Vencido'),
    )
    
    perfil = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE, related_name='periodos_aquisitivos')
    data_inicio_aquisitivo = models.DateField()
    data_fim_aquisitivo = models.DateField()
    dias_direito = models.IntegerField(default=30)
    dias_disponiveis = models.IntegerField(default=30)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABERTO')

    def __str__(self):
        return f"{self.perfil.user.username} ({self.data_inicio_aquisitivo.year}) - Saldo: {self.dias_disponiveis}"

# =========================================================================
# 3. SOLICITAÇÃO DE FÉRIAS (Onde fica a "autenticação de 2 fatores")
# =========================================================================
class SolicitacaoFerias(models.Model):
    STATUS_CHOICES = (
        ('PENDENTE_GESTOR', 'Pendente (Gestor)'),
        ('PENDENTE_RH', 'Pendente (RH)'),
        ('APROVADA_FINAL', 'Aprovada'),
        ('REJEITADA', 'Rejeitada'),
    )

    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitacoes')
    data_inicio = models.DateField()
    data_fim = models.DateField()
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE_GESTOR')
    aprovador_gestor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='ferias_aprovadas_gestor')
    aprovador_rh = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='ferias_aprovadas_rh')
    data_aprovacao_gestor = models.DateTimeField(null=True, blank=True)
    data_aprovacao_rh = models.DateTimeField(null=True, blank=True)
    motivo_rejeicao = models.TextField(blank=True, null=True)
    
    periodos_utilizados = models.ManyToManyField(
        PeriodoAquisitivo,
        through='DescontoFerias',
        related_name='solicitacoes_descontadas'
    )
    
    @property
    def total_dias(self):
        # TODO: Implementar lógica de dias úteis aqui
        return (self.data_fim - self.data_inicio).days + 1

    def __str__(self):
        return f"{self.solicitante.username} - {self.data_inicio} a {self.data_fim} ({self.status})"

# =========================================================================
# 4. TABELA DE LIGAÇÃO (Para a regra dos 45 dias)
# =========================================================================
class DescontoFerias(models.Model):
    solicitacao = models.ForeignKey(SolicitacaoFerias, on_delete=models.CASCADE)
    periodo_aquisitivo = models.ForeignKey(PeriodoAquisitivo, on_delete=models.CASCADE)
    dias_descontados = models.IntegerField()

    class Meta:
        unique_together = ('solicitacao', 'periodo_aquisitivo')