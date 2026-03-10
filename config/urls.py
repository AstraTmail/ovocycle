from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentification
    path('connexion/', auth_views.LoginView.as_view(
        template_name='auth/login.html',
        redirect_authenticated_user=True,
    ), name='login'),
    path('deconnexion/', auth_views.LogoutView.as_view(
        next_page='login',
    ), name='logout'),

    # Application
    path('', include('apps.incubation.urls', namespace='incubation')),
    path('analytique/', include('apps.analytics.urls', namespace='analytics')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'OvoCycle — Administration'
admin.site.site_title  = 'OvoCycle'
admin.site.index_title = 'Gestion de la couveuse'