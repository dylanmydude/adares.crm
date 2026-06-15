from django.urls import path

from . import views

urlpatterns = [
    path('backup/', views.backup_page, name='backup_page'),
    path('backup/create/', views.backup_create, name='backup_create'),
    path('backup/<int:pk>/download/', views.backup_download, name='backup_download'),
]
