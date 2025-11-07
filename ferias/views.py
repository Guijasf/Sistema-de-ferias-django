# ferias/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
import datetime
from django.contrib import messages # NOVA IMPORTAÇÃO para mensagens de sucesso

# ATUALIZADO: Importamos os novos formulários de edição
from .models import PerfilUsuario, PeriodoAquisitivo, SolicitacaoFerias, DescontoFerias
from .forms import SolicitacaoFeriasForm, CustomLoginForm, UserEditForm, PerfilUsuarioEditForm

# ----------------------------------------
# ATUALIZADO: Dashboard (View Principal)
# ----------------------------------------
@login_required
def dashboard(request):
    try:
        perfil = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        perfil = None

    solicitacoes = SolicitacaoFerias.objects.filter(solicitante=request.user).order_by('-data_solicitacao')
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

# ----------------------------------------
# ATUALIZADO: Solicitar Férias (View)
# ----------------------------------------
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

# ----------------------------------------
# ATUALIZADO: Dashboard do Gestor (View)
# ----------------------------------------
@login_required
def dashboard_gestor(request):
    try:
        perfil_gestor = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        return redirect('ferias:dashboard')

    if not perfil_gestor:
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

# ----------------------------------------
# ATUALIZADO: Aprovar (Fluxo de 1 Check)
# ----------------------------------------
@login_required
@transaction.atomic
def aprovar_solicitacao(request, pk):
    solicitacao = get_object_or_404(SolicitacaoFerias, pk=pk)
    
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
        
    except IntegrityError:
        pass 
    
    return redirect('ferias:dashboard_gestor')

# ----------------------------------------
# ATUALIZADO: Rejeitar (View)
# ----------------------------------------
@login_required
def rejeitar_solicitacao(request, pk):
    solicitacao = get_object_or_404(SolicitacaoFerias, pk=pk)
    
    if request.method == 'POST':
        solicitacao.status = 'REJEITADA'
        solicitacao.aprovador_gestor = request.user 
        solicitacao.data_aprovacao_gestor = timezone.now()
        solicitacao.motivo_rejeicao = request.POST.get('motivo_rejeicao', '')
        solicitacao.save()
    
    return redirect('ferias:dashboard_gestor')

# ----------------------------------------
# ATUALIZADO: API do Calendário (View)
# ----------------------------------------
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

# ----------------------------------------
# VIEWS QUE NÃO MUDAM (Calendário, Tema)
# ----------------------------------------
@login_required
def calendario_ferias(request):
    return render(request, 'ferias/calendario.html')

@login_required
def definir_tema(request, tema):
    request.session['tema_preferido'] = tema
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('ferias:dashboard')))

# ----------------------------------------
# VIEW DE PERFIL (Existente)
# ----------------------------------------
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

# ----------------------------------------
# A NOVA VIEW QUE ESTAVA FALTANDO!
# ----------------------------------------
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