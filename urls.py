from django.urls import path
from . import views

urlpatterns = [
    path('', views.summary_report, name='summary_report'),
    path('summary/', views.summary_report, name='summary_report'),
    path('health/', views.health_check, name='health_check'),
    path('wait_event_summary/', views.wait_event_summary, name='wait_event_summary'),
    path('top-10/', views.top_10_checklists, name='top_10_checklists'),
]