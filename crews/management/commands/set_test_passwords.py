"""
Management command to set passwords for test users.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Set passwords for test users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default='testpass123',
            help='Password to set for all test users (default: testpass123)',
        )

    def handle(self, *args, **options):
        password = options['password']
        
        # Get all test users (IDs 100-107)
        test_users = User.objects.filter(pk__in=range(100, 108))
        
        if not test_users.exists():
            self.stdout.write(
                self.style.ERROR('No test users found. Run "python manage.py load_test_crews" first.')
            )
            return

        self.stdout.write(f'Setting password "{password}" for test users...')
        
        updated_count = 0
        for user in test_users:
            user.set_password(password)
            user.save()
            updated_count += 1
            self.stdout.write(f'  ✓ {user.username} ({user.get_full_name()})')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully set passwords for {updated_count} test users.\n'
                f'You can now log in with any of these accounts using password: {password}'
            )
        )
        
        self.stdout.write('\nTest user accounts:')
        for user in test_users:
            self.stdout.write(f'  • Username: {user.username} | Name: {user.get_full_name()}')
