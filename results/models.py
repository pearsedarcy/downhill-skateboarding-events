from django.db import models
from events.models import Event
from profiles.models import UserProfile
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from cloudinary.models import CloudinaryField
from django_countries.fields import CountryField
import uuid
from django.core.files.base import ContentFile

class League(models.Model):
    CONTINENT_CHOICES = [
        ('AF', 'Africa'),
        ('AS', 'Asia'),
        ('EU', 'Europe'),
        ('NA', 'North America'),
        ('SA', 'South America'),
        ('OC', 'Oceania'),
        ('AN', 'Antarctica'),
    ]
    
    POINTS_SYSTEM_CHOICES = [
        ('STANDARD', 'Standard (1000-961-943...)'),
        ('CUSTOM', 'Custom')
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, null=True)
    description = models.TextField(blank=True)
    banner = CloudinaryField("banner", null=True, blank=True, help_text="Banner image for the league")
    logo = CloudinaryField("logo", null=True, blank=True, help_text="Logo image for the league")
    league_class = models.CharField(max_length=20, choices=Event.CLASS_CHOICES, default='LOCAL', verbose_name="League Class")
    country = CountryField(blank_label="(select country)", null=True, blank=True)
    continent = models.CharField(max_length=2, choices=CONTINENT_CHOICES, null=True, blank=True)
    points_system = models.CharField(max_length=20, choices=POINTS_SYSTEM_CHOICES, default='STANDARD')
    season = models.PositiveIntegerField(default=2025)
    
    # Crew ownership
    created_by_crew = models.ForeignKey(
        'crews.Crew', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_leagues',
        help_text="Crew that created and manages this league"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # New: Many-to-many relation with events through LeagueEvent
    events_relation = models.ManyToManyField(Event, through='LeagueEvent', related_name='leagues')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} {self.season}"
    
    def can_manage(self, user):
        """Check if a user can manage this league."""
        if not user.is_authenticated:
            return False
        
        # If no crew is assigned, allow original organizer/admin logic
        if not self.created_by_crew:
            return user.is_superuser
            
        # Check crew permissions
        return self.created_by_crew.can_manage(user)

    @property
    def events(self):
        return Event.objects.filter(league_links__league=self)
        
class LeagueEvent(models.Model):
    """Links an Event to a League with specific settings"""
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='league_events')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='league_links')
    multiplier = models.FloatField(default=1.0, help_text="Point multiplier for this event")
    weight = models.PositiveIntegerField(default=100, help_text="Percentage weight of this event in league calculations")
    
    class Meta:
        unique_together = ['league', 'event']
    
    def __str__(self):
        return f"{self.event.title} in {self.league.name}"

class Result(models.Model):
    RESULT_TYPES = [
        ('TIME_TRIAL', 'Time Trial'),
        ('KNOCKOUT', 'Knockout'),
        ('BRACKET', 'Bracket')
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='results')
    result_type = models.CharField(max_length=20, choices=RESULT_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    raw_data = models.FileField(upload_to='results/')
    is_final = models.BooleanField(default=False)  # Added to mark official results

    class Meta:
        unique_together = ['event', 'result_type', 'is_final']  # Only one final result per type

    def __str__(self):
        return f"{self.event.title} - {self.result_type}"

class TimeTrialResult(models.Model):
    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='time_trials')
    competitor = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    time = models.DurationField()
    points = models.IntegerField(default=0)

    class Meta:
        ordering = ['position']

class KnockoutResult(models.Model):
    ROUND_CHOICES = [
        ('FINAL', 'Final'),
        ('SEMI', 'Semi-Final'),
        ('QUARTER', 'Quarter-Final'),
        ('ROUND16', 'Round of 16'),
        ('ROUND32', 'Round of 32'),
    ]

    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='knockouts')
    round = models.CharField(max_length=10, choices=ROUND_CHOICES)
    winner = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='knockout_wins')
    loser = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='knockout_losses')
    match_number = models.PositiveIntegerField()

    class Meta:
        ordering = ['match_number']

class Discipline(models.Model):
    """Represents a discipline within a league (e.g., Open Skate, Women's Skate, Luge, etc.)"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='disciplines')
    description = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} - {self.league.name}"
    
    class Meta:
        unique_together = ['league', 'slug']

class CSVColumnMapping(models.Model):
    """Define how CSV columns map to result data fields"""
    FIELD_TYPE_CHOICES = [
        ('RANK', 'Rank/Position'),
        ('NAME', 'Competitor Name'),
        ('POINTS', 'Points'),
        ('DISCIPLINE', 'Discipline'),
        ('EVENT', 'Event'),
        ('TIME', 'Time'),
        ('COUNTRY', 'Country'),
        ('IGNORE', 'Ignore This Column')
    ]
    
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='csv_mappings', null=True, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='csv_mappings', null=True, blank=True)
    name = models.CharField(max_length=100, help_text="CSV column header name")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES)
    default_value = models.CharField(max_length=100, blank=True, help_text="Default value if column is empty")
    
    class Meta:
        unique_together = [
            ['league', 'name'],
            ['event', 'name']
        ]
        
    def __str__(self):
        owner = self.league or self.event
        return f"{self.name} → {self.get_field_type_display()} ({owner})"

class BracketResult(models.Model):
    """Individual competitor result for a bracket-style competition"""
    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='bracket_results')
    competitor_name = models.CharField(max_length=200)  # Store name directly for flexibility
    position = models.PositiveIntegerField()
    discipline = models.CharField(max_length=100, help_text="The discipline category (e.g., Open Skate)")
    points = models.IntegerField(default=0)
    event_name = models.CharField(max_length=200, blank=True, help_text="Optional event name if different from actual event")
    
    # Optional link to user profile if competitor exists in the system
    competitor_profile = models.ForeignKey(
        UserProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='bracket_results'
    )
    
    class Meta:
        ordering = ['position']
        
    def __str__(self):
        return f"{self.competitor_name} - {self.discipline} - Pos: {self.position}"

class PointsSystem(models.Model):
    """Standard points allocation system for event rankings"""
    position = models.PositiveIntegerField(unique=True)
    points = models.PositiveIntegerField()
    
    class Meta:
        ordering = ['position']
        
    def __str__(self):
        return f"Position {self.position}: {self.points} points"

    @classmethod
    def get_points_for_position(cls, position):
        """Get points for a given position using the standard points system"""
        try:
            return cls.objects.get(position=position).points
        except cls.DoesNotExist:
            # Calculate points using the standard formula if not in database
            # This follows the pattern seen in the CSV: 1000, 961, 943, 926, etc.
            if position == 1:
                return 1000
            elif position == 2:
                return 961
            elif position == 3:
                return 943
            elif position == 4:
                return 926
            elif position == 5:
                return 911
            elif position == 6:
                return 896
            elif position == 7:
                return 883
            elif position == 8:
                return 870
            elif position == 9:
                return 857
            elif position == 10:
                return 846
            else:
                # Approximate formula for positions > 10
                return max(500, int(1000 * 0.985 ** (position - 1)))


class EventDisciplineResult(models.Model):
    """Tracks the discipline-specific results for an event"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='discipline_results')
    discipline = models.CharField(max_length=100)
    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='discipline_results')
    
    class Meta:
        unique_together = ['event', 'discipline', 'result']
        
    def __str__(self):
        return f"{self.event.title} - {self.discipline}"


class LeagueStanding(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='standings')
    competitor = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True)
    competitor_name = models.CharField(max_length=200)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, related_name='standings')
    points = models.IntegerField(default=0)
    position = models.PositiveIntegerField(null=True, blank=True)
    events_competed = models.PositiveIntegerField(default=0)
    average_rank = models.FloatField(default=0)
    
    # Event-specific results
    event_results = models.JSONField(default=dict, blank=True, help_text="JSON with event results: {event_slug: {points: X, position: Y}}")
    
    class Meta:
        ordering = ['-points', 'position']
        unique_together = ['league', 'competitor_name', 'discipline']
        
    def __str__(self):
        return f"{self.competitor_name} - {self.discipline.name} - {self.points} pts"
