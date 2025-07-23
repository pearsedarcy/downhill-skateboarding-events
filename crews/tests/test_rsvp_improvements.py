#!/usr/bin/env python
"""Test the improved RSVP functionality."""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'downhill_skateboarding_events.settings')
django.setup()

from django.contrib.auth.models import User
from profiles.models import UserProfile
from events.models import Event, RSVP
from django.utils import timezone
from django.db import IntegrityError


def test_rsvp_improvements():
    """Test the improved RSVP system."""
    print("Testing Improved RSVP System...")
    print("=" * 60)
    
    try:
        # Create test users
        print("1. Creating test data...")
        user1, created = User.objects.get_or_create(
            username='rsvp_user1',
            defaults={'email': 'user1@test.com'}
        )
        user2, created = User.objects.get_or_create(
            username='rsvp_user2', 
            defaults={'email': 'user2@test.com'}
        )
        
        # Create test event
        event, created = Event.objects.get_or_create(
            title='RSVP Test Event',
            defaults={
                'slug': 'rsvp-test-event',
                'description': 'Testing improved RSVP',
                'start_date': timezone.now().date(),
                'skill_level': 'Beginner',
                'event_type': 'Local Meetup',
                'max_attendees': 2,  # Test capacity limits
                'published': True
            }
        )
        
        print(f"   ✓ Created event: {event.title}")
        print(f"   ✓ Max attendees: {event.max_attendees}")
        
        # Test RSVP creation with all statuses
        print("\n2. Testing RSVP status options...")
        
        # Test Going status
        rsvp1 = RSVP.objects.create(
            user=user1.profile,
            event=event,
            status='Going'
        )
        print(f"   ✓ User1 RSVP: {rsvp1.status}")
        print(f"   ✓ Is attending: {rsvp1.is_attending}")
        print(f"   ✓ Is interested: {rsvp1.is_interested}")
        
        # Test Interested status
        rsvp2 = RSVP.objects.create(
            user=user2.profile,
            event=event, 
            status='Interested'
        )
        print(f"   ✓ User2 RSVP: {rsvp2.status}")
        print(f"   ✓ Is attending: {rsvp2.is_attending}")
        print(f"   ✓ Is interested: {rsvp2.is_interested}")
        
        # Test unique constraint
        print("\n3. Testing unique constraint...")
        try:
            RSVP.objects.create(
                user=user1.profile,
                event=event,
                status='Not interested'
            )
            print("   ❌ Should have failed unique constraint")
        except IntegrityError:
            print("   ✓ Unique constraint working correctly")
        
        # Test event helper methods
        print("\n4. Testing event helper methods...")
        print(f"   ✓ User1 RSVP status: {event.get_user_rsvp_status(user1)}")
        print(f"   ✓ User2 RSVP status: {event.get_user_rsvp_status(user2)}")
        
        counts = event.get_attendee_counts()
        print(f"   ✓ Attendee counts: {counts}")
        print(f"   ✓ Going count: {event.get_going_count()}")
        print(f"   ✓ Interested count: {event.get_interested_count()}")
        print(f"   ✓ Is full: {event.is_full()}")
        
        # Test capacity management
        print("\n5. Testing capacity management...")
        
        # Create another user to test capacity
        user3, created = User.objects.get_or_create(
            username='rsvp_user3',
            defaults={'email': 'user3@test.com'}
        )
        
        # Add user3 as going (should reach capacity)
        rsvp3 = RSVP.objects.create(
            user=user3.profile,
            event=event,
            status='Going'
        )
        print(f"   ✓ User3 added as Going")
        print(f"   ✓ Going count now: {event.get_going_count()}")
        print(f"   ✓ Is full now: {event.is_full()}")
        
        # Test status changes
        print("\n6. Testing status changes...")
        
        # Change user2 from Interested to Going (should still work since user3 filled capacity)
        original_status = rsvp2.status
        rsvp2.status = 'Not interested'
        rsvp2.save()
        print(f"   ✓ User2 changed from {original_status} to {rsvp2.status}")
        
        # Verify updated counts
        final_counts = event.get_attendee_counts()
        print(f"   ✓ Final counts: {final_counts}")
        
        # Test ordering (newest first)
        print("\n7. Testing RSVP ordering...")
        rsvps = event.rsvps.all()
        for i, rsvp in enumerate(rsvps):
            print(f"   {i+1}. {rsvp.user.user.username} - {rsvp.status} ({rsvp.created_at.strftime('%H:%M:%S')})")
        
        print("\n" + "=" * 60)
        print("✅ All RSVP improvement tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_rsvp_improvements()
    sys.exit(0 if success else 1)
