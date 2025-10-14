# ferias/forms.py

from django import forms
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import SolicitacaoFerias, PeriodoAquisitivo, Funcionario
from django.core.exceptions import ValidationError

class PeriodoAquisitivoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"Período {obj.data_inicio.year}/{obj.data_fim.year} (Saldo: {obj.saldo_dias} dias)"

class SolicitacaoFeriasForm(forms.ModelForm):
    periodo_aquisitivo = PeriodoAquisitivoChoiceField(
        queryset=PeriodoAquisitivo.objects.none(),
        label="Descontar do Período Aquisitivo",
        empty_label="--- Nenhum período com saldo disponível ---"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            # LÓGICA ALTERADA: Encontrar apenas o período mais antigo com saldo
            periodos_com_saldo = PeriodoAquisitivo.objects.filter(
                funcionario__user=self.user, 
                saldo_dias__gt=0
            ).order_by('data_inicio')  # Ordena do mais antigo para o mais novo

            primeiro_periodo_valido = periodos_com_saldo.first()
            
            if primeiro_periodo_valido:
                # Se encontrarmos um período válido, o dropdown só terá essa opção
                self.fields['periodo_aquisitivo'].queryset = PeriodoAquisitivo.objects.filter(pk=primeiro_periodo_valido.pk)
            else:
                # Se não houver nenhum período com saldo, o queryset continua vazio
                self.fields['periodo_aquisitivo'].queryset = PeriodoAquisitivo.objects.none()

        self.fields['data_inicio'].widget.attrs.update({'class': 'form-control'})
        self.fields['data_fim'].widget.attrs.update({'class': 'form-control'})
        self.fields['periodo_aquisitivo'].widget.attrs.update({'class': 'form-select'})

    class Meta:
        model = SolicitacaoFerias
        fields = ['data_inicio', 'data_fim', 'periodo_aquisitivo']
    
    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get("data_inicio")
        data_fim = cleaned_data.get("data_fim")
        periodo_selecionado = cleaned_data.get("periodo_aquisitivo")
        
        if not (data_inicio and data_fim and periodo_selecionado):
            return cleaned_data

        # --- NOVA VALIDAÇÃO DE SEGURANÇA ---
        periodo_mais_antigo_com_saldo = PeriodoAquisitivo.objects.filter(
            funcionario__user=self.user,
            saldo_dias__gt=0
        ).order_by('data_inicio').first()

        if periodo_mais_antigo_com_saldo and periodo_selecionado != periodo_mais_antigo_com_saldo:
            raise ValidationError(
                f"Ação inválida. Você deve primeiro utilizar o saldo do seu período aquisitivo mais antigo: "
                f"{periodo_mais_antigo_com_saldo.data_inicio.year}/{periodo_mais_antigo_com_saldo.data_fim.year}."
            )
        # --- FIM DA NOVA VALIDAÇÃO ---

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