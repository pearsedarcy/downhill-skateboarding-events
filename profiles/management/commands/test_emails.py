"""
Django management command to test email functionality.

This command allows testing different types of emails to ensure they
work correctly and look good across different email clients.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from profiles.email_service import email_service
from datetime import timedelta


class Command(BaseCommand):
    help = 'Test email functionality by sending sample emails'

    def add_arguments(self, parser):
        parser.add_argument(
            'email_type',
            choices=['welcome', 'event', 'community', 'newsletter', 'marketing', 'stats'],
            help='Type of email to test'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test email to (defaults to first superuser)'
        )

    def handle(self, *args, **options):
        email_type = options['email_type']
        target_email = options.get('email')
        
        # Get target user
        if target_email:
            try:
                user = User.objects.get(email=target_email)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with email {target_email} not found')
                )
                return
        else:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                self.stdout.write(
                    self.style.ERROR('No superuser found. Please create one or specify --email')
                )
                return

        self.stdout.write(f'Sending {email_type} email to {user.email}...')

        try:
            if email_type == 'welcome':
                self.test_welcome_email(user)
            elif email_type == 'event':
                self.test_event_notification(user)
            elif email_type == 'community':
                self.test_community_news(user)
            elif email_type == 'newsletter':
                self.test_newsletter(user)
            elif email_type == 'marketing':
                self.test_marketing_email(user)
            elif email_type == 'stats':
                self.show_email_stats()
                return

            self.stdout.write(
                self.style.SUCCESS(f'Successfully sent {email_type} email!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send email: {e}')
            )

    def test_welcome_email(self, user):
        """Test welcome email"""
        email_service.send_welcome_email(user)

    def test_event_notification(self, user):
        """Test event notification with mock event data"""
        # Create mock event data
        mock_event = type('MockEvent', (), {
            'title': 'Epic Downhill Challenge 2025',
            'start_date': timezone.now() + timedelta(days=14),
            'end_date': timezone.now() + timedelta(days=14),
            'location': 'Mount Tamalpais State Park',
            'city': 'Mill Valley',
            'country': 'USA',
            'event_type': 'RACE',
            'description': 'Join us for an epic downhill race through the beautiful trails of Mount Tamalpais. This challenging course features technical sections, high-speed straights, and breathtaking views of the San Francisco Bay.',
            'max_participants': 50,
            'current_participants': 23,
            'skill_level_required': 'INTERMEDIATE',
            'slug': 'epic-downhill-challenge-2025',
            'organizer': user,
            'is_registration_open': True,
            'get_event_type_display': lambda: 'Race',
            'get_skill_level_required_display': lambda: 'Intermediate'
        })()
        
        email_service.send_event_notification(mock_event, [user])

    def test_community_news(self, user):
        """Test community news email"""
        # Mock data
        featured_rider = User.objects.filter(profile__isnull=False).first() or user
        
        mock_recent_events = [
            type('MockEvent', (), {
                'title': 'Bay Area Freeride Session',
                'start_date': timezone.now() - timedelta(days=7),
                'city': 'San Francisco',
                'participants': type('MockParticipants', (), {'count': lambda: 15})(),
                'highlight': 'Amazing session with perfect weather and gnarly slides!'
            })(),
            type('MockEvent', (), {
                'title': 'SoCal Speed Demons Race',
                'start_date': timezone.now() - timedelta(days=3),
                'city': 'Los Angeles',
                'participants': type('MockParticipants', (), {'count': lambda: 32})(),
                'highlight': 'New course record set by local rider!'
            })()
        ]
        
        mock_upcoming_events = [
            type('MockEvent', (), {
                'title': 'Golden Gate Park Cruise',
                'start_date': timezone.now() + timedelta(days=10),
                'city': 'San Francisco',
                'slug': 'golden-gate-park-cruise'
            })()
        ]
        
        email_service.send_community_news(
            featured_rider=featured_rider,
            recent_events=mock_recent_events,
            safety_tip="Always check your bearings before hitting the hills - clean bearings mean smoother, safer rides!",
            upcoming_events=mock_upcoming_events,
            community_stats={
                'new_members': 47,
                'events_this_month': 12,
                'total_distance': 2340
            }
        )

    def test_newsletter(self, user):
        """Test monthly newsletter"""
        current_date = timezone.now()
        
        mock_featured_content = {
            'event': type('MockEvent', (), {
                'title': 'International Downhill Championship',
                'description': 'The biggest downhill event of the year featuring riders from over 20 countries competing on the most challenging course ever designed.',
                'slug': 'international-downhill-championship'
            })(),
            'rider': user,
            'rider_story': 'From beginner to pro in just two years - this month we spotlight an inspiring journey of dedication and progression.'
        }
        
        mock_gear_review = {
            'title': 'Sector 9 Meridian Complete Review',
            'excerpt': 'We put this premium complete through its paces on hills across California.',
            'rating': 4.5,
            'url': '#gear-review'
        }
        
        mock_tips = [
            {
                'title': 'Perfect Your Pre-Drift Setup',
                'content': 'Learn the key body positioning and timing for smooth drift entries.',
                'video_url': '#tutorial-1'
            },
            {
                'title': 'Reading the Road Surface',
                'content': 'How to identify grip levels and adjust your riding style accordingly.',
                'video_url': None
            }
        ]
        
        mock_upcoming_events = [
            type('MockEvent', (), {
                'title': 'Golden Gate Park Cruise',
                'start_date': timezone.now() + timedelta(days=10),
                'city': 'San Francisco',
                'slug': 'golden-gate-park-cruise'
            })()
        ]
        
        email_service.send_monthly_newsletter(
            month_name=current_date.strftime('%B'),
            year=current_date.year,
            monthly_stats={
                'events_count': 18,
                'new_members': 234,
                'crews_formed': 8
            },
            featured_content=mock_featured_content,
            gear_review=mock_gear_review,
            tips_section=mock_tips,
            upcoming_events=mock_upcoming_events,
            safety_focus={
                'title': 'Helmet Technology Updates',
                'content': 'New MIPS technology in skateboarding helmets and why it matters for downhill riders.',
                'link': '#safety-guide'
            },
            community_shoutouts=[
                {'user': user, 'achievement': 'completed their first major race'},
                {'user': user, 'achievement': 'organized 5 community events this month'}
            ]
        )

    def test_marketing_email(self, user):
        """Test marketing email"""
        mock_offer = {
            'title': 'Spring Gear Sale - Up to 40% Off',
            'description': 'Get ready for the season with premium downhill gear at unbeatable prices.',
            'discount_percentage': 40,
            'original_price': 299.99,
            'sale_price': 179.99,
            'code': 'SPRING2025',
            'expires_at': timezone.now() + timedelta(days=7),
            'url': '#shop-sale',
            'details': [
                'Valid on all boards, trucks, and wheels',
                'Free shipping on orders over $100',
                'Limited time offer - while supplies last',
                'Cannot be combined with other offers'
            ]
        }
        
        mock_partner_info = {
            'name': 'Sector 9',
            'description': 'Premium skateboard manufacturer specializing in longboards and downhill equipment.',
            'website': 'https://sector9.com'
        }
        
        email_service.send_marketing_email(
            offer=mock_offer,
            partner_info=mock_partner_info,
            why_sharing="We've partnered with Sector 9 to bring our community exclusive discounts on high-quality gear."
        )

    def show_email_stats(self):
        """Show email preference statistics"""
        stats = email_service.get_email_stats()
        
        self.stdout.write(self.style.SUCCESS('Email Preference Statistics:'))
        self.stdout.write(f"Total Active Users: {stats.get('total_active_users', 0)}")
        self.stdout.write('')
        
        preferences = [
            ('Event Notifications', 'event_notifications'),
            ('Community News', 'community_news'),
            ('Newsletter', 'newsletter'),
            ('Crew Invites', 'crew_invites'),
            ('Marketing', 'marketing')
        ]
        
        for name, key in preferences:
            count = stats.get(key, 0)
            percentage = stats.get(f'{key}_percentage', 0)
            self.stdout.write(f"{name}: {count} users ({percentage}%)")
