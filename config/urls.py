from django.contrib import admin
from django.urls import path, include

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