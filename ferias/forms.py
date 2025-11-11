# ferias/forms.py

from django import forms
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import PerfilUsuario, PeriodoAquisitivo, SolicitacaoFerias
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction

# --- CAMPO CUSTOMIZADO PARA O DROPDOWN DE PERÍODO (USADO NO ONBOARDING) ---
class PeriodoAquisitivoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"Período {obj.data_inicio_aquisitivo.year}/{obj.data_fim_aquisitivo.year} (Saldo: {obj.dias_disponiveis} dias)"

# --- FORMULÁRIO DE SOLICITAÇÃO (LÓGICA DE CASCATA) ---
class SolicitacaoFeriasForm(forms.ModelForm):
    # O usuário não escolhe mais o período, o sistema faz isso
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
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
            return cleaned_data

        perfil = self.user.perfil

        # Regra 1: Data fim/início
        if data_fim < data_inicio:
            raise ValidationError("A data de término não pode ser anterior à data de início.")

        # Regra 2: Mínimo de 10 dias
        total_dias_solicitados = (data_fim - data_inicio).days + 1
        if total_dias_solicitados < 10:
            raise ValidationError("O período mínimo para solicitação de férias é de 10 dias.")

        # Regra 3: 1 ano de casa
        um_ano_de_casa = perfil.data_contratacao + relativedelta(years=1)
        if data_inicio < um_ano_de_casa:
            raise ValidationError(f"Você só pode solicitar férias após {um_ano_de_casa.strftime('%d/%m/%Y')}.")

        # Regra 4: Saldo em Cascata
        periodos_com_saldo = PeriodoAquisitivo.objects.filter(
            perfil=perfil,
            dias_disponiveis__gt=0
        ).order_by('data_inicio_aquisitivo')
        saldo_total_disponivel = sum(p.dias_disponiveis for p in periodos_com_saldo)

        if saldo_total_disponivel < total_dias_solicitados:
            raise ValidationError(
                f"Saldo total insuficiente. Dias solicitados: {total_dias_solicitados}, "
                f"Seu saldo total é: {saldo_total_disponivel} dias."
            )

        # Regra 5: Conflito de Secretaria
        secretaria_do_funcionario = perfil.secretaria
        if secretaria_do_funcionario:
            ferias_aprovadas_na_secretaria = SolicitacaoFerias.objects.filter(
                solicitante__perfil__secretaria=secretaria_do_funcionario,
                status='APROVADA_FINAL' # Só checa férias 100% aprovadas
            ).exclude(pk=self.instance.pk)

            for ferias_existente in ferias_aprovadas_na_secretaria:
                if (data_inicio <= ferias_existente.data_fim and data_fim >= ferias_existente.data_inicio):
                    raise ValidationError(
                        f"Conflito de datas! Alguém da sua secretaria já tem férias marcadas "
                        f"entre {ferias_existente.data_inicio.strftime('%d/%m/%Y')} e "
                        f"{ferias_existente.data_fim.strftime('%d/%m/%Y')}."
                    )
        return cleaned_data

# --- FORMULÁRIO DE LOGIN (CUSTOMIZADO) ---
class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'input-form', 'placeholder': 'Nome de usuário'}
        )
        self.fields['password'].widget.attrs.update(
            {'class': 'input-form', 'placeholder': 'Senha'}
        )

# --- FORMULÁRIOS DE EDIÇÃO DE PERFIL ---
class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({'class': 'input-form'})
        self.fields['last_name'].widget.attrs.update({'class': 'input-form'})
        self.fields['email'].widget.attrs.update({'class': 'input-form'})

class PerfilUsuarioEditForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ['foto_perfil', 'data_nascimento', 'matricula', 'cargo', 'secretaria', 'lotacao']
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['foto_perfil'].widget.attrs.update({'class': 'input-form'})
        self.fields['data_nascimento'].widget.attrs.update({'class': 'input-form'})
        self.fields['matricula'].widget.attrs.update({'class': 'input-form'})
        self.fields['cargo'].widget.attrs.update({'class': 'input-form'})
        self.fields['secretaria'].widget.attrs.update({'class': 'input-form'})
        self.fields['lotacao'].widget.attrs.update({'class': 'input-form'})

# --- FORMULÁRIO DE CADASTRO PÚBLICO ---
class CadastroForm(forms.ModelForm):
    username = forms.CharField(label="Nome de Usuário (login)", max_length=100)
    first_name = forms.CharField(label="Nome", max_length=100)
    last_name = forms.CharField(label="Sobrenome", max_length=100)
    email = forms.EmailField(label="E-mail")
    password = forms.CharField(label="Senha", widget=forms.PasswordInput)
    password_confirm = forms.CharField(label="Confirmação de Senha", widget=forms.PasswordInput)

    cargo = forms.CharField(label="Cargo", max_length=100)
    lotacao = forms.CharField(label="Lotação", max_length=100)
    secretaria = forms.CharField(label="Secretaria", max_length=100)
    matricula = forms.CharField(label="Matrícula", max_length=20)
    data_contratacao = forms.DateField(label="Data de Nomeação/Contratação", widget=forms.DateInput(attrs={'type': 'date'}))
    data_nascimento = forms.DateField(label="Data de Nascimento", widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'password_confirm', 
                  'cargo', 'lotacao', 'secretaria', 'matricula', 'data_contratacao', 'data_nascimento']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input-form'})

    def clean_password_confirm(self):
        password = self.cleaned_data.get("password")
        password_confirm = self.cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise ValidationError("As senhas não coincidem.")
        return password_confirm
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Um usuário com este e-mail já existe.")
        return email
    
    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')
        if PerfilUsuario.objects.filter(matricula=matricula).exists():
            raise ValidationError("Um usuário com esta matrícula já existe.")
        return matricula

    @transaction.atomic
    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        
        perfil = user.perfil 
        perfil.cargo = self.cleaned_data['cargo']
        perfil.lotacao = self.cleaned_data['lotacao']
        perfil.secretaria = self.cleaned_data['secretaria']
        perfil.matricula = self.cleaned_data['matricula']
        perfil.data_contratacao = self.cleaned_data['data_contratacao']
        perfil.data_nascimento = self.cleaned_data['data_nascimento']
        
        if commit:
            perfil.save()
        
        return user