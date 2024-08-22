from django.urls import path
from . import views
from . import scheduler

app_name = 'importer'

urlpatterns = [
    path('import/', views.import_file, name='import_file'),
    path('import-jobs/', views.import_job_list, name='import_job_list'),
    path('edit-import-job/<int:job_id>/', views.edit_import_job, name='edit_import_job'),
    path('delete-import-job/<int:job_id>/', views.delete_import_job, name='delete_import_job'),
]

scheduler.initialize()