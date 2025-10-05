from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import SolicitacaoFerias, Funcionario, PeriodoAquisitivo
from .forms import SolicitacaoFeriasForm
import datetime
from django.http import JsonResponse

@login_required
def dashboard(request):
    solicitacoes = SolicitacaoFerias.objects.filter(solicitante=request.user).order_by('-data_solicitacao')
    is_gestor = Funcionario.objects.filter(gestor__user=request.user).exists()
    periodos = PeriodoAquisitivo.objects.filter(
        funcionario__user=request.user
    ).order_by('-data_inicio')
    context = {
        'solicitacoes': solicitacoes,
        'is_gestor': is_gestor,
        'periodos_aquisitivos': periodos,
    }
    return render(request, 'ferias/dashboard.html', context)

@login_required
def solicitar_ferias(request):
    if request.method == 'POST':
        form = SolicitacaoFeriasForm(request.POST, user=request.user)
        if form.is_valid():
            solicitacao = form.save(commit=False)
            solicitacao.solicitante = request.user
            solicitacao.save()
            return redirect('ferias:dashboard')
    else:
        form = SolicitacaoFeriasForm(user=request.user)

    return render(request, 'ferias/solicitar_ferias.html', {'form': form})    

@login_required
def dashboard_gestor(request):
    if not Funcionario.objects.filter(gestor__user=request.user).exists():
        return redirect('ferias:dashboard')
    
    equipe_qs = Funcionario.objects.filter(gestor__user=request.user)
    membros_da_equipe = [f.user for f in equipe_qs]

    solicitacoes_pendentes = SolicitacaoFerias.objects.filter(
        solicitante__in=membros_da_equipe,
        status='pendente'
    ).order_by('data_inicio')

    context = {
        'solicitacoes_pendentes': solicitacoes_pendentes,
    }
    return render(request, 'ferias/dashboard_gestor.html', context)

@login_required
@transaction.atomic
def aprovar_solicitacao(request, pk):
    solicitacao = get_object_or_404(SolicitacaoFerias, pk=pk)

    periodo = solicitacao.periodo_aquisitivo
    total_dias = solicitacao.total_dias

    if periodo.saldo_dias >= total_dias:
        periodo.saldo_dias -= total_dias
        periodo.save()

        solicitacao.status = 'aprovado'
        solicitacao.aprovador = request.user
        solicitacao.data_aprovacao = timezone.now()
        solicitacao.save()
    else:
        pass

    return redirect('ferias:dashboard_gestor')


@login_required
def rejeitar_solicitacao(request, pk):
    solicitacao = get_object_or_404(SolicitacaoFerias, pk=pk)

    if request.method == 'POST':
        solicitacao.status = 'rejeitado'
        solicitacao.aprovador = request.user
        solicitacao.data_aprovacao = timezone.now()
        solicitacao.motivo_rejeicao = request.POST.get('motivo_rejeicao', '')
        solicitacao.save()

    return redirect('ferias:dashboard_gestor')

@login_required
def definir_tema(request, tema):
    request.session['tema_preferido'] = tema
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('ferias:dashboard')))

@login_required
def api_eventos_ferias(request):
    ferias_aprovadas = SolicitacaoFerias.objects.filter(status='aprovado')
    eventos = []
    for ferias in ferias_aprovadas:
        eventos.append({
            'title': ferias.solicitante.get_full_name() or ferias.solicitante.username,
            'start': ferias.data_inicio,
            'end': ferias.data_fim + datetime.timedelta(days=1)
        })

    return JsonResponse(eventos, safe=False)