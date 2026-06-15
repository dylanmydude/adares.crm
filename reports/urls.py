from django.urls import path

from . import views

urlpatterns = [
    path('reports/', views.report_list, name='report_list'),
    path('reports/generate/<str:report_type>/', views.report_generate, name='report_generate'),
    path('reports/<int:pk>/download/', views.report_download, name='report_download'),
]
