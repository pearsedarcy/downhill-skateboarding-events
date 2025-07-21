from django.urls import path
from . import views

app_name = 'results'

urlpatterns = [
    # Results views
    path('', views.results_list, name='results_list'),
    path('upload/<int:event_id>/', views.upload_results, name='upload_results'),
    path('upload/bracket/<int:event_id>/', views.upload_bracket_results, name='upload_bracket_results'),
    path('view/<int:event_id>/', views.view_results, name='view_results'),
    
    # League views
    path('leagues/', views.league_list, name='league_list'),
    
    # League management - these MUST come before the slug pattern
    path('league/create/', views.manage_league, name='create_league'),
    path('league/<slug:slug>/edit/', views.manage_league, name='edit_league'),
    path('league/<slug:slug>/events/', views.manage_league_events, name='manage_league_events'),
    path('league/<slug:slug>/disciplines/', views.manage_league_disciplines, name='manage_league_disciplines'),
    path('league/<slug:slug>/recalculate/', views.recalculate_league, name='recalculate_league'),
    
    # League detail view - this MUST come after specific paths
    path('league/<slug:slug>/', views.league_standings, name='league_standings'),
]
