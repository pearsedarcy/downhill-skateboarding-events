"""
Django management command to test crew email notifications.

Usage:
    python manage.py test_crew_emails --crew-slug=my-crew --user-email=test@example.com
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from crews.models import Crew, CrewInvitation, CrewMembership
from crews.email_service import crew_email_service
from django.utils import timezone


class Command(BaseCommand):
    help = 'Test crew email notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--crew-slug',
            type=str,
            required=True,
            help='Slug of the crew to use for testing',
        )
        parser.add_argument(
            '--user-email',
            type=str,
            required=True,
            help='Email address to send test emails to',
        )
        parser.add_argument(
            '--test-type',
            type=str,
            choices=['invitation', 'welcome', 'role_change', 'member_left', 'all'],
            default='all',
            help='Type of email to test',
        )

    def handle(self, *args, **options):
        crew_slug = options['crew_slug']
        user_email = options['user_email']
        test_type = options['test_type']

        try:
            crew = Crew.objects.get(slug=crew_slug)
        except Crew.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Crew with slug "{crew_slug}" does not exist')
            )
            return

        # Get or create a test user
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=f'test_user_{timezone.now().timestamp()}',
                email=user_email,
                first_name='Test',
                last_name='User'
            )
            self.stdout.write(f'Created test user: {user.username}')

        # Get crew owner for testing
        crew_owner = crew.memberships.filter(role='OWNER', is_active=True).first()
        if not crew_owner:
            self.stdout.write(
                self.style.ERROR('Crew has no owner. Cannot run tests.')
            )
            return

        if test_type in ['invitation', 'all']:
            self.test_invitation_email(crew, crew_owner.user, user_email)

        if test_type in ['welcome', 'all']:
            self.test_welcome_email(crew, user)

        if test_type in ['role_change', 'all']:
            self.test_role_change_email(crew, user, crew_owner.user)

        if test_type in ['member_left', 'all']:
            self.test_member_left_email(crew, user, crew_owner.user)

        self.stdout.write(
            self.style.SUCCESS('Email tests completed! Check your email and/or console output.')
        )

    def test_invitation_email(self, crew, inviter, user_email):
        """Test crew invitation email."""
        self.stdout.write('Testing invitation email...')
        
        # Create a test invitation
        invitation = CrewInvitation.objects.create(
            crew=crew,
            inviter=inviter,
            invitee_email=user_email,
            proposed_role='MEMBER',
            expires_at=timezone.now() + timezone.timedelta(days=30)
        )
        
        # Send email
        result = crew_email_service.send_crew_invitation(invitation)
        
        if result:
            self.stdout.write(self.style.SUCCESS('✅ Invitation email sent'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ Invitation email failed'))
        
        # Clean up
        invitation.delete()

    def test_welcome_email(self, crew, user):
        """Test welcome email."""
        self.stdout.write('Testing welcome email...')
        
        # Create a test membership
        membership = CrewMembership.objects.create(
            crew=crew,
            user=user,
            role='MEMBER',
            is_active=True
        )
        
        # Send email
        result = crew_email_service.send_welcome_message(membership)
        
        if result:
            self.stdout.write(self.style.SUCCESS('✅ Welcome email sent'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ Welcome email failed'))
        
        # Clean up
        membership.delete()

    def test_role_change_email(self, crew, user, changed_by):
        """Test role change email."""
        self.stdout.write('Testing role change email...')
        
        # Create a test membership
        membership = CrewMembership.objects.create(
            crew=crew,
            user=user,
            role='ADMIN',
            is_active=True
        )
        
        # Send email
        result = crew_email_service.send_role_changed(
            membership=membership,
            old_role='MEMBER',
            changed_by=changed_by
        )
        
        if result:
            self.stdout.write(self.style.SUCCESS('✅ Role change email sent'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ Role change email failed'))
        
        # Clean up
        membership.delete()

    def test_member_left_email(self, crew, departed_user, admin_user):
        """Test member left notification email."""
        self.stdout.write('Testing member left email...')
        
        # Send email
        result = crew_email_service.send_member_left(
            crew=crew,
            user=departed_user,
            admin_user=admin_user
        )
        
        if result:
            self.stdout.write(self.style.SUCCESS('✅ Member left email sent'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ Member left email failed'))
