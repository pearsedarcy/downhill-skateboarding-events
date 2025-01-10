from django.db import models
from events.models import Event
from profiles.models import UserProfile
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify

class League(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, null=True)
    description = models.TextField(blank=True)
    events = models.ManyToManyField(Event, related_name='leagues')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Result(models.Model):
    RESULT_TYPES = [
        ('TIME_TRIAL', 'Time Trial'),
        ('KNOCKOUT', 'Knockout')
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

class LeagueStanding(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='standings')
    competitor = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    position = models.PositiveIntegerField(null=True, blank=True)
    events_competed = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-points', 'position']
