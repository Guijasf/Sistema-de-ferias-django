# ferias/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
import datetime
from django.contrib import messages
from django.contrib.auth import login # Para auto-login no cadastro

# Importamos os novos modelos e formulários
from .models import PerfilUsuario, PeriodoAquisitivo, SolicitacaoFerias, DescontoFerias
from .forms import (
    SolicitacaoFeriasForm, CustomLoginForm, UserEditForm, 
    PerfilUsuarioEditForm, CadastroForm
)

# --- VIEW DO DASHBOARD ---
@login_required
def dashboard(request):
    try:
        perfil = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        perfil = None

    solicitacoes = SolicitacaoFerias.objects.filter(solicitante=request.user).order_by('-data_solicitacao')
    # Checa se o usuário logado é gestor de ALGUÉM
    is_gestor = PerfilUsuario.objects.filter(gestor=perfil).exists()

    periodo_ativo = PeriodoAquisitivo.objects.filter(
        perfil=perfil,
        dias_disponiveis__gt=0
    ).order_by('data_inicio_aquisitivo').first()

    context = {
        'solicitacoes': solicitacoes,
        'is_gestor': is_gestor,
        'periodo_ativo': periodo_ativo,
    }
    return render(request, 'ferias/dashboard.html', context)

# --- VIEW DE SOLICITAR FÉRIAS (com lógica de cascata) ---
@login_required
@transaction.atomic
def solicitar_ferias(request):
    if request.method == 'POST':
        form = SolicitacaoFeriasForm(request.POST, user=request.user)
        if form.is_valid():
            solicitacao = form.save(commit=False)
            solicitacao.solicitante = request.user
            solicitacao.status = 'PENDENTE_GESTOR' 
            solicitacao.save() 
            
            dias_a_descontar = (form.cleaned_data['data_fim'] - form.cleaned_data['data_inicio']).days + 1
            perfil = request.user.perfil
            
            periodos_com_saldo = PeriodoAquisitivo.objects.filter(
                perfil=perfil,
                dias_disponiveis__gt=0
            ).order_by('data_inicio_aquisitivo')
            
            for periodo in periodos_com_saldo:
                if dias_a_descontar == 0:
                    break
                if periodo.dias_disponiveis >= dias_a_descontar:
                    DescontoFerias.objects.create(
                        solicitacao=solicitacao,
                        periodo_aquisitivo=periodo,
                        dias_descontados=dias_a_descontar
                    )
                    dias_a_descontar = 0
                else:
                    dias_para_descontar_deste_periodo = periodo.dias_disponiveis
                    DescontoFerias.objects.create(
                        solicitacao=solicitacao,
                        periodo_aquisitivo=periodo,
                        dias_descontados=dias_para_descontar_deste_periodo
                    )
                    dias_a_descontar -= dias_para_descontar_deste_periodo
            
            return redirect('ferias:dashboard')
    else:
        form = SolicitacaoFeriasForm(user=request.user)
    return render(request, 'ferias/solicitar_ferias.html', {'form': form})

# --- VIEW DO PAINEL DO GESTOR ---
@login_required
def dashboard_gestor(request):
    try:
        perfil_gestor = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        return redirect('ferias:dashboard')
    
    # Checagem de segurança dupla
    if not PerfilUsuario.objects.filter(gestor=perfil_gestor).exists():
        messages.error(request, "Você não tem permissão para acessar o painel do gestor.")
        return redirect('ferias:dashboard')

    equipe_qs = PerfilUsuario.objects.filter(gestor=perfil_gestor)
    membros_da_equipe_users = [p.user for p in equipe_qs]
    
    solicitacoes_pendentes = SolicitacaoFerias.objects.filter(
        solicitante__in=membros_da_equipe_users, 
        status='PENDENTE_GESTOR'
    ).order_by('data_inicio')
    
    context = {
        'solicitacoes_pendentes': solicitacoes_pendentes,
    }
    return render(request, 'ferias/dashboard_gestor.html', context)

# --- VIEW DE APROVAÇÃO (1-CHECK) ---
@login_required
@transaction.atomic
def aprovar_solicitacao(request, pk):
    solicitacao = get_object_or_404(SolicitacaoFerias, pk=pk)
    
    # TODO: Checar permissão (se o user é o gestor do solicitante)
    
    solicitacao.status = 'APROVADA_FINAL'
    solicitacao.aprovador_gestor = request.user
    solicitacao.data_aprovacao_gestor = timezone.now()
    
    descontos_a_fazer = DescontoFerias.objects.filter(solicitacao=solicitacao)
    
    try:
        for desconto in descontos_a_fazer:
            periodo = desconto.periodo_aquisitivo
            
            if periodo.dias_disponiveis >= desconto.dias_descontados:
                periodo.dias_disponiveis -= desconto.dias_descontados
                if periodo.dias_disponiveis == 0:
                    periodo.status = 'FECHADO'
                periodo.save()
            else:
                raise IntegrityError("Falha na aprovação. Saldo insuficiente detectado.")
        
        solicitacao.save()
        messages.success(request, "Férias aprovadas com sucesso!")
        
    except IntegrityError:
        messages.error(request, "Erro ao aprovar. O saldo do funcionário pode ter mudado.")
    
    return redirect('ferias:dashboard_gestor')

# --- VIEW DE REJEIÇÃO ---
@login_required
def rejeitar_solicitacao(request, pk):
    solicitacao = get_object_or_404(SolicitacaoFerias, pk=pk)
    
    # TODO: Checar permissão
    
    if request.method == 'POST':
        solicitacao.status = 'REJEITADA'
        solicitacao.aprovador_gestor = request.user 
        solicitacao.data_aprovacao_gestor = timezone.now()
        solicitacao.motivo_rejeicao = request.POST.get('motivo_rejeicao', '')
        solicitacao.save()
        messages.success(request, "Solicitação rejeitada.")
    
    return redirect('ferias:dashboard_gestor')

# --- VIEWS DE PERFIL ---
@login_required
def ver_perfil(request):
    try:
        perfil = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        return redirect('ferias:dashboard')
    periodos_abertos = PeriodoAquisitivo.objects.filter(
        perfil=perfil,
        status='ABERTO'
    ).order_by('data_inicio_aquisitivo')
    context = {
        'perfil': perfil,
        'periodos_abertos': periodos_abertos
    }
    return render(request, 'ferias/perfil.html', context)

@login_required
@transaction.atomic
def editar_perfil(request):
    try:
        perfil = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        return redirect('ferias:dashboard')

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        perfil_form = PerfilUsuarioEditForm(request.POST, request.FILES, instance=perfil)

        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            messages.success(request, 'Seu perfil foi atualizado com sucesso!')
            return redirect('ferias:ver_perfil')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        user_form = UserEditForm(instance=request.user)
        perfil_form = PerfilUsuarioEditForm(instance=perfil)

    context = {
        'user_form': user_form,
        'perfil_form': perfil_form
    }
    return render(request, 'ferias/editar_perfil.html', context)

# --- VIEW DE CADASTRO PÚBLICO ---
def cadastro_view(request):
    if request.user.is_authenticated:
        return redirect('ferias:dashboard')
    
    if request.method == 'POST':
        form = CadastroForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Cadastro realizado com sucesso! Faça o login para continuar.')
            return redirect('login')
    else:
        form = CadastroForm()
        
    return render(request, 'registration/cadastro.html', {'form': form})

# --- VIEW DE ONBOARDING ---
@login_required
@transaction.atomic
def onboarding_view(request):
    try:
        perfil = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        return redirect('ferias:dashboard')
    
    if perfil.onboarding_completo:
        return redirect('ferias:dashboard')

    periodos = PeriodoAquisitivo.objects.filter(
        perfil=perfil,
        status='ABERTO'
    ).order_by('data_inicio_aquisitivo')

    if request.method == 'POST':
        try:
            for periodo in periodos:
                nome_do_campo_saldo = f"periodo_saldo_{periodo.id}"
                nome_do_campo_check = f"periodo_check_{periodo.id}"
                
                if nome_do_campo_check in request.POST:
                    periodo.dias_disponiveis = 0
                    periodo.status = 'FECHADO'
                else:
                    dias_disponiveis_str = request.POST.get(nome_do_campo_saldo)
                    if dias_disponiveis_str is not None:
                        novos_dias = int(dias_disponiveis_str)
                        periodo.dias_disponiveis = novos_dias
                        if novos_dias == 0:
                            periodo.status = 'FECHADO'
                        else:
                            periodo.status = 'ABERTO'
                
                periodo.save()
            
            perfil.onboarding_completo = True
            perfil.save()
            
            return redirect('ferias:dashboard')

        except Exception as e:
            messages.error(request, f"Ocorreu um erro: {e}. Verifique os valores digitados.")

    context = {
        'periodos_onboarding': periodos
    }
    return render(request, 'ferias/onboarding.html', context)

# --- VIEWS DE UTILIDADE ---
@login_required
def api_eventos_ferias(request):
    ferias_aprovadas = SolicitacaoFerias.objects.filter(status='APROVADA_FINAL')
    eventos = []
    for ferias in ferias_aprovadas:
        eventos.append({
            'title': ferias.solicitante.get_full_name() or ferias.solicitante.username,
            'start': ferias.data_inicio,
            'end': ferias.data_fim + datetime.timedelta(days=1),
        })
    return JsonResponse(eventos, safe=False)

@login_required
def calendario_ferias(request):
    return render(request, 'ferias/calendario.html')

@login_required
def definir_tema(request, tema):
    request.session['tema_preferido'] = tema
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('ferias:dashboard')))