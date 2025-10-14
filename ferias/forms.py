# ferias/forms.py

from django import forms
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import SolicitacaoFerias, PeriodoAquisitivo, Funcionario
from django.core.exceptions import ValidationError

# NOVO: Criamos uma classe de campo customizada
class PeriodoAquisitivoChoiceField(forms.ModelChoiceField):
    # Este método é chamado para cada objeto na lista, para decidir qual texto mostrar
    def label_from_instance(self, obj):
        return f"Período {obj.data_inicio.year}/{obj.data_fim.year} (Saldo: {obj.saldo_dias:.0f} dias)"

class SolicitacaoFeriasForm(forms.ModelForm):
    # ALTERADO: Usamos nosso novo campo customizado
    periodo_aquisitivo = PeriodoAquisitivoChoiceField(
        queryset=PeriodoAquisitivo.objects.none(), 
        label="Descontar do Período Aquisitivo",
        empty_label="--- Selecione o Período ---"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            queryset = PeriodoAquisitivo.objects.filter(
                funcionario__user=self.user, 
                saldo_dias__gt=0
            ).order_by('-data_inicio')
            self.fields['periodo_aquisitivo'].queryset = queryset
        
        # Adicionando classes do Bootstrap aos campos diretamente aqui
        self.fields['data_inicio'].widget.attrs.update({'class': 'form-control'})
        self.fields['data_fim'].widget.attrs.update({'class': 'form-control'})
        self.fields['periodo_aquisitivo'].widget.attrs.update({'class': 'form-select'})


    class Meta:
        model = SolicitacaoFerias
        fields = ['data_inicio', 'data_fim', 'periodo_aquisitivo']
        # Removemos os widgets daqui, pois estamos configurando no __init__
    
    def clean(self):
        # ... (O método clean continua exatamente o mesmo de antes, sem alterações)
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get("data_inicio")
        data_fim = cleaned_data.get("data_fim")
        periodo_selecionado = cleaned_data.get("periodo_aquisitivo")
        
        if not (data_inicio and data_fim and periodo_selecionado):
            return cleaned_data

        if data_fim < data_inicio:
            raise ValidationError("A data de término não pode ser anterior à data de início.")

        total_dias_solicitados = (data_fim - data_inicio).days + 1

        if total_dias_solicitados < 10:
            raise ValidationError("O período mínimo para solicitação de férias é de 10 dias.")

        funcionario = self.user.funcionario
        um_ano_de_casa = funcionario.data_nomeacao + relativedelta(years=1)
        if data_inicio < um_ano_de_casa:
            raise ValidationError(f"Você só pode solicitar férias após {um_ano_de_casa.strftime('%d/%m/%Y')}.")

        if periodo_selecionado.saldo_dias < total_dias_solicitados:
            raise ValidationError(
                f"Saldo insuficiente no período selecionado. "
                f"Dias solicitados: {total_dias_solicitados}, "
                f"Saldo disponível no período: {periodo_selecionado.saldo_dias}"
            )

        setor_do_funcionario = funcionario.setor
        ferias_aprovadas_no_setor = SolicitacaoFerias.objects.filter(
            solicitante__funcionario__setor=setor_do_funcionario,
            status='aprovado'
        ).exclude(pk=self.instance.pk)

        for ferias_existente in ferias_aprovadas_no_setor:
            if (data_inicio <= ferias_existente.data_fim and data_fim >= ferias_existente.data_inicio):
                raise ValidationError(
                    f"Conflito de datas! O funcionário {ferias_existente.solicitante.username} "
                    f"do mesmo setor já tem férias marcadas entre "
                    f"{ferias_existente.data_inicio.strftime('%d/%m/%Y')} e "
                    f"{ferias_existente.data_fim.strftime('%d/%m/%Y')}."
                )

        return cleaned_data