from django.urls import path

from . import views

urlpatterns = [
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/<int:pk>/delete/', views.notification_delete, name='notification_delete'),
]
