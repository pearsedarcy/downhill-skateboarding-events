#!/usr/bin/env python
"""
Simple test script to verify crew permissions functionality
without using Django's test framework.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'downhill_skateboarding_events.settings')
django.setup()

from django.contrib.auth.models import User
from crews.models import Crew, CrewMembership


def test_permission_system():
    """Test the crew permission system manually."""
    print("Testing Crew Permissions System...")
    print("=" * 50)
    
    try:
        # Create test users
        print("1. Creating test users...")
        owner, created = User.objects.get_or_create(
            username='test_owner',
            defaults={'email': 'owner@test.com'}
        )
        if created:
            owner.set_password('password')
            owner.save()
        
        member, created = User.objects.get_or_create(
            username='test_member',
            defaults={'email': 'member@test.com'}
        )
        if created:
            member.set_password('password')
            member.save()
        
        print(f"   ✓ Created owner: {owner.username}")
        print(f"   ✓ Created member: {member.username}")
        
        # Create test crew
        print("\n2. Creating test crew...")
        crew, created = Crew.objects.get_or_create(
            name='Test Permission Crew',
            defaults={'description': 'A crew for testing permissions'}
        )
        print(f"   ✓ Created crew: {crew.name}")
        
        # Create memberships
        print("\n3. Creating memberships...")
        owner_membership, created = CrewMembership.objects.get_or_create(
            crew=crew,
            user=owner,
            defaults={'role': 'OWNER'}
        )
        print(f"   ✓ Owner membership: {owner_membership}")
        
        member_membership, created = CrewMembership.objects.get_or_create(
            crew=crew,
            user=member,
            defaults={'role': 'MEMBER'}
        )
        print(f"   ✓ Member membership: {member_membership}")
        
        # Test role-based permissions
        print("\n4. Testing role-based permissions...")
        print(f"   Owner has create permission: {owner_membership.has_event_permission('create')}")
        print(f"   Owner has edit permission: {owner_membership.has_event_permission('edit')}")
        print(f"   Owner has publish permission: {owner_membership.has_event_permission('publish')}")
        print(f"   Owner has delegate permission: {owner_membership.has_event_permission('delegate')}")
        
        print(f"   Member has create permission: {member_membership.has_event_permission('create')}")
        print(f"   Member has edit permission: {member_membership.has_event_permission('edit')}")
        print(f"   Member has publish permission: {member_membership.has_event_permission('publish')}")
        print(f"   Member has delegate permission: {member_membership.has_event_permission('delegate')}")
        
        # Test specific permission granting
        print("\n5. Testing permission granting...")
        print("   Granting 'create' permission to member...")
        member_membership.grant_permission('create', owner)
        print(f"   Member now has create permission: {member_membership.has_event_permission('create')}")
        print(f"   Member still no edit permission: {member_membership.has_event_permission('edit')}")
        
        # Test crew-level permission checking
        print("\n6. Testing crew-level permission methods...")
        print(f"   Crew.can_create_events(owner): {crew.can_create_events(owner)}")
        print(f"   Crew.can_create_events(member): {crew.can_create_events(member)}")
        print(f"   Crew.can_edit_events(member): {crew.can_edit_events(member)}")
        
        # Test permission summary
        print("\n7. Testing permission summary...")
        owner_summary = owner_membership.get_permission_summary()
        member_summary = member_membership.get_permission_summary()
        
        print(f"   Owner summary: {owner_summary}")
        print(f"   Member summary: {member_summary}")
        
        # Test delegation
        print("\n8. Testing delegation capabilities...")
        print(f"   Owner can delegate to member: {owner_membership.can_delegate_to_member(member_membership)}")
        print(f"   Member can delegate to owner: {member_membership.can_delegate_to_member(owner_membership)}")
        
        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_permission_system()
    sys.exit(0 if success else 1)
