# ferias/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Funcionario, PeriodoAquisitivo, SolicitacaoFerias

# NOTA: Todos os sinais antigos que usavam SaldoFerias foram removidos.
# Nós vamos recriar a lógica para o novo sistema de PeriodoAquisitivo
# nas etapas seguintes do nosso plano.
# Por enquanto, este arquivo ficará assim, mais simples, para permitir
# que a migração do banco de dados seja concluída com sucesso.