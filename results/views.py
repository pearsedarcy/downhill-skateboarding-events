from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
import csv
import io
from datetime import datetime
from django.utils import timezone
from .models import Result, TimeTrialResult, KnockoutResult, League, LeagueStanding
from events.models import Event
from profiles.models import UserProfile
from django.db.models import Q, Count
from django_countries import countries

@login_required
def upload_results(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    # Only event organizers can upload results
    if request.user.profile != event.organizer:
        messages.error(request, "You don't have permission to upload results for this event.")
        return redirect('events:event_details', slug=event.slug)
    
    if request.method == 'POST':
        result_type = request.POST.get('result_type')
        results_file = request.FILES.get('results_file')
        is_final = request.POST.get('is_final') == 'on'
        
        if not results_file or not result_type:
            messages.error(request, 'Please provide both a results file and result type.')
            return render(request, 'results/upload_results.html', {'event': event})
        
        try:
            # Create a new result object
            result = Result.objects.create(
                event=event,
                result_type=result_type,
                uploaded_by=request.user.profile,
                raw_data=results_file,
                is_final=is_final
            )
            
            # Process the CSV file
            csv_data = io.StringIO(results_file.read().decode('utf-8'))
            
            if result_type == 'TIME_TRIAL':
                process_time_trial_results(csv_data, result)
            elif result_type == 'KNOCKOUT':
                process_knockout_results(csv_data, result)
            
            # Update event status
            event.has_results = True
            event.save()
            
            messages.success(request, f'{result_type} results uploaded successfully.')
            return redirect('results:view_results', event_id=event.id)
            
        except Exception as e:
            messages.error(request, f'Error processing results: {str(e)}')
            return render(request, 'results/upload_results.html', {'event': event})
    
    return render(request, 'results/upload_results.html', {'event': event})

def process_time_trial_results(csv_data, result):
    reader = csv.DictReader(csv_data)
    for row in reader:
        competitor_username = row['competitor']
        position = int(row['position'])
        
        # Parse time - expected format: MM:SS.ms or SS.ms
        time_str = row['time']
        if ':' in time_str:
            minutes, seconds = time_str.split(':')
            time_obj = datetime.strptime(f"00:{minutes}:{seconds}", "%H:%M:%S.%f")
        else:
            time_obj = datetime.strptime(f"00:00:{time_str}", "%H:%M:%S.%f")
        
        points = int(row['points'])
        
        # Get competitor profile
        try:
            competitor = UserProfile.objects.get(user__username=competitor_username)
            
            # Create time trial result
            TimeTrialResult.objects.create(
                result=result,
                competitor=competitor,
                position=position,
                time=time_obj.time(),
                points=points
            )
        except UserProfile.DoesNotExist:
            raise ValueError(f"User {competitor_username} does not exist.")

def process_knockout_results(csv_data, result):
    reader = csv.DictReader(csv_data)
    for row in reader:
        round_name = row['round']
        match_number = int(row['match_number'])
        winner_username = row['winner']
        loser_username = row['loser']
        
        try:
            winner = UserProfile.objects.get(user__username=winner_username)
            loser = UserProfile.objects.get(user__username=loser_username)
            
            # Create knockout result
            KnockoutResult.objects.create(
                result=result,
                round=round_name,
                winner=winner,
                loser=loser,
                match_number=match_number
            )
        except UserProfile.DoesNotExist as e:
            raise ValueError(f"User does not exist: {str(e)}")

def view_results(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    context = {
        'event': event,
        'time_trial_results': event.results.filter(
            result_type='TIME_TRIAL'
        ).order_by('-is_final', '-uploaded_at'),
        'knockout_results': event.results.filter(
            result_type='KNOCKOUT'
        ).order_by('-is_final', '-uploaded_at')
    }
    
    return render(request, 'results/view_results.html', context)

def get_default_years():
    current_year = timezone.now().year
    return range(current_year, current_year - 10, -1)

def league_standings(request, slug):
    league = get_object_or_404(League, slug=slug)
    
    # Get the year from query params or default to current year
    year = request.GET.get('year', timezone.now().year)
    try:
        year = int(year)
    except (TypeError, ValueError):
        year = timezone.now().year
    
    # Get all years that have standings for this league
    db_years = LeagueStanding.objects.filter(
        league=league
    ).values_list('year', flat=True).distinct()
    
    # Combine database years with default years
    available_years = sorted(set(list(db_years) + list(get_default_years())), reverse=True)
    
    standings = league.standings.filter(year=year)
    
    return render(request, 'results/league_standings.html', {
        'league': league,
        'standings': standings,
        'current_year': year,
        'available_years': available_years
    })

def results_list(request):
    time_trial_results = Result.objects.filter(
        result_type='TIME_TRIAL',
        is_final=True
    ).select_related('event').order_by('-uploaded_at')
    
    knockout_results = Result.objects.filter(
        result_type='KNOCKOUT',
        is_final=True
    ).select_related('event').order_by('-uploaded_at')
    
    context = {
        'time_trial_results': time_trial_results,
        'knockout_results': knockout_results
    }
    
    return render(request, 'results/results_list.html', context)

def league_list(request):
    # Start with all leagues
    leagues_queryset = League.objects.all()
    
    # Get the year from query params or default to current year
    year = request.GET.get('year', timezone.now().year)
    try:
        year = int(year)
    except (TypeError, ValueError):
        year = timezone.now().year
    
    # Apply filters if provided
    name_filter = request.GET.get('name')
    if name_filter:
        leagues_queryset = leagues_queryset.filter(name__icontains=name_filter)
    
    league_class_filter = request.GET.get('league_class')
    if league_class_filter:
        leagues_queryset = leagues_queryset.filter(league_class=league_class_filter)
        
    country_filter = request.GET.get('country')
    if country_filter:
        leagues_queryset = leagues_queryset.filter(country=country_filter)
    
    continent_filter = request.GET.get('continent')
    if continent_filter:
        leagues_queryset = leagues_queryset.filter(continent=continent_filter)
    
    events_count_filter = request.GET.get('events_count')
    if events_count_filter:
        leagues_queryset = leagues_queryset.annotate(
            total_events=Count('events')
        ).filter(total_events__gte=int(events_count_filter))
    
    # Order by name
    leagues = leagues_queryset.order_by('name').prefetch_related(
        'standings__competitor__user'
    )
    
    # Add top 3 standings for the selected year to each league
    for league in leagues:
        league.top_standings = league.standings.filter(year=year)[:3]
    
    # Get all years that have standings plus default years
    db_years = LeagueStanding.objects.values_list(
        'year', flat=True
    ).distinct()
    
    # Combine database years with default years
    available_years = sorted(set(list(db_years) + list(get_default_years())), reverse=True)
    
    # Get all countries for the filter dropdown
    countries_list = list(countries)
    
    return render(request, 'results/league_list.html', {
        'leagues': leagues,
        'countries': countries_list,
        'continents': League.CONTINENT_CHOICES,
        'current_year': year,
        'available_years': available_years
    })
