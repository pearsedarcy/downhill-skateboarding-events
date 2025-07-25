"""
Email service for sending different types of notifications and communications.

This module handles sending various types of emails to users based on their
communication preferences, including welcome emails, event notifications,
crew invitations, community news, newsletters, and marketing emails.
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from profiles.models import UserProfile
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service class for handling all email communications."""
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@downhillskating.com')
    
    def send_welcome_email(self, user):
        """
        Send welcome email to new users.
        
        Args:
            user: User instance
        """
        try:
            subject = 'Welcome to the Downhill Skateboarding Community!'
            
            context = {
                'user': user,
            }
            
            # Render email templates
            html_message = render_to_string('emails/welcome_email.html', context)
            text_message = render_to_string('emails/welcome_email.txt', context)
            
            # Send email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=self.from_email,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Welcome email sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {e}")
    
    def send_event_notification(self, event, users=None):
        """
        Send event notification to users who opted in for event notifications.
        
        Args:
            event: Event instance
            users: Optional list of specific users to notify (defaults to all eligible users)
        """
        try:
            if users is None:
                # Get users who opted in for event notifications
                users = User.objects.filter(
                    profile__email_event_notifications=True,
                    is_active=True
                ).exclude(email='')
            
            subject = f'New Event: {event.title}'
            
            for user in users:
                context = {
                    'user': user,
                    'event': event,
                }
                
                # Render email templates
                html_message = render_to_string('emails/event_notification.html', context)
                text_message = render_to_string('emails/event_notification.txt', context)
                
                # Send email
                send_mail(
                    subject=subject,
                    message=text_message,
                    from_email=self.from_email,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=True,  # Don't fail for individual email errors
                )
            
            logger.info(f"Event notification sent for {event.title} to {len(users)} users")
            
        except Exception as e:
            logger.error(f"Failed to send event notification for {event.title}: {e}")
    
    def send_crew_invitation(self, invitation, inviter, crew):
        """
        Send crew invitation email to invited user.
        
        Args:
            invitation: CrewInvitation instance
            inviter: User who sent the invitation
            crew: Crew instance
        """
        try:
            # Check if user opted in for crew invitations
            if not invitation.invited_user.profile.email_crew_invites:
                logger.info(f"User {invitation.invited_user.email} has opted out of crew invitations")
                return
            
            subject = f'Invitation to join {crew.name} crew'
            
            context = {
                'user': invitation.invited_user,
                'crew': crew,
                'inviter': inviter,
                'invitation': invitation,
                'invitation_message': getattr(invitation, 'message', ''),
            }
            
            # Render email templates
            html_message = render_to_string('emails/crew_invitation.html', context)
            
            # Send email
            send_mail(
                subject=subject,
                message=f"You've been invited to join the {crew.name} crew by {inviter.profile.get_display_name()}. Check out the invitation on our platform!",
                from_email=self.from_email,
                recipient_list=[invitation.invited_user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Crew invitation sent to {invitation.invited_user.email} for crew {crew.name}")
            
        except Exception as e:
            logger.error(f"Failed to send crew invitation to {invitation.invited_user.email}: {e}")
    
    def send_community_news(self, featured_rider=None, recent_events=None, safety_tip=None, 
                          upcoming_events=None, community_stats=None):
        """
        Send community news email to users who opted in.
        
        Args:
            featured_rider: Featured rider of the period
            recent_events: List of recent highlighted events
            safety_tip: Safety tip to include
            upcoming_events: List of upcoming events to promote
            community_stats: Dictionary of community statistics
        """
        try:
            # Get users who opted in for community news
            users = User.objects.filter(
                profile__email_community_news=True,
                is_active=True
            ).exclude(email='')
            
            subject = 'Community Spotlight - What\'s Happening in Skateboarding'
            
            for user in users:
                context = {
                    'user': user,
                    'featured_rider': featured_rider,
                    'recent_events': recent_events or [],
                    'safety_tip': safety_tip,
                    'upcoming_events': upcoming_events or [],
                    'community_stats': community_stats or {},
                }
                
                # Render email template
                html_message = render_to_string('emails/community_news.html', context)
                
                # Send email
                send_mail(
                    subject=subject,
                    message="Community news update - check out what's happening in our skateboarding community!",
                    from_email=self.from_email,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=True,
                )
            
            logger.info(f"Community news sent to {len(users)} users")
            
        except Exception as e:
            logger.error(f"Failed to send community news: {e}")
    
    def send_monthly_newsletter(self, month_name, year, monthly_stats=None, 
                              featured_content=None, gear_review=None, 
                              tips_section=None, upcoming_events=None,
                              safety_focus=None, community_shoutouts=None):
        """
        Send monthly newsletter to subscribed users.
        
        Args:
            month_name: Name of the month
            year: Year
            monthly_stats: Dictionary of monthly statistics
            featured_content: Dictionary with featured event, rider, etc.
            gear_review: Gear review content
            tips_section: List of tips and techniques
            upcoming_events: List of upcoming events
            safety_focus: Safety focus content
            community_shoutouts: List of community achievements
        """
        try:
            # Get users who opted in for newsletter
            users = User.objects.filter(
                profile__email_newsletter=True,
                is_active=True
            ).exclude(email='')
            
            subject = f'{month_name} {year} Newsletter - Your Monthly Skateboarding Digest'
            
            for user in users:
                context = {
                    'user': user,
                    'month_name': month_name,
                    'year': year,
                    'monthly_stats': monthly_stats or {},
                    'featured_content': featured_content or {},
                    'gear_review': gear_review,
                    'tips_section': tips_section or [],
                    'upcoming_events': upcoming_events or [],
                    'safety_focus': safety_focus,
                    'community_shoutouts': community_shoutouts or [],
                }
                
                # Render email template
                html_message = render_to_string('emails/monthly_newsletter.html', context)
                
                # Send email
                send_mail(
                    subject=subject,
                    message=f"Your {month_name} {year} skateboarding newsletter is ready!",
                    from_email=self.from_email,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=True,
                )
            
            logger.info(f"Monthly newsletter sent to {len(users)} users")
            
        except Exception as e:
            logger.error(f"Failed to send monthly newsletter: {e}")
    
    def send_marketing_email(self, offer, partner_info=None, why_sharing=None):
        """
        Send marketing/promotional email to users who opted in.
        
        Args:
            offer: Dictionary containing offer details
            partner_info: Information about the partner/sponsor
            why_sharing: Explanation of why we're sharing this offer
        """
        try:
            # Get users who opted in for marketing emails
            users = User.objects.filter(
                profile__email_marketing=True,
                is_active=True
            ).exclude(email='')
            
            subject = f'Special Offer: {offer.get("title", "Exclusive Deal for Skaters")}'
            
            for user in users:
                context = {
                    'user': user,
                    'offer': offer,
                    'partner_info': partner_info,
                    'why_sharing': why_sharing,
                }
                
                # Render email template
                html_message = render_to_string('emails/marketing_email.html', context)
                
                # Send email
                send_mail(
                    subject=subject,
                    message=f"Special offer available: {offer.get('title', 'Exclusive skateboarding gear deal')}",
                    from_email=self.from_email,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=True,
                )
            
            logger.info(f"Marketing email sent to {len(users)} users")
            
        except Exception as e:
            logger.error(f"Failed to send marketing email: {e}")
    
    def get_email_stats(self):
        """
        Get statistics about email preferences across all users.
        
        Returns:
            Dictionary with email preference statistics
        """
        try:
            total_users = UserProfile.objects.filter(user__is_active=True).count()
            
            stats = {
                'total_active_users': total_users,
                'event_notifications': UserProfile.objects.filter(
                    user__is_active=True, 
                    email_event_notifications=True
                ).count(),
                'community_news': UserProfile.objects.filter(
                    user__is_active=True, 
                    email_community_news=True
                ).count(),
                'newsletter': UserProfile.objects.filter(
                    user__is_active=True, 
                    email_newsletter=True
                ).count(),
                'crew_invites': UserProfile.objects.filter(
                    user__is_active=True, 
                    email_crew_invites=True
                ).count(),
                'marketing': UserProfile.objects.filter(
                    user__is_active=True, 
                    email_marketing=True
                ).count(),
            }
            
            # Calculate percentages
            for key in ['event_notifications', 'community_news', 'newsletter', 'crew_invites', 'marketing']:
                if total_users > 0:
                    stats[f'{key}_percentage'] = round((stats[key] / total_users) * 100, 1)
                else:
                    stats[f'{key}_percentage'] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get email stats: {e}")
            return {}


# Global instance for easy importing
email_service = EmailService()
