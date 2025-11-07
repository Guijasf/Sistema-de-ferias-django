# config/urls.py

from django.contrib import admin
from django.urls import path, include

# NOVO: Importações necessárias para servir arquivos de mídia
from django.conf import settings
from django.conf.urls.static import static

from django.contrib.auth import views as auth_views
from ferias.forms import CustomLoginForm

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('contas/login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=CustomLoginForm
    ), name='login'),

    path('contas/', include('django.contrib.auth.urls')),
    
    path('', include('ferias.urls')),
]

# NOVO: Adiciona a rota para servir arquivos de Mídia (fotos)
# Isso SÓ funciona em modo DEBUG (desenvolvimento)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)