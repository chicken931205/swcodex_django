"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.static import serve
from home import views


handler404 = 'home.views.handler404'
handler403 = 'home.views.handler403'
handler500 = 'home.views.handler500'


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path("normalization/", include("normalization.urls")),
    path("connector/", include("connector.urls")),
    path("reconciliation/", include("reconciliation.urls")),
    path("reports/", include("reports.urls")),
    path("importer/", include("importer.urls")),
    path("samint/", include("apps.samint.urls")),
    path("api/", include("apps.api.urls")),    
    path('accounts/', include('allauth.urls')),
    path('', include('apps.file_manager.urls')),
    path('tasks/', include('apps.tasks.urls')),
    path('charts/', include('apps.charts.urls')),
    path("tables/", include("apps.tables.urls")),
    path("users/", include("apps.users.urls")),
    path('i18n/', include('django.conf.urls.i18n')),

    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}), 
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}), 

    # Debug toolbar
    path("__debug__/", include("debug_toolbar.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


urlpatterns += i18n_patterns(
    path('i18n/', views.i18n_view, name="i18n_view")
)