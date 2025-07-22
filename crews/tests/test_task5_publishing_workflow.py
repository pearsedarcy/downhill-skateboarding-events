"""
Test Task 5: Publishing Workflow Implementation

Tests the integration of crew permission system with event publishing workflow.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from crews.models import Crew, CrewMembership
from events.models import Event, Location


class PublishingWorkflowTestCase(TestCase):
    def setUp(self):
        """Set up test data for publishing workflow tests."""
        # Create users
        self.owner = User.objects.create_user(username='owner', password='test123')
        self.admin = User.objects.create_user(username='admin', password='test123')
        self.member_with_create = User.objects.create_user(username='member_create', password='test123')
        self.member_with_edit = User.objects.create_user(username='member_edit', password='test123')
        self.member_with_publish = User.objects.create_user(username='member_publish', password='test123')
        self.regular_member = User.objects.create_user(username='regular', password='test123')
        self.non_member = User.objects.create_user(username='outsider', password='test123')
        
        # Create crew
        self.crew = Crew.objects.create(
            name='Test Crew',
            slug='test-crew',
            description='Test crew for publishing workflow'
        )
        
        # Create memberships with specific permissions
        self.owner_membership = CrewMembership.objects.create(
            crew=self.crew, user=self.owner, role='OWNER'
        )
        
        self.admin_membership = CrewMembership.objects.create(
            crew=self.crew, user=self.admin, role='ADMIN'
        )
        
        self.member_create_membership = CrewMembership.objects.create(
            crew=self.crew, user=self.member_with_create, role='MEMBER',
            can_create_events=True
        )
        
        self.member_edit_membership = CrewMembership.objects.create(
            crew=self.crew, user=self.member_with_edit, role='MEMBER',
            can_edit_events=True
        )
        
        self.member_publish_membership = CrewMembership.objects.create(
            crew=self.crew, user=self.member_with_publish, role='MEMBER',
            can_publish_events=True
        )
        
        self.regular_membership = CrewMembership.objects.create(
            crew=self.crew, user=self.regular_member, role='MEMBER'
        )
        
        # Create test location
        self.location = Location.objects.create(
            location_title='Test Location',
            city='Test City',
            country='US',
            start_latitude=40.7128,
            start_longitude=-74.0060
        )
        
        # Create test event
        self.event = Event.objects.create(
            title='Test Event',
            description='Test event for publishing workflow',
            start_date='2025-12-25',
            event_type='Race',
            skill_level='INTERMEDIATE',
            organizer=self.owner.profile,
            location=self.location,
            created_by_crew=self.crew,
            published=False
        )
        
        self.client = Client()

    def test_event_form_crew_choices(self):
        """Test that event form only shows crews where user can create events."""
        # Test user with create permission
        self.client.login(username='member_create', password='test123')
        response = self.client.get(reverse('events:submit'))
        self.assertEqual(response.status_code, 200)
        # Form should include the crew since user has create permission
        form = response.context['form']
        crew_choices = list(form.fields['created_by_crew'].queryset)
        self.assertIn(self.crew, crew_choices)
        
        # Test user without create permission
        self.client.login(username='regular', password='test123')
        response = self.client.get(reverse('events:submit'))
        form = response.context['form']
        crew_choices = list(form.fields['created_by_crew'].queryset)
        self.assertNotIn(self.crew, crew_choices)

    def test_event_creation_permission_check(self):
        """Test that event creation respects crew permissions."""
        # Test successful creation with permission
        self.client.login(username='member_create', password='test123')
        event_data = {
            'title': 'New Event',
            'description': 'New event description',
            'start_date': '2025-12-31',
            'event_type': 'Freeride',
            'skill_level': 'BEGINNER',
            'created_by_crew': self.crew.id,
            'published': True,
            # Location data
            'location_title': 'New Location',
            'city': 'New City',
            'country': 'US',
            'start_latitude': 40.0,
            'start_longitude': -74.0
        }
        response = self.client.post(reverse('events:submit'), event_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        
        # Verify event was created
        new_event = Event.objects.filter(title='New Event').first()
        self.assertIsNotNone(new_event)
        self.assertEqual(new_event.created_by_crew, self.crew)

    def test_event_editing_permission_check(self):
        """Test that event editing respects crew permissions."""
        # Test editing with appropriate permission
        self.client.login(username='member_edit', password='test123')
        response = self.client.get(reverse('events:edit_event', args=[self.event.slug]))
        self.assertEqual(response.status_code, 200)
        
        # Test editing without permission
        self.client.login(username='regular', password='test123')
        response = self.client.get(reverse('events:edit_event', args=[self.event.slug]))
        self.assertEqual(response.status_code, 302)  # Redirect due to lack of permission

    def test_event_publishing_permission_check(self):
        """Test that event publishing respects crew permissions."""
        # Test publishing with appropriate permission
        self.client.login(username='member_publish', password='test123')
        response = self.client.post(reverse('events:toggle_publish', args=[self.event.slug]))
        self.assertEqual(response.status_code, 302)  # Redirect after successful toggle
        
        # Verify event was published
        self.event.refresh_from_db()
        self.assertTrue(self.event.published)
        
        # Test publishing without permission
        self.client.login(username='regular', password='test123')
        self.event.published = False
        self.event.save()
        
        response = self.client.post(reverse('events:toggle_publish', args=[self.event.slug]))
        self.assertEqual(response.status_code, 302)  # Redirect due to lack of permission
        
        # Verify event was not published
        self.event.refresh_from_db()
        self.assertFalse(self.event.published)

    def test_event_can_manage_method(self):
        """Test the Event.can_manage() method with crew permissions."""
        # Owner should be able to manage
        self.assertTrue(self.event.can_manage(self.owner))
        
        # Admin should be able to manage (owners have all permissions)
        self.assertTrue(self.event.can_manage(self.admin))
        
        # Member with edit permission should be able to manage
        self.assertTrue(self.event.can_manage(self.member_with_edit))
        
        # Regular member should not be able to manage
        self.assertFalse(self.event.can_manage(self.regular_member))
        
        # Non-member should not be able to manage
        self.assertFalse(self.event.can_manage(self.non_member))

    def test_event_can_publish_method(self):
        """Test the Event.can_publish() method with crew permissions."""
        # Owner should be able to publish
        self.assertTrue(self.event.can_publish(self.owner))
        
        # Admin should be able to publish (owners have all permissions)
        self.assertTrue(self.event.can_publish(self.admin))
        
        # Member with publish permission should be able to publish
        self.assertTrue(self.event.can_publish(self.member_with_publish))
        
        # Member without publish permission should not be able to publish
        self.assertFalse(self.event.can_publish(self.member_with_edit))
        self.assertFalse(self.event.can_publish(self.regular_member))
        
        # Non-member should not be able to publish
        self.assertFalse(self.event.can_publish(self.non_member))

    def test_crew_detail_page_permissions(self):
        """Test that crew detail page shows appropriate event management options."""
        # Test with user who has create permission
        self.client.login(username='member_create', password='test123')
        response = self.client.get(reverse('crews:detail', args=[self.crew.slug]))
        self.assertEqual(response.status_code, 200)
        
        # Check that create button is visible
        self.assertContains(response, 'Create Event')
        
        # Test with user who doesn't have create permission
        self.client.login(username='regular', password='test123')
        response = self.client.get(reverse('crews:detail', args=[self.crew.slug]))
        self.assertEqual(response.status_code, 200)
        
        # Create button should not be visible
        self.assertNotContains(response, 'Create Event')

    def test_event_permission_context_in_crew_detail(self):
        """Test that events in crew detail have proper permission context."""
        self.client.login(username='member_edit', password='test123')
        response = self.client.get(reverse('crews:detail', args=[self.crew.slug]))
        
        # Check that events have permission flags set
        upcoming_events = response.context['upcoming_events']
        if upcoming_events:
            event = upcoming_events[0]
            self.assertTrue(hasattr(event, 'user_can_manage'))
            self.assertTrue(hasattr(event, 'user_can_publish'))


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    if not settings.configured:
        settings.configure(
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'crews',
                'events',
                'profiles',
            ],
            SECRET_KEY='test-secret-key'
        )
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['__main__'])
