from django.urls import path

from . import views

urlpatterns = [
    path('', views.management_user_list, name='management_user_list'),
    path('add/', views.management_user_add, name='management_user_add'),
    path('<int:pk>/', views.management_user_detail, name='management_user_detail'),
    path('<int:pk>/edit/', views.management_user_edit, name='management_user_edit'),
    path('<int:pk>/delete/', views.management_user_delete, name='management_user_delete'),
]
