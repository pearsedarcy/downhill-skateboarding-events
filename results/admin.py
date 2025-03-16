from django.contrib import admin
from .models import League, Result, TimeTrialResult, KnockoutResult, LeagueStanding
from unfold.admin import ModelAdmin

@admin.register(League)
class LeagueAdmin(ModelAdmin):
    list_display = ('name', 'league_class', 'country', 'continent', 'event_count', 'created_at')
    list_filter = ('league_class', 'country', 'continent')
    search_fields = ('name',)
    readonly_fields = ('event_count',)
    
    def event_count(self, obj):
        return obj.league_events.count()
    event_count.short_description = 'Events'

@admin.register(Result)
class ResultAdmin(ModelAdmin):
    list_display = ('event', 'result_type', 'uploaded_at', 'uploaded_by', 'is_final')
    list_filter = ('result_type', 'is_final')
    search_fields = ('event__title',)

@admin.register(TimeTrialResult)
class TimeTrialResultAdmin(ModelAdmin):
    list_display = ('result', 'competitor', 'position', 'time', 'points')
    list_filter = ('result__event',)
    search_fields = ('competitor__user__username',)
    ordering = ('position',)

@admin.register(KnockoutResult)
class KnockoutResultAdmin(ModelAdmin):
    list_display = ('result', 'round', 'winner', 'loser', 'match_number')
    list_filter = ('round', 'result__event')
    search_fields = ('winner__user__username', 'loser__user__username')

@admin.register(LeagueStanding)
class LeagueStandingAdmin(ModelAdmin):
    list_display = ('league', 'competitor', 'points', 'position', 'events_competed')
    list_filter = ('league',)
    search_fields = ('competitor__user__username',)
    ordering = ('-points',)
