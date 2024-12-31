from django.contrib import admin
from .models import League, Result, TimeTrialResult, KnockoutResult, LeagueStanding

@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    filter_horizontal = ('events',)
    search_fields = ('name',)

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('event', 'result_type', 'uploaded_at', 'uploaded_by', 'is_final')
    list_filter = ('result_type', 'is_final')
    search_fields = ('event__title',)

@admin.register(TimeTrialResult)
class TimeTrialResultAdmin(admin.ModelAdmin):
    list_display = ('result', 'competitor', 'position', 'time', 'points')
    list_filter = ('result__event',)
    search_fields = ('competitor__user__username',)
    ordering = ('position',)

@admin.register(KnockoutResult)
class KnockoutResultAdmin(admin.ModelAdmin):
    list_display = ('result', 'round', 'winner', 'loser', 'match_number')
    list_filter = ('round', 'result__event')
    search_fields = ('winner__user__username', 'loser__user__username')

@admin.register(LeagueStanding)
class LeagueStandingAdmin(admin.ModelAdmin):
    list_display = ('league', 'competitor', 'points', 'position', 'events_competed')
    list_filter = ('league',)
    search_fields = ('competitor__user__username',)
    ordering = ('-points',)
