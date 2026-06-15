from django.urls import path

from . import views

urlpatterns = [
    path('clients/', views.client_list, name='client_list'),
    path('clients/add/', views.client_create, name='client_create'),
    path('clients/<int:pk>/edit/', views.client_edit, name='client_edit'),
    path('clients/<int:pk>/delete/', views.client_delete, name='client_delete'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/add/', views.job_create, name='job_create'),
    path('jobs/<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('jobs/<int:pk>/delete/', views.job_delete, name='job_delete'),
]
