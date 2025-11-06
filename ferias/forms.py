# ferias/forms.py

from django import forms # <--- A LINHA QUE ESTAVA FALTANDO!
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import PerfilUsuario, PeriodoAquisitivo, SolicitacaoFerias
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm

class PeriodoAquisitivoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"Período {obj.data_inicio_aquisitivo.year}/{obj.data_fim_aquisitivo.year} (Saldo: {obj.dias_disponiveis} dias)"

class SolicitacaoFeriasForm(forms.ModelForm):
    # REMOVEMOS o campo 'periodo_aquisitivo_choice' daqui

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # O __init__ agora fica muito mais simples, só aplica as classes
        self.fields['data_inicio'].widget.attrs.update({'class': 'input-form'})
        self.fields['data_fim'].widget.attrs.update({'class': 'input-form'})

    class Meta:
        model = SolicitacaoFerias
        fields = ['data_inicio', 'data_fim']
    
    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get("data_inicio")
        data_fim = cleaned_data.get("data_fim")
        
        if not (data_inicio and data_fim):
            return cleaned_data # Validação básica

        perfil = self.user.perfil

        # 1. Regra de data fim/início
        if data_fim < data_inicio:
            raise ValidationError("A data de término não pode ser anterior à data de início.")

        # 2. Regra de 10 dias (TODO: Mudar para dias úteis)
        total_dias_solicitados = (data_fim - data_inicio).days + 1
        if total_dias_solicitados < 10:
            raise ValidationError("O período mínimo para solicitação de férias é de 10 dias.")

        # 3. Regra de 1 ano de casa
        um_ano_de_casa = perfil.data_contratacao + relativedelta(years=1)
        if data_inicio < um_ano_de_casa:
            raise ValidationError(f"Você só pode solicitar férias após {um_ano_de_casa.strftime('%d/%m/%Y')}.")

        # 4. NOVA REGRA DE SALDO "CASCATA" (Regra dos 45 dias)
        periodos_com_saldo = PeriodoAquisitivo.objects.filter(
            perfil=perfil,
            dias_disponiveis__gt=0
        ).order_by('data_inicio_aquisitivo')

        saldo_total_disponivel = sum(p.dias_disponiveis for p in periodos_com_saldo)

        if saldo_total_disponivel < total_dias_solicitados:
            raise ValidationError(
                f"Saldo total insuficiente para esta solicitação. "
                f"Dias solicitados: {total_dias_solicitados}, "
                f"Seu saldo total disponível é: {saldo_total_disponivel} dias."
            )

        # 5. Regra de Conflito de Setor (agora Secretaria)
        secretaria_do_funcionario = perfil.secretaria
        if secretaria_do_funcionario:
            ferias_aprovadas_na_secretaria = SolicitacaoFerias.objects.filter(
                solicitante__perfil__secretaria=secretaria_do_funcionario,
                status__in=['PENDENTE_RH', 'APROVADA_FINAL']
            ).exclude(pk=self.instance.pk)

            for ferias_existente in ferias_aprovadas_na_secretaria:
                if (data_inicio <= ferias_existente.data_fim and data_fim >= ferias_existente.data_inicio):
                    raise ValidationError(
                        f"Conflito de datas! O funcionário {ferias_existente.solicitante.username} "
                        f"da mesma secretaria já tem férias marcadas entre "
                        f"{ferias_existente.data_inicio.strftime('%d/%m/%Y')} e "
                        f"{ferias_existente.data_fim.strftime('%d/%m/%Y')}."
                    )

        return cleaned_data


class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'input-form', 'placeholder': 'Nome de usuário'}
        )
        self.fields['password'].widget.attrs.update(
            {'class': 'input-form', 'placeholder': 'Senha'}
        )