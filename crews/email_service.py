"""
Email notification service for crew-related activities.

Handles sending email notifications for:
- Crew invitations
- Membership changes
- Role assignments
- Welcome messages
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.sites.models import Site
import logging

logger = logging.getLogger(__name__)


class CrewEmailService:
    """Service class for handling crew-related email notifications."""
    
    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.enabled = getattr(settings, 'CREW_NOTIFICATIONS_ENABLED', True)
    
    def _get_site_domain(self):
        """Get the current site domain for building absolute URLs."""
        try:
            current_site = Site.objects.get_current()
            return f"https://{current_site.domain}"
        except:
            return "https://skatedownhills.com"  # Fallback
    
    def _send_email(self, subject, template_name, context, recipient_email, recipient_name=None):
        """
        Send an email using HTML template with text fallback.
        
        Args:
            subject: Email subject line
            template_name: Template name (without .html extension)
            context: Template context dictionary
            recipient_email: Recipient email address
            recipient_name: Optional recipient name
        """
        if not self.enabled:
            logger.info(f"Email notifications disabled. Would send: {subject} to {recipient_email}")
            return False
        
        try:
            # Add common context variables
            context.update({
                'site_domain': self._get_site_domain(),
                'site_name': 'Skate Downhills',
                'recipient_name': recipient_name or recipient_email.split('@')[0],
            })
            
            # Render HTML and text versions
            html_content = render_to_string(f'crews/emails/{template_name}.html', context)
            text_content = strip_tags(html_content)
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[recipient_email],
            )
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            logger.info(f"Email sent successfully: {subject} to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            return False
    
    def send_crew_invitation(self, invitation):
        """
        Send email notification for crew invitation.
        
        Args:
            invitation: CrewInvitation instance
        """
        context = {
            'invitation': invitation,
            'crew': invitation.crew,
            'inviter': invitation.inviter,
            'accept_url': reverse('crews:accept_invitation', args=[invitation.id]),
            'decline_url': reverse('crews:decline_invitation', args=[invitation.id]),
            'crew_url': reverse('crews:detail', args=[invitation.crew.slug]),
        }
        
        # Determine recipient info
        if invitation.invitee_user:
            recipient_email = invitation.invitee_user.email
            recipient_name = invitation.invitee_user.get_full_name() or invitation.invitee_user.username
        else:
            recipient_email = invitation.invitee_email
            recipient_name = invitation.invitee_email.split('@')[0]
        
        subject = f"You're invited to join {invitation.crew.name} on Skate Downhills"
        
        return self._send_email(
            subject=subject,
            template_name='crew_invitation',
            context=context,
            recipient_email=recipient_email,
            recipient_name=recipient_name
        )
    
    def send_invitation_accepted(self, invitation, new_member):
        """
        Send notification to crew admins when invitation is accepted.
        
        Args:
            invitation: CrewInvitation instance
            new_member: User who accepted the invitation
        """
        # Get crew admins and owners to notify
        admin_memberships = invitation.crew.memberships.filter(
            role__in=['OWNER', 'ADMIN'],
            is_active=True
        ).select_related('user')
        
        context = {
            'crew': invitation.crew,
            'new_member': new_member,
            'invitation': invitation,
            'crew_url': reverse('crews:detail', args=[invitation.crew.slug]),
            'member_profile_url': reverse('profiles:user_profile', args=[new_member.username]),
        }
        
        subject = f"{new_member.username} joined {invitation.crew.name}"
        
        # Send to each admin
        for membership in admin_memberships:
            if membership.user.email and membership.user != new_member:
                self._send_email(
                    subject=subject,
                    template_name='member_joined',
                    context=context,
                    recipient_email=membership.user.email,
                    recipient_name=membership.user.get_full_name() or membership.user.username
                )
    
    def send_welcome_message(self, membership):
        """
        Send welcome email to new crew member.
        
        Args:
            membership: CrewMembership instance
        """
        context = {
            'membership': membership,
            'crew': membership.crew,
            'user': membership.user,
            'crew_url': reverse('crews:detail', args=[membership.crew.slug]),
            'profile_url': reverse('profiles:user_profile', args=[membership.user.username]),
        }
        
        subject = f"Welcome to {membership.crew.name}!"
        
        return self._send_email(
            subject=subject,
            template_name='welcome_to_crew',
            context=context,
            recipient_email=membership.user.email,
            recipient_name=membership.user.get_full_name() or membership.user.username
        )
    
    def send_role_changed(self, membership, old_role, changed_by):
        """
        Send notification when member's role is changed.
        
        Args:
            membership: CrewMembership instance
            old_role: Previous role
            changed_by: User who made the change
        """
        context = {
            'membership': membership,
            'crew': membership.crew,
            'user': membership.user,
            'old_role': old_role,
            'new_role': membership.get_role_display(),
            'changed_by': changed_by,
            'crew_url': reverse('crews:detail', args=[membership.crew.slug]),
        }
        
        subject = f"Your role in {membership.crew.name} has been updated"
        
        return self._send_email(
            subject=subject,
            template_name='role_changed',
            context=context,
            recipient_email=membership.user.email,
            recipient_name=membership.user.get_full_name() or membership.user.username
        )
    
    def send_member_left(self, crew, user, admin_user):
        """
        Send notification to crew admins when a member leaves.
        
        Args:
            crew: Crew instance
            user: User who left
            admin_user: Admin to notify
        """
        context = {
            'crew': crew,
            'departed_user': user,
            'crew_url': reverse('crews:detail', args=[crew.slug]),
        }
        
        subject = f"{user.username} left {crew.name}"
        
        return self._send_email(
            subject=subject,
            template_name='member_left',
            context=context,
            recipient_email=admin_user.email,
            recipient_name=admin_user.get_full_name() or admin_user.username
        )


# Singleton instance
crew_email_service = CrewEmailService()
