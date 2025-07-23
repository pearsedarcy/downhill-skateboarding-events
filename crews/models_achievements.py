"""
Models for crew achievements and milestones system.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from crews.models import Crew


class CrewAchievement(models.Model):
    """
    Model for crew achievements and milestones.
    """
    
    ACHIEVEMENT_TYPES = [
        ('MEMBER_MILESTONE', 'Member Milestone'),
        ('EVENT_MILESTONE', 'Event Milestone'),
        ('ANNIVERSARY', 'Anniversary'),
        ('PARTICIPATION', 'Participation'),
        ('ORGANIZATION', 'Organization'),
        ('COMMUNITY', 'Community'),
        ('SPECIAL', 'Special Recognition'),
    ]
    
    ACHIEVEMENT_LEVELS = [
        ('BRONZE', 'Bronze'),
        ('SILVER', 'Silver'), 
        ('GOLD', 'Gold'),
        ('PLATINUM', 'Platinum'),
        ('LEGENDARY', 'Legendary'),
    ]
    
    crew = models.ForeignKey(Crew, on_delete=models.CASCADE, related_name='achievements')
    
    # Achievement details
    title = models.CharField(max_length=100)
    description = models.TextField()
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPES)
    level = models.CharField(max_length=20, choices=ACHIEVEMENT_LEVELS, default='BRONZE')
    
    # Achievement criteria
    criteria_met = models.JSONField(
        default=dict,
        help_text="JSON data about criteria met (e.g., member count, events organized)"
    )
    
    # Visual
    icon = models.CharField(
        max_length=50, 
        default='fas fa-trophy',
        help_text="FontAwesome icon class"
    )
    color = models.CharField(
        max_length=20,
        default='primary',
        help_text="Badge color (primary, secondary, accent, etc.)"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    earned_at = models.DateTimeField(auto_now_add=True)
    awarded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="If manually awarded"
    )
    
    class Meta:
        ordering = ['-earned_at']
        unique_together = ['crew', 'title']  # Prevent duplicate achievements
    
    def __str__(self):
        return f"{self.crew.name} - {self.title}"
    
    @property
    def level_color(self):
        """Get color class for achievement level."""
        color_map = {
            'BRONZE': 'warning',
            'SILVER': 'info', 
            'GOLD': 'warning',
            'PLATINUM': 'primary',
            'LEGENDARY': 'secondary'
        }
        return color_map.get(self.level, 'primary')


class AchievementTemplate(models.Model):
    """
    Templates for automatic achievement detection.
    """
    
    title = models.CharField(max_length=100)
    description = models.TextField()
    achievement_type = models.CharField(max_length=20, choices=CrewAchievement.ACHIEVEMENT_TYPES)
    level = models.CharField(max_length=20, choices=CrewAchievement.ACHIEVEMENT_LEVELS)
    
    # Criteria for automatic awarding
    criteria = models.JSONField(
        help_text="JSON criteria for automatic detection"
    )
    
    # Visual
    icon = models.CharField(max_length=50, default='fas fa-trophy')
    color = models.CharField(max_length=20, default='primary')
    
    # Status  
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['level', 'title']
    
    def __str__(self):
        return self.title
    
    def check_crew_eligibility(self, crew):
        """
        Check if a crew meets the criteria for this achievement.
        
        Args:
            crew (Crew): Crew to check
            
        Returns:
            bool: True if crew meets criteria
        """
        criteria = self.criteria
        
        # Member count achievements
        if criteria.get('min_members'):
            if crew.member_count < criteria['min_members']:
                return False
        
        # Event count achievements
        if criteria.get('min_events'):
            event_count = crew.events.filter(is_published=True).count()
            if event_count < criteria['min_events']:
                return False
        
        # Age achievements
        if criteria.get('min_age_days'):
            crew_age = (timezone.now() - crew.created_at).days
            if crew_age < criteria['min_age_days']:
                return False
        
        # Verification status
        if criteria.get('requires_verification', False):
            if not crew.is_verified:
                return False
        
        return True
    
    def award_to_crew(self, crew, awarded_by=None):
        """
        Award this achievement to a crew.
        
        Args:
            crew (Crew): Crew to award to
            awarded_by (User): Optional user who manually awarded it
            
        Returns:
            CrewAchievement: Created achievement instance
        """
        achievement, created = CrewAchievement.objects.get_or_create(
            crew=crew,
            title=self.title,
            defaults={
                'description': self.description,
                'achievement_type': self.achievement_type,
                'level': self.level,
                'icon': self.icon,
                'color': self.color,
                'awarded_by': awarded_by,
                'criteria_met': self._get_current_criteria_values(crew)
            }
        )
        
        return achievement, created
    
    def _get_current_criteria_values(self, crew):
        """Get current values for criteria tracking."""
        return {
            'member_count': crew.member_count,
            'event_count': crew.events.filter(is_published=True).count(),
            'crew_age_days': (timezone.now() - crew.created_at).days,
            'is_verified': crew.is_verified,
            'awarded_at': timezone.now().isoformat()
        }
