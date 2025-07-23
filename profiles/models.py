"""
Models for user profiles in the downhill skateboarding events application.

Defines the UserProfile model that extends the built-in Django User model
with additional skateboarding-specific information.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from cloudinary.models import CloudinaryField
from search.models import SearchableModel


# Choices for skateboarding-specific fields
SKATING_STYLES = [
    ('DOWNHILL', 'Downhill'),
    ('FREERIDE', 'Freeride'), 
    ('FREESTYLE', 'Freestyle'),
    ('CRUISING', 'Cruising'),
    ('DANCING', 'Dancing'),
    ('SLALOM', 'Slalom'),
    ('PUMPING', 'Pumping'),
    ('OTHER', 'Other')
]

STANCE_CHOICES = [
    ('REGULAR', 'Regular'),
    ('GOOFY', 'Goofy'),
    ('SWITCH', 'Switch')
]

PROFILE_VISIBILITY = [
    ('PUBLIC', 'Public to all'),
    ('COMMUNITY', 'Skateboarding community only'),
    ('CREWS', 'My crews only'),
    ('PRIVATE', 'Private')
]


class UserProfile(SearchableModel):
    """
    Enhanced user profile model with skateboarding-specific information.
    
    Extends the built-in Django User model through a one-to-one relationship.
    """
    
    # Core Information
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name="profile"
    )
    display_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Display name (optional, defaults to username)"
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text="A brief description about yourself (max 500 characters)"
    )
    avatar = CloudinaryField(
        "avatar",
        null=True,
        blank=True,
        help_text="Profile picture"
    )
    
    # Location
    country = models.CharField(
        max_length=100,
        blank=True,
        help_text="Your country"
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        help_text="Your city"
    )
    
    # Social Media
    instagram = models.CharField(
        max_length=100,
        blank=True,
        help_text="Your Instagram handle (without @)"
    )
    youtube = models.URLField(
        blank=True,
        help_text="Your YouTube channel URL"
    )
    website = models.URLField(
        blank=True,
        help_text="Your personal website"
    )
    
    # Skateboarding Profile
    skating_style = models.CharField(
        max_length=50,
        choices=SKATING_STYLES,
        blank=True,
        help_text="Your preferred skating style"
    )
    skill_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True,
        blank=True,
        help_text="Your skill level (1-10, where 10 is professional)"
    )
    years_skating = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="How many years you've been skating"
    )
    stance = models.CharField(
        max_length=20,
        choices=STANCE_CHOICES,
        blank=True,
        help_text="Your skateboarding stance"
    )
    
    # Equipment
    primary_setup = models.TextField(
        max_length=300,
        blank=True,
        help_text="Description of your main skateboard setup"
    )
    
    # Privacy & Preferences
    profile_visibility = models.CharField(
        max_length=20,
        choices=PROFILE_VISIBILITY,
        default='PUBLIC',
        help_text="Who can view your profile"
    )
    show_real_name = models.BooleanField(
        default=True,
        help_text="Show your real name on your profile"
    )
    show_location = models.BooleanField(
        default=True,
        help_text="Show your location on your profile"
    )
    
    # Statistics & Metadata
    profile_completion_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100)],
        help_text="Automatically calculated profile completion percentage"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Updated search fields to include new fields
    search_fields = ['user__username', 'display_name', 'bio', 'city', 'country', 'skating_style']
    search_field_weights = {
        'user__username': 'A',
        'display_name': 'A',
        'bio': 'B',
        'city': 'C',
        'country': 'C',
        'skating_style': 'B'
    }

    def __str__(self):
        return f"{self.user.username}'s profile"
    
    def get_display_name(self):
        """Return display name or username if display name is empty"""
        return self.display_name or self.user.username
    
    def get_full_name(self):
        """Return full name if available and show_real_name is True"""
        if self.show_real_name and (self.user.first_name or self.user.last_name):
            return f"{self.user.first_name} {self.user.last_name}".strip()
        return self.get_display_name()
    
    def calculate_completion_percentage(self):
        """Calculate profile completion percentage"""
        total_fields = 0
        completed_fields = 0
        
        # Core information (40% weight)
        core_fields = [
            ('bio', 10),
            ('avatar', 15),
            ('display_name', 5),
            ('country', 5),
            ('city', 5)
        ]
        
        # Skateboarding information (40% weight)
        skating_fields = [
            ('skating_style', 10),
            ('skill_level', 10),
            ('years_skating', 5),
            ('stance', 5),
            ('primary_setup', 10)
        ]
        
        # Social & other (20% weight)
        social_fields = [
            ('instagram', 5),
            ('youtube', 5),
            ('website', 5),
            ('profile_visibility', 5)  # Always completed due to default
        ]
        
        all_fields = core_fields + skating_fields + social_fields
        
        for field_name, weight in all_fields:
            total_fields += weight
            field_value = getattr(self, field_name)
            if field_value:  # Field has a value
                completed_fields += weight
        
        percentage = int((completed_fields / total_fields) * 100) if total_fields > 0 else 0
        
        # Update the field if it has changed
        if self.profile_completion_percentage != percentage:
            self.profile_completion_percentage = percentage
            self.save(update_fields=['profile_completion_percentage'])
        
        return percentage
    
    def get_location_display(self):
        """Return formatted location string"""
        if not self.show_location:
            return None
        
        location_parts = []
        if self.city:
            location_parts.append(self.city)
        if self.country:
            location_parts.append(self.country)
        
        return ", ".join(location_parts) if location_parts else None
    
    def get_skating_experience_display(self):
        """Return formatted skating experience"""
        experience_parts = []
        
        if self.skating_style:
            experience_parts.append(self.get_skating_style_display())
        
        if self.years_skating:
            years_text = "year" if self.years_skating == 1 else "years"
            experience_parts.append(f"{self.years_skating} {years_text}")
        
        if self.skill_level:
            experience_parts.append(f"Level {self.skill_level}")
        
        return " • ".join(experience_parts) if experience_parts else None
    
    def get_completion_suggestions(self):
        """Return a list of suggestions to complete the profile"""
        suggestions = []
        
        # Check for missing core fields
        if not self.bio:
            suggestions.append({
                'field': 'bio',
                'message': 'Add a bio to tell others about yourself',
                'weight': 10
            })
        
        if not self.avatar:
            suggestions.append({
                'field': 'avatar',
                'message': 'Upload a profile picture',
                'weight': 15
            })
        
        if not self.city:
            suggestions.append({
                'field': 'city',
                'message': 'Add your city to connect with local skaters',
                'weight': 5
            })
        
        # Check for missing skating information
        if not self.skating_style:
            suggestions.append({
                'field': 'skating_style',
                'message': 'Select your preferred skating style',
                'weight': 10
            })
        
        if not self.skill_level:
            suggestions.append({
                'field': 'skill_level',
                'message': 'Rate your skating skill level',
                'weight': 10
            })
        
        if not self.primary_setup:
            suggestions.append({
                'field': 'primary_setup',
                'message': 'Describe your skateboard setup',
                'weight': 10
            })
        
        # Check for missing social links
        if not self.instagram:
            suggestions.append({
                'field': 'instagram',
                'message': 'Add your Instagram handle',
                'weight': 5
            })
        
        # Sort by weight (highest first)
        suggestions.sort(key=lambda x: x['weight'], reverse=True)
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def get_social_links(self):
        """Return a dictionary of available social links"""
        social_links = {}
        
        if self.instagram:
            social_links['instagram'] = {
                'url': f'https://instagram.com/{self.instagram}',
                'display': f'@{self.instagram}',
                'icon': 'fab fa-instagram'
            }
        
        if self.youtube:
            social_links['youtube'] = {
                'url': self.youtube,
                'display': 'YouTube Channel',
                'icon': 'fab fa-youtube'
            }
        
        if self.website:
            social_links['website'] = {
                'url': self.website,
                'display': 'Website',
                'icon': 'fas fa-globe'
            }
        
        return social_links
    
    def get_average_rating(self):
        """Get average rating from event reviews (if available)"""
        # This would require a Review model relationship
        # For now, return None - can be implemented later
        return None

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ['-created_at']