# ferias/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
# ALTERADO: Importamos os novos modelos
from .models import PerfilUsuario, SolicitacaoFerias
from django.core.mail import send_mail
from django.conf import settings

# NOVO SINAL:
# Cria um PerfilUsuario automaticamente toda vez que um User é criado.
@receiver(post_save, sender=User)
def criar_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(user=instance)

# SINAL ATUALIZADO:
# Envia e-mails de notificação
@receiver(post_save, sender=SolicitacaoFerias)
def enviar_notificacao_por_email(sender, instance, created, **kwargs):
    solicitacao = instance
    
    # E-mail para o gestor quando uma nova solicitação é criada
    if created and solicitacao.status == 'PENDENTE_GESTOR':
        try:
            # ATUALIZADO: O caminho para o gestor agora é via 'perfil'
            gestor_perfil = solicitacao.solicitante.perfil.gestor
            if gestor_perfil and gestor_perfil.user.email:
                gestor_user = gestor_perfil.user
                subject = f'Nova Solicitação de Férias: {solicitacao.solicitante.get_full_name()}'
                message = f"""
                Olá {gestor_user.get_full_name()},

                Uma nova solicitação de férias foi feita por {solicitacao.solicitante.get_full_name()}.
                Período: {solicitacao.data_inicio.strftime('%d/%m/%Y')} a {solicitacao.data_fim.strftime('%d/%m/%Y')}
                
                Por favor, acesse o painel de gestão para analisar.
                """
                send_mail(
                    subject, message, settings.DEFAULT_FROM_EMAIL,
                    [gestor_user.email], fail_silently=False
                )
        except PerfilUsuario.DoesNotExist:
            pass # Não falha se o perfil/gestor não existir

    # E-mail para o funcionário quando o status muda (aprovado/rejeitado)
    if not created and solicitacao.solicitante.email:
        # ATUALIZADO: Checa os novos status
        if instance.status == 'APROVADA_FINAL' or instance.status == 'REJEITADA':
            subject = f'Atualização da sua Solicitação de Férias'
            message = f"""
            Olá {solicitacao.solicitante.get_full_name()},
            
            Sua solicitação de férias para o período de {solicitacao.data_inicio.strftime('%d/%m/%Y')} a {solicitacao.data_fim.strftime('%d/%m/%Y')} foi {solicitacao.get_status_display()}.
            
            Status: {solicitacao.get_status_display().upper()}
            """
            send_mail(
                subject, message, settings.DEFAULT_FROM_EMAIL,
                [solicitacao.solicitante.email], fail_silently=False
            )