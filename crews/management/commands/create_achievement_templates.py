"""
Management command to create default achievement templates.
"""
from django.core.management.base import BaseCommand
from crews.models_achievements import AchievementTemplate


class Command(BaseCommand):
    help = 'Create default achievement templates for crews'

    def handle(self, *args, **options):
        achievements = [
            # Member Milestones
            {
                'title': 'First Steps',
                'description': 'Congratulations on creating your crew! Your skateboarding journey begins.',
                'achievement_type': 'MEMBER_MILESTONE',
                'level': 'BRONZE',
                'criteria': {'min_members': 1},
                'icon': 'fas fa-baby',
                'color': 'success'
            },
            {
                'title': 'Growing Strong',
                'description': 'Your crew has reached 5 members! The community is growing.',
                'achievement_type': 'MEMBER_MILESTONE', 
                'level': 'SILVER',
                'criteria': {'min_members': 5},
                'icon': 'fas fa-users',
                'color': 'info'
            },
            {
                'title': 'Crew Family',
                'description': 'Amazing! Your crew has 10 dedicated members.',
                'achievement_type': 'MEMBER_MILESTONE',
                'level': 'GOLD',
                'criteria': {'min_members': 10},
                'icon': 'fas fa-heart',
                'color': 'warning'
            },
            {
                'title': 'Skateboarding Squad',
                'description': 'Incredible! 25 members strong and rolling together.',
                'achievement_type': 'MEMBER_MILESTONE',
                'level': 'PLATINUM',
                'criteria': {'min_members': 25},
                'icon': 'fas fa-crown',
                'color': 'primary'
            },
            
            # Event Milestones
            {
                'title': 'Event Starter',
                'description': 'Your crew organized its first event! Leading the way.',
                'achievement_type': 'EVENT_MILESTONE',
                'level': 'BRONZE',
                'criteria': {'min_events': 1},
                'icon': 'fas fa-calendar-plus',
                'color': 'success'
            },
            {
                'title': 'Event Organizer',
                'description': 'Your crew has organized 5 events. Keep the momentum going!',
                'achievement_type': 'EVENT_MILESTONE',
                'level': 'SILVER', 
                'criteria': {'min_events': 5},
                'icon': 'fas fa-calendar-check',
                'color': 'info'
            },
            {
                'title': 'Event Master',
                'description': 'Wow! 10 events organized. Your crew is a community pillar.',
                'achievement_type': 'EVENT_MILESTONE',
                'level': 'GOLD',
                'criteria': {'min_events': 10},
                'icon': 'fas fa-trophy',
                'color': 'warning'
            },
            {
                'title': 'Event Legend',
                'description': 'Legendary status! 25 events and counting.',
                'achievement_type': 'EVENT_MILESTONE',
                'level': 'LEGENDARY',
                'criteria': {'min_events': 25},
                'icon': 'fas fa-star',
                'color': 'secondary'
            },
            
            # Anniversary Achievements
            {
                'title': 'One Year Strong',
                'description': 'Your crew has been rolling for a full year! Happy anniversary!',
                'achievement_type': 'ANNIVERSARY',
                'level': 'GOLD',
                'criteria': {'min_age_days': 365},
                'icon': 'fas fa-birthday-cake',
                'color': 'warning'
            },
            {
                'title': 'Two Years Rolling',
                'description': 'Two years of skateboarding excellence! Time flies when you\'re having fun.',
                'achievement_type': 'ANNIVERSARY',
                'level': 'PLATINUM',
                'criteria': {'min_age_days': 730},
                'icon': 'fas fa-calendar-alt',
                'color': 'primary'
            },
            
            # Special Recognition
            {
                'title': 'Verified Crew',
                'description': 'Your crew has been verified! Official recognition of your contribution.',
                'achievement_type': 'SPECIAL',
                'level': 'PLATINUM',
                'criteria': {'requires_verification': True},
                'icon': 'fas fa-check-circle',
                'color': 'primary'
            },
            {
                'title': 'Community Builder',
                'description': 'A verified crew with 10+ members and 5+ events. True community leaders!',
                'achievement_type': 'COMMUNITY',
                'level': 'LEGENDARY',
                'criteria': {
                    'requires_verification': True,
                    'min_members': 10,
                    'min_events': 5
                },
                'icon': 'fas fa-hands-helping',
                'color': 'secondary'
            }
        ]
        
        created_count = 0
        
        for achievement_data in achievements:
            template, created = AchievementTemplate.objects.get_or_create(
                title=achievement_data['title'],
                defaults=achievement_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created achievement template: {template.title}')
                )
            else:
                self.stdout.write(f'Achievement template already exists: {template.title}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new achievement templates')
        )
