"""
Models for user profiles in the downhill skateboarding events application.

Defines the UserProfile model that extends the built-in Django User model
with additional skateboarding-specific information.
"""

from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from search.models import SearchableModel
from django_countries.fields import CountryField


class UserProfile(SearchableModel):
    """
    Extended user profile model with additional fields for skateboarders.
    
    Extends the built-in Django User model through a one-to-one relationship.
    """
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name="profile"
    )
    bio = models.TextField(
        blank=True,
        help_text="A brief description about yourself"
    )
    avatar = CloudinaryField(
        "avatar",
        null=True,
        blank=True,
        help_text="Profile picture"
    )
    instagram = models.CharField(
        max_length=100,
        blank=True,
        help_text="Your Instagram handle"
    )
    country = CountryField(
        blank_label="(select country)", 
        null=True, 
        blank=True,
        help_text="Your country of residence"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    search_fields = ['user__username', 'bio', 'country', 'location', 'skills']
    search_field_weights = {
        'user__username': 'A',
        'bio': 'B',
        'country': 'C',
        'location': 'C',
        'skills': 'C'
    }

    def __str__(self):
        return f"{self.user.username}'s profile"