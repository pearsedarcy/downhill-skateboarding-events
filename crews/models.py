"""
Models for crew management in the downhill skateboarding events application.

Defines models for skateboarding crews, crew memberships, and crew-related
functionality including roles, permissions, and associations with events/leagues.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from cloudinary.models import CloudinaryField
from django_countries.fields import CountryField
from search.models import SearchableModel


class Crew(SearchableModel):
    """
    Model representing a skateboarding crew/team.
    
    A crew is a group of skateboarders who organize events, compete together,
    or share common interests in the skateboarding community.
    """
    
    CREW_TYPE_CHOICES = [
        ('CASUAL', 'Casual Crew'),
        ('COMPETITIVE', 'Competitive Team'),
        ('ORGANIZER', 'Event Organizer'),
        ('SPONSOR', 'Sponsor/Brand'),
        ('SHOP', 'Skate Shop'),
    ]
    
    DISCIPLINE_CHOICES = [
        ('DOWNHILL', 'Downhill'),
        ('STREET', 'Street'),
        ('FREESTYLE', 'Freestyle'),
        ('FREERIDE', 'Freeride'),
        ('DANCING', 'Dancing'),
        ('CRUISING', 'Cruising'),
        ('MIXED', 'Mixed Disciplines'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, help_text="Describe your crew's mission and activities")
    
    # Visual Identity
    logo = CloudinaryField("logo", null=True, blank=True, help_text="Crew logo or emblem")
    banner = CloudinaryField("banner", null=True, blank=True, help_text="Crew banner image")
    
    # Location & Identity
    country = CountryField(blank_label="(select country)", null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    crew_type = models.CharField(max_length=20, choices=CREW_TYPE_CHOICES, default='CASUAL')
    primary_discipline = models.CharField(max_length=20, choices=DISCIPLINE_CHOICES, default='MIXED')
    
    # Social Links
    website = models.URLField(blank=True)
    instagram = models.CharField(max_length=100, blank=True, help_text="Instagram handle (without @)")
    facebook = models.CharField(max_length=100, blank=True, help_text="Facebook page URL")
    youtube = models.URLField(blank=True)
    
    # Status
    is_verified = models.BooleanField(default=False, help_text="Verified crews get special badges")
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Search configuration
    search_fields = ['name', 'description', 'city']
    search_field_weights = {
        'name': 'A',
        'description': 'B', 
        'city': 'C'
    }
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Crew'
        verbose_name_plural = 'Crews'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    @property
    def member_count(self):
        """Get total number of crew members."""
        return self.memberships.filter(is_active=True).count()
    
    @property
    def owners(self):
        """Get all crew owners."""
        return User.objects.filter(
            crew_memberships__crew=self,
            crew_memberships__role='OWNER',
            crew_memberships__is_active=True
        )
    
    @property
    def admins(self):
        """Get all crew admins (owners + admins)."""
        return User.objects.filter(
            crew_memberships__crew=self,
            crew_memberships__role__in=['OWNER', 'ADMIN'],
            crew_memberships__is_active=True
        )
    
    def can_manage(self, user):
        """Check if a user can manage this crew."""
        if not user.is_authenticated:
            return False
        return self.memberships.filter(
            user=user,
            role__in=['OWNER', 'ADMIN'],
            is_active=True
        ).exists()
    
    def can_create_events(self, user):
        """Check if a user can create events for this crew."""
        if not user.is_authenticated:
            return False
        
        try:
            membership = self.memberships.get(user=user, is_active=True)
            return membership.has_event_permission('create')
        except CrewMembership.DoesNotExist:
            return False
    
    def can_edit_events(self, user):
        """Check if a user can edit this crew's events."""
        if not user.is_authenticated:
            return False
        
        try:
            membership = self.memberships.get(user=user, is_active=True)
            return membership.has_event_permission('edit')
        except CrewMembership.DoesNotExist:
            return False
    
    def can_publish_events(self, user):
        """Check if a user can publish this crew's events."""
        if not user.is_authenticated:
            return False
        
        try:
            membership = self.memberships.get(user=user, is_active=True)
            return membership.has_event_permission('publish')
        except CrewMembership.DoesNotExist:
            return False
    
    def can_delegate_permissions(self, user):
        """Check if a user can delegate permissions for this crew."""
        if not user.is_authenticated:
            return False
        
        try:
            membership = self.memberships.get(user=user, is_active=True)
            return membership.has_event_permission('delegate')
        except CrewMembership.DoesNotExist:
            return False
    
    def get_user_membership(self, user):
        """Get user's membership in this crew."""
        if not user.is_authenticated:
            return None
        
        try:
            return self.memberships.get(user=user, is_active=True)
        except CrewMembership.DoesNotExist:
            return None


class CrewMembership(models.Model):
    """
    Model representing a user's membership in a crew.
    
    Defines roles and permissions for crew members.
    """
    
    ROLE_CHOICES = [
        ('OWNER', 'Owner'),           # Full control, can delete crew
        ('ADMIN', 'Admin'),           # Can manage members, events, settings
        ('EVENT_MANAGER', 'Event Manager'),  # Can create/manage events
        ('MEMBER', 'Member'),         # Basic member
        ('PENDING', 'Pending'),       # Invited but not accepted
    ]
    
    crew = models.ForeignKey(Crew, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crew_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='MEMBER')
    
    # Crew Permissions - Event Management
    can_create_events = models.BooleanField(
        default=False, 
        help_text="Can create events on behalf of the crew"
    )
    can_edit_events = models.BooleanField(
        default=False, 
        help_text="Can edit crew events created by others"
    )
    can_publish_events = models.BooleanField(
        default=False, 
        help_text="Can publish draft events to make them public"
    )
    can_delegate_permissions = models.BooleanField(
        default=False, 
        help_text="Can grant/revoke permissions to other crew members"
    )
    
    # Member profile within crew
    nickname = models.CharField(max_length=50, blank=True, help_text="Crew nickname (optional)")
    bio = models.TextField(blank=True, help_text="Your role/bio within the crew")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True, help_text="Show membership publicly")
    
    # Timestamps
    joined_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='crew_invitations_sent'
    )
    
    class Meta:
        unique_together = ['crew', 'user']
        ordering = ['role', 'joined_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.crew.name} ({self.get_role_display()})"
    
    def can_manage(self):
        """Check if this member can manage crew settings and members."""
        return self.role in ['OWNER', 'ADMIN']
    
    @property
    def can_invite_members(self):
        """Check if this member can invite other members."""
        return self.role in ['OWNER', 'ADMIN']
    
    @property
    def can_manage_events(self):
        """Check if this member can manage crew events."""
        return self.role in ['OWNER', 'ADMIN', 'EVENT_MANAGER']
    
    # Enhanced Permission Methods
    def has_event_permission(self, permission_type):
        """
        Check if member has specific event permission.
        
        Args:
            permission_type (str): 'create', 'edit', 'publish', or 'delegate'
        
        Returns:
            bool: True if member has the permission
        """
        if not self.is_active:
            return False
            
        # Owners and Admins have all permissions by default
        if self.role in ['OWNER', 'ADMIN']:
            return True
            
        # Check specific permissions
        permission_map = {
            'create': self.can_create_events,
            'edit': self.can_edit_events,
            'publish': self.can_publish_events,
            'delegate': self.can_delegate_permissions,
        }
        
        return permission_map.get(permission_type, False)
    
    def can_delegate_to_member(self, target_member):
        """
        Check if this member can delegate permissions to another member.
        
        Args:
            target_member (CrewMembership): Target member to delegate to
            
        Returns:
            bool: True if delegation is allowed
        """
        if not self.has_event_permission('delegate'):
            return False
            
        # Can't delegate to yourself
        if target_member.user == self.user:
            return False
            
        # Can't delegate to higher or equal role (except owners can delegate to admins)
        role_hierarchy = {'OWNER': 4, 'ADMIN': 3, 'EVENT_MANAGER': 2, 'MEMBER': 1, 'PENDING': 0}
        
        my_level = role_hierarchy.get(self.role, 0)
        target_level = role_hierarchy.get(target_member.role, 0)
        
        # Owners can delegate to anyone except other owners
        if self.role == 'OWNER' and target_member.role != 'OWNER':
            return True
            
        # Admins can delegate to event managers and members
        if self.role == 'ADMIN' and target_member.role in ['EVENT_MANAGER', 'MEMBER']:
            return True
            
        return False
    
    def grant_permission(self, permission_type, granted_by=None):
        """
        Grant a specific permission to this member.
        
        Args:
            permission_type (str): 'create', 'edit', 'publish', or 'delegate'
            granted_by (User): User who granted the permission
        """
        if permission_type == 'create':
            self.can_create_events = True
        elif permission_type == 'edit':
            self.can_edit_events = True
        elif permission_type == 'publish':
            self.can_publish_events = True
        elif permission_type == 'delegate':
            self.can_delegate_permissions = True
        
        self.save()
        
        # Log the permission change
        if granted_by:
            CrewActivity.objects.create(
                crew=self.crew,
                activity_type='MEMBER_PROMOTED',
                user=granted_by,
                target_user=self.user,
                description=f"Granted {permission_type} permission to {self.user.username}",
                metadata={'permission_type': permission_type, 'action': 'granted'}
            )
    
    def revoke_permission(self, permission_type, revoked_by=None):
        """
        Revoke a specific permission from this member.
        
        Args:
            permission_type (str): 'create', 'edit', 'publish', or 'delegate'
            revoked_by (User): User who revoked the permission
        """
        if permission_type == 'create':
            self.can_create_events = False
        elif permission_type == 'edit':
            self.can_edit_events = False
        elif permission_type == 'publish':
            self.can_publish_events = False
        elif permission_type == 'delegate':
            self.can_delegate_permissions = False
        
        self.save()
        
        # Log the permission change
        if revoked_by:
            CrewActivity.objects.create(
                crew=self.crew,
                activity_type='MEMBER_PROMOTED',  # We'll use this for permission changes
                user=revoked_by,
                target_user=self.user,
                description=f"Revoked {permission_type} permission from {self.user.username}",
                metadata={'permission_type': permission_type, 'action': 'revoked'}
            )
    
    def get_permission_summary(self):
        """
        Get a summary of all permissions for this member.
        
        Returns:
            dict: Dictionary of permission types and their status
        """
        return {
            'create': self.has_event_permission('create'),
            'edit': self.has_event_permission('edit'),
            'publish': self.has_event_permission('publish'),
            'delegate': self.has_event_permission('delegate'),
            'role_based': self.role in ['OWNER', 'ADMIN'],
        }


class CrewInvitation(models.Model):
    """
    Model for crew invitations sent to users.
    
    Tracks pending invitations to join crews.
    """
    
    crew = models.ForeignKey(Crew, on_delete=models.CASCADE, related_name='invitations')
    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_crew_invitations')
    invitee_email = models.EmailField(help_text="Email of person to invite")
    invitee_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='received_crew_invitations',
        help_text="User account if they already exist"
    )
    
    message = models.TextField(blank=True, help_text="Personal message with invitation")
    proposed_role = models.CharField(
        max_length=20, 
        choices=CrewMembership.ROLE_CHOICES,
        default='MEMBER'
    )
    
    # Status
    is_accepted = models.BooleanField(default=False)
    is_declined = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(help_text="When invitation expires")
    
    class Meta:
        unique_together = ['crew', 'invitee_email']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invitation to {self.invitee_email} for {self.crew.name}"
    
    @property
    def is_expired(self):
        """Check if invitation has expired."""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    @property
    def is_pending(self):
        """Check if invitation is still pending."""
        return not self.is_accepted and not self.is_declined and not self.is_expired


class CrewActivity(models.Model):
    """
    Model to track crew activities for activity feeds.
    
    Records important crew events like member joins, event creation, etc.
    """
    
    ACTIVITY_TYPES = [
        ('MEMBER_JOINED', 'Member Joined'),
        ('MEMBER_LEFT', 'Member Left'),
        ('MEMBER_PROMOTED', 'Member Promoted'),
        ('EVENT_CREATED', 'Event Created'),
        ('LEAGUE_CREATED', 'League Created'),
        ('CREW_UPDATED', 'Crew Updated'),
    ]
    
    crew = models.ForeignKey(Crew, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="User who performed the action")
    target_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='crew_activities_as_target',
        help_text="User affected by the action (for member actions)"
    )
    
    description = models.TextField(help_text="Description of the activity")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional activity data")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Crew Activities'
    
    def __str__(self):
        return f"{self.crew.name} - {self.get_activity_type_display()}"
