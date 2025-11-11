# ferias/middleware.py

from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import PeriodoAquisitivo, PerfilUsuario
import datetime

class OnboardingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # --- LÓGICA DE EXECUÇÃO ---
        # Este código roda em TODA requisição
        
        # 1. Verifica se o usuário está logado
        if request.user.is_authenticated:
            
            # 2. Ignora o Master ADM (superuser)
            if request.user.is_staff:
                return self.get_response(request)

            # 3. Busca o perfil
            try:
                perfil = request.user.perfil
            except PerfilUsuario.DoesNotExist:
                return self.get_response(request) # Deixa passar se não tiver perfil

            # 4. Verifica a "trava" do onboarding
            if not perfil.onboarding_completo:
                
                # 5. LIBERAÇÃO: Permite o acesso se o usuário JÁ ESTIVER
                # tentando acessar a página de onboarding ou de logout
                allowed_paths = [
                    reverse('ferias:onboarding'),
                    reverse('logout')
                ]
                if request.path in allowed_paths:
                    return self.get_response(request)
                
                # 6. BLOQUEIO: Força o redirecionamento.
                
                # ANTES DE REDIRECIONAR, vamos calcular e criar
                # os períodos aquisitivos que faltam (sua regra de negócio)
                self.criar_periodos_faltantes(perfil)
                
                return redirect('ferias:onboarding')

        # Se não estiver logado, ou se o onboarding estiver completo,
        # apenas continua o fluxo normal.
        return self.get_response(request)

    def criar_periodos_faltantes(self, perfil):
        """
        Calcula e cria os períodos aquisitivos que faltam
        desde a data de contratação.
        """
        hoje = timezone.now().date()
        data_contratacao = perfil.data_contratacao
        
        ultimo_periodo = perfil.periodos_aquisitivos.order_by('-data_inicio_aquisitivo').first()
        
        if ultimo_periodo:
            proximo_inicio = ultimo_periodo.data_fim_aquisitivo + datetime.timedelta(days=1)
        else:
            # Se nunca teve, o primeiro "aniversário" é a própria data de contratação
            proximo_inicio = data_contratacao
        
        # Loop que cria os períodos faltantes
        # O período só é "ganho" quando se completa 1 ano
        while proximo_inicio + relativedelta(years=1) <= hoje:
            data_fim = proximo_inicio + relativedelta(years=1) - datetime.timedelta(days=1)
            
            PeriodoAquisitivo.objects.get_or_create(
                perfil=perfil,
                data_inicio_aquisitivo=proximo_inicio,
                defaults={
                    'data_fim_aquisitivo': data_fim,
                    'dias_direito': 30,
                    'dias_disponiveis': 30, # Começa com 30 (usuário vai ajustar)
                    'status': 'ABERTO'
                }
            )
            # Prepara para o próximo ano
            proximo_inicio = proximo_inicio + relativedelta(years=1)