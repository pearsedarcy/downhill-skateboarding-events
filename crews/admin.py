from django.contrib import admin
from .models import Crew, CrewMembership, CrewInvitation, CrewActivity


@admin.register(Crew)
class CrewAdmin(admin.ModelAdmin):
    list_display = ['name', 'crew_type', 'city', 'country', 'member_count', 'is_verified', 'is_active', 'created_at']
    list_filter = ['crew_type', 'primary_discipline', 'is_verified', 'is_active', 'country']
    search_fields = ['name', 'description', 'city']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Visual Identity', {
            'fields': ('logo', 'banner')
        }),
        ('Location & Type', {
            'fields': ('country', 'city', 'crew_type', 'primary_discipline')
        }),
        ('Social Links', {
            'fields': ('website', 'instagram', 'youtube')
        }),
        ('Status', {
            'fields': ('is_verified', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(CrewMembership)
class CrewMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'crew', 'role', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'is_public']
    search_fields = ['user__username', 'crew__name', 'nickname']
    raw_id_fields = ['user', 'crew', 'invited_by']


@admin.register(CrewInvitation)
class CrewInvitationAdmin(admin.ModelAdmin):
    list_display = ['invitee_email', 'crew', 'inviter', 'proposed_role', 'is_accepted', 'is_declined', 'created_at']
    list_filter = ['is_accepted', 'is_declined', 'proposed_role']
    search_fields = ['invitee_email', 'crew__name', 'inviter__username']
    raw_id_fields = ['crew', 'inviter', 'invitee_user']


@admin.register(CrewActivity)
class CrewActivityAdmin(admin.ModelAdmin):
    list_display = ['crew', 'activity_type', 'user', 'target_user', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['crew__name', 'user__username', 'description']
    raw_id_fields = ['crew', 'user', 'target_user']
    readonly_fields = ['created_at']
