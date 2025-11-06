# ferias/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
import datetime

# ALTERADO: Importamos os novos modelos
from .models import PerfilUsuario, PeriodoAquisitivo, SolicitacaoFerias, DescontoFerias
from .forms import SolicitacaoFeriasForm

# ----------------------------------------
# ATUALIZADO: Dashboard (View Principal)
# ----------------------------------------
@login_required
def dashboard(request):
    try:
        # ATUALIZADO: Puxa o perfil
        perfil = request.user.perfil
    except PerfilUsuario.DoesNotExist:
        # Lida com um usuário que não tem perfil (ex: superadmin)
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
            # 1. Salva a solicitação principal
            solicitacao = form.save(commit=False)
            solicitacao.solicitante = request.user
            solicitacao.status = 'PENDENTE_GESTOR' # Reinicia o status
            solicitacao.save() 
            
            # --- INÍCIO DA NOVA LÓGICA DE "CASCATA" ---
            
            # 2. Pega os dados validados
            dias_a_descontar = (form.cleaned_data['data_fim'] - form.cleaned_data['data_inicio']).days + 1
            perfil = request.user.perfil
            
            # 3. Busca todos os períodos com saldo, do mais antigo para o mais novo
            periodos_com_saldo = PeriodoAquisitivo.objects.filter(
                perfil=perfil,
                dias_disponiveis__gt=0
            ).order_by('data_inicio_aquisitivo')
            
            # 4. Itera sobre os períodos e desconta os dias
            for periodo in periodos_com_saldo:
                if dias_a_descontar == 0:
                    break # Já descontou tudo o que precisava

                if periodo.dias_disponiveis >= dias_a_descontar:
                    # Este período tem saldo suficiente para cobrir o resto
                    DescontoFerias.objects.create(
                        solicitacao=solicitacao,
                        periodo_aquisitivo=periodo,
                        dias_descontados=dias_a_descontar
                    )
                    # Não descontamos o saldo real ainda, só na APROVAÇÃO FINAL DO RH
                    dias_a_descontar = 0
                else:
                    # Esgota o saldo deste período e passa para o próximo
                    dias_para_descontar_deste_periodo = periodo.dias_disponiveis
                    DescontoFerias.objects.create(
                        solicitacao=solicitacao,
                        periodo_aquisitivo=periodo,
                        dias_descontados=dias_para_descontar_deste_periodo
                    )
                    dias_a_descontar -= dias_para_descontar_deste_periodo
            
            # --- FIM DA LÓGICA DE "CASCATA" ---
            
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
        # Se o usuário não tem perfil (ex: admin), ele não pode ser gestor
        return redirect('ferias:dashboard')

    if not perfil_gestor:
        return redirect('ferias:dashboard')

    # Encontra os usuários da equipe deste gestor
    equipe_qs = PerfilUsuario.objects.filter(gestor=perfil_gestor)
    membros_da_equipe_users = [p.user for p in equipe_qs]
    
    # Busca solicitações da equipe que estão PENDENTES_GESTOR
    solicitacoes_pendentes = SolicitacaoFerias.objects.filter(
        solicitante__in=membros_da_equipe_users, 
        status='PENDENTE_GESTOR'
    ).order_by('data_inicio')
    
    context = {
        'solicitacoes_pendentes': solicitacoes_pendentes,
    }
    return render(request, 'ferias/dashboard_gestor.html', context)

# ----------------------------------------
# ATUALIZADO: Aprovar (Check 1 do Gestor)
# ----------------------------------------
@login_required
def aprovar_solicitacao(request, pk):
    solicitacao = get_object_or_404(SolicitacaoFerias, pk=pk)
    
    # TODO: Checar se o request.user é de fato o gestor do solicitante
    
    # ATUALIZADO: O gestor agora "promove" a solicitação para o RH
    solicitacao.status = 'PENDENTE_RH'
    solicitacao.aprovador_gestor = request.user
    solicitacao.data_aprovacao_gestor = timezone.now()
    solicitacao.save()
    
    # ATENÇÃO: Os dias NÃO são descontados aqui. Só na aprovação final do RH.
    
    return redirect('ferias:dashboard_gestor')

# ----------------------------------------
# ATUALIZADO: Rejeitar (View)
# ----------------------------------------
@login_required
def rejeitar_solicitacao(request, pk):
    solicitacao = get_object_or_404(SolicitacaoFerias, pk=pk)
    
    # TODO: Checar se o request.user é o gestor
    
    if request.method == 'POST':
        solicitacao.status = 'REJEITADA'
        solicitacao.aprovador_gestor = request.user # Registra quem rejeitou
        solicitacao.data_aprovacao_gestor = timezone.now()
        solicitacao.motivo_rejeicao = request.POST.get('motivo_rejeicao', '')
        solicitacao.save()
    
    return redirect('ferias:dashboard_gestor')

# ----------------------------------------
# ATUALIZADO: API do Calendário (View)
# ----------------------------------------
@login_required
def api_eventos_ferias(request):
    # ATUALIZADO: O calendário só mostra férias com APROVAÇÃO FINAL
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