"""
Admin configuration for the profiles application.

Provides admin interface for managing user profiles with enhanced features using Unfold.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from unfold.admin import ModelAdmin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    """Enhanced admin interface for UserProfile model using Unfold"""
    
    list_display = [
        'user_username', 'display_name', 'get_completion_badge', 
        'skating_style', 'skill_level', 'profile_visibility',
        'created_at', 'updated_at'
    ]
    
    list_filter = [
        'skating_style', 'profile_visibility', 'skill_level', 
        'stance', 'country', 'created_at'
    ]
    
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 
        'user__last_name', 'display_name', 'bio', 'city', 'country'
    ]
    
    readonly_fields = [
        'profile_completion_percentage', 'created_at', 'updated_at',
        'get_avatar_preview', 'get_profile_stats'
    ]
    
    fieldsets = (
        ('User Information', {
            'fields': (
                ('user', 'display_name'),
                ('profile_completion_percentage',),
                ('get_avatar_preview', 'avatar'),
            )
        }),
        ('Personal Information', {
            'fields': (
                'bio',
                ('country', 'city'),
                ('show_real_name', 'show_location'),
            )
        }),
        ('Skateboarding Profile', {
            'fields': (
                ('skating_style', 'stance'),
                ('skill_level', 'years_skating'),
                'primary_setup',
            )
        }),
        ('Social Media', {
            'fields': (
                'instagram', 'youtube', 'website'
            ),
            'classes': ('collapse',)
        }),
        ('Privacy & Settings', {
            'fields': (
                'profile_visibility',
            )
        }),
        ('Statistics', {
            'fields': (
                'get_profile_stats',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',)
        }),
    )
    
    def user_username(self, obj):
        """Display username as a link to user admin"""
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.user.id, obj.user.username
        )
    user_username.short_description = 'Username'
    user_username.admin_order_field = 'user__username'
    
    def get_completion_badge(self, obj):
        """Display completion percentage as a colored badge"""
        percentage = obj.profile_completion_percentage
        if percentage >= 80:
            color = 'green'
        elif percentage >= 50:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, f"{percentage}%"
        )
    get_completion_badge.short_description = 'Completion'
    get_completion_badge.admin_order_field = 'profile_completion_percentage'
    
    def get_avatar_preview(self, obj):
        """Display avatar preview in admin"""
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; border-radius: 50%;" />',
                obj.avatar.url
            )
        return "No avatar"
    get_avatar_preview.short_description = 'Avatar Preview'
    
    def get_profile_stats(self, obj):
        """Display profile statistics"""
        # This would integrate with events, crews, etc. when available
        stats = []
        
        # Basic profile stats
        stats.append(f"Profile completion: {obj.profile_completion_percentage}%")
        
        if obj.skating_style:
            stats.append(f"Skating style: {obj.get_skating_style_display()}")
        
        if obj.skill_level:
            stats.append(f"Skill level: {obj.skill_level}/10")
        
        if obj.years_skating:
            stats.append(f"Years skating: {obj.years_skating}")
        
        location = obj.get_location_display()
        if location:
            stats.append(f"Location: {location}")
        
        return format_html('<br>'.join(stats)) if stats else "No statistics available"
    get_profile_stats.short_description = 'Profile Statistics'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')
    
    actions = ['recalculate_completion']
    
    def recalculate_completion(self, request, queryset):
        """Admin action to recalculate completion percentages"""
        updated = 0
        for profile in queryset:
            profile.calculate_completion_percentage()
            updated += 1
        
        self.message_user(
            request,
            f'Successfully recalculated completion for {updated} profiles.'
        )
    recalculate_completion.short_description = "Recalculate completion percentages"
