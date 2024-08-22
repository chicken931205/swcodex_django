from django.urls import path
from . import views
from . import scheduler

app_name = 'integration'

urlpatterns = [
    path('integrations/', views.integration_list, name='integration_list'),
]