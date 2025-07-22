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
    list_display = [
        'user', 'crew', 'role', 'is_active', 
        'can_create_events', 'can_edit_events', 'can_publish_events', 'can_delegate_permissions',
        'joined_at'
    ]
    list_filter = [
        'role', 'is_active', 'is_public', 
        'can_create_events', 'can_edit_events', 'can_publish_events', 'can_delegate_permissions'
    ]
    search_fields = ['user__username', 'crew__name', 'nickname']
    raw_id_fields = ['user', 'crew', 'invited_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'crew', 'role', 'nickname', 'bio')
        }),
        ('Event Permissions', {
            'fields': (
                'can_create_events', 
                'can_edit_events', 
                'can_publish_events', 
                'can_delegate_permissions'
            ),
            'description': 'Event management permissions for this crew member. Note: Owners and Admins automatically have all permissions regardless of these settings.'
        }),
        ('Status', {
            'fields': ('is_active', 'is_public')
        }),
        ('Metadata', {
            'fields': ('joined_at', 'invited_by'),
            'classes': ('collapse',)
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly = ['joined_at']
        if obj:  # Editing existing object
            readonly.extend(['user', 'crew'])  # Don't allow changing user/crew relationships
        return readonly


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
