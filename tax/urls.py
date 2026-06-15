from django.urls import path

from . import views

urlpatterns = [
    path('tax/', views.tax_summary, name='tax_summary'),
]
