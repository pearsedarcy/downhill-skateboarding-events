"""
Utility functions for crew achievements system.
"""
from django.utils import timezone
from django.db import transaction
from .models_achievements import AchievementTemplate, CrewAchievement
from .models import CrewActivity


def check_and_award_achievements(crew, triggered_by_user=None):
    """
    Check all achievement templates and award any that the crew now qualifies for.
    
    Args:
        crew (Crew): The crew to check achievements for
        triggered_by_user (User): Optional user who triggered the check
        
    Returns:
        list: List of newly awarded achievements
    """
    newly_awarded = []
    
    # Get all active achievement templates
    templates = AchievementTemplate.objects.filter(is_active=True)
    
    # Get already earned achievement titles to avoid duplicates
    earned_titles = set(
        crew.achievements.values_list('title', flat=True)
    )
    
    for template in templates:
        # Skip if already earned
        if template.title in earned_titles:
            continue
            
        # Check if crew meets criteria
        if template.check_crew_eligibility(crew):
            try:
                with transaction.atomic():
                    achievement, created = template.award_to_crew(crew)
                    
                    if created:
                        newly_awarded.append(achievement)
                        
                        # Log the achievement in crew activity
                        CrewActivity.objects.create(
                            crew=crew,
                            activity_type='MEMBER_PROMOTED',  # We'll reuse this for achievements
                            user=triggered_by_user or crew.owners.first(),
                            description=f"🏆 Earned achievement: {achievement.title}",
                            metadata={
                                'achievement_id': achievement.id,
                                'achievement_level': achievement.level,
                                'achievement_type': achievement.achievement_type,
                                'auto_awarded': triggered_by_user is None
                            }
                        )
                        
            except Exception as e:
                # Log error but don't break the flow
                print(f"Error awarding achievement {template.title} to {crew.name}: {e}")
                continue
    
    return newly_awarded


def award_manual_achievement(crew, achievement_title, awarded_by, custom_description=None):
    """
    Manually award an achievement to a crew.
    
    Args:
        crew (Crew): The crew to award to
        achievement_title (str): Title of the achievement template
        awarded_by (User): User awarding the achievement
        custom_description (str): Optional custom description
        
    Returns:
        CrewAchievement or None: The awarded achievement if successful
    """
    try:
        template = AchievementTemplate.objects.get(title=achievement_title, is_active=True)
    except AchievementTemplate.DoesNotExist:
        return None
    
    # Check if already awarded
    if crew.achievements.filter(title=template.title).exists():
        return None
    
    try:
        with transaction.atomic():
            achievement = CrewAchievement.objects.create(
                crew=crew,
                title=template.title,
                description=custom_description or template.description,
                achievement_type=template.achievement_type,
                level=template.level,
                icon=template.icon,
                color=template.color,
                awarded_by=awarded_by,
                criteria_met=template._get_current_criteria_values(crew)
            )
            
            # Log the manual achievement
            CrewActivity.objects.create(
                crew=crew,
                activity_type='MEMBER_PROMOTED',
                user=awarded_by,
                description=f"🏆 Manually awarded achievement: {achievement.title}",
                metadata={
                    'achievement_id': achievement.id,
                    'achievement_level': achievement.level,
                    'achievement_type': achievement.achievement_type,
                    'manually_awarded': True
                }
            )
            
            return achievement
            
    except Exception as e:
        print(f"Error manually awarding achievement {achievement_title} to {crew.name}: {e}")
        return None


def get_crew_achievement_progress(crew):
    """
    Get progress towards all available achievements.
    
    Args:
        crew (Crew): The crew to check progress for
        
    Returns:
        dict: Achievement progress data
    """
    templates = AchievementTemplate.objects.filter(is_active=True)
    earned_titles = set(crew.achievements.values_list('title', flat=True))
    
    progress = {
        'earned': [],
        'available': [],
        'locked': []
    }
    
    current_stats = {
        'member_count': crew.member_count,
        'event_count': crew.events.filter(is_published=True).count(),
        'crew_age_days': (timezone.now() - crew.created_at).days,
        'is_verified': crew.is_verified,
    }
    
    for template in templates:
        if template.title in earned_titles:
            progress['earned'].append({
                'template': template,
                'achievement': crew.achievements.get(title=template.title)
            })
        else:
            # Calculate progress percentage
            criteria = template.criteria
            progress_pct = 0
            progress_details = {}
            
            if criteria.get('min_members'):
                progress_details['members'] = {
                    'current': current_stats['member_count'],
                    'required': criteria['min_members'],
                    'percentage': min(100, (current_stats['member_count'] / criteria['min_members']) * 100)
                }
                progress_pct = max(progress_pct, progress_details['members']['percentage'])
            
            if criteria.get('min_events'):
                progress_details['events'] = {
                    'current': current_stats['event_count'],
                    'required': criteria['min_events'],
                    'percentage': min(100, (current_stats['event_count'] / criteria['min_events']) * 100)
                }
                progress_pct = max(progress_pct, progress_details['events']['percentage'])
            
            if criteria.get('min_age_days'):
                progress_details['age'] = {
                    'current': current_stats['crew_age_days'],
                    'required': criteria['min_age_days'],
                    'percentage': min(100, (current_stats['crew_age_days'] / criteria['min_age_days']) * 100)
                }
                progress_pct = max(progress_pct, progress_details['age']['percentage'])
            
            if criteria.get('requires_verification', False):
                progress_details['verification'] = {
                    'current': current_stats['is_verified'],
                    'required': True,
                    'percentage': 100 if current_stats['is_verified'] else 0
                }
                progress_pct = min(progress_pct, progress_details['verification']['percentage'])
            
            achievement_data = {
                'template': template,
                'progress_percentage': progress_pct,
                'progress_details': progress_details,
                'eligible': template.check_crew_eligibility(crew)
            }
            
            if achievement_data['eligible']:
                progress['available'].append(achievement_data)
            else:
                progress['locked'].append(achievement_data)
    
    return progress
