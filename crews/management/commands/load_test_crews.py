"""
Management command to load test crew data for development and testing.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
from crews.models import Crew, CrewMembership, CrewActivity


class Command(BaseCommand):
    help = 'Load test crew data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing crew data before loading test data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing crew data...')
            
            # Clear crew-related data (this will cascade to memberships and activities)
            Crew.objects.all().delete()
            
            # Clear test users (IDs 100-107)
            User.objects.filter(pk__in=range(100, 108)).delete()
            
            self.stdout.write(
                self.style.SUCCESS('Cleared existing crew data.')
            )

        self.stdout.write('Loading test crew data...')
        
        try:
            # Load the test data fixture
            call_command('loaddata', 'crews/fixtures/test_crews.json')
            
            # Report what was created
            crew_count = Crew.objects.count()
            membership_count = CrewMembership.objects.count()
            activity_count = CrewActivity.objects.count()
            test_user_count = User.objects.filter(pk__in=range(100, 108)).count()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully loaded test data:\n'
                    f'  - {test_user_count} test users\n'
                    f'  - {crew_count} crews\n'
                    f'  - {membership_count} memberships\n'
                    f'  - {activity_count} activity records'
                )
            )
            
            # Show crew summaries
            self.stdout.write('\nCreated crews:')
            for crew in Crew.objects.all():
                member_count = crew.memberships.count()
                owner = crew.memberships.filter(role='OWNER').first()
                self.stdout.write(
                    f'  • {crew.name} ({crew.slug}) - {member_count} members, '
                    f'owner: {owner.user.get_full_name() if owner else "None"}'
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading test data: {e}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                '\nTest data loaded successfully! You can now test crew management features.'
            )
        )
