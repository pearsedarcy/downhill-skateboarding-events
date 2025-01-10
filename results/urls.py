from django.urls import path
from . import views

app_name = 'results'

urlpatterns = [
    path('', views.results_list, name='results_list'),
    path('upload/<int:event_id>/', views.upload_results, name='upload_results'),
    path('view/<int:event_id>/', views.view_results, name='view_results'),
    path('league/<slug:slug>/', views.league_standings, name='league_standings'),
    path('leagues/', views.league_list, name='league_list'),
]
