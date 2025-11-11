# config/urls.py

from django.contrib import admin
from django.urls import path, include

# Importações para servir arquivos de mídia (fotos)
from django.conf import settings
from django.conf.urls.static import static

# Importações para o login e cadastro
from django.contrib.auth import views as auth_views
from ferias.forms import CustomLoginForm
from ferias import views as ferias_views # Importamos as views para o cadastro

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # URL de Cadastro Público
    path('contas/cadastrar/', ferias_views.cadastro_view, name='cadastro'),
    
    # URL de Login Customizada
    path('contas/login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=CustomLoginForm
    ), name='login'),

    # Inclui as outras URLs de autenticação (logout, etc.)
    path('contas/', include('django.contrib.auth.urls')),
    
    # Inclui todas as URLs do nosso app 'ferias'
    path('', include('ferias.urls')),
]

# Adiciona a rota para servir arquivos de Mídia (fotos) em modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)