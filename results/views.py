from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
import csv
import io
import json
from datetime import datetime
from django.db.models import Q, Count, Avg, Min, Max, Sum
from django.db import transaction
from django.urls import reverse
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django_countries import countries

from .models import (
    Result, TimeTrialResult, KnockoutResult, BracketResult, 
    League, LeagueStanding, Discipline, LeagueEvent, 
    PointsSystem, CSVColumnMapping, EventDisciplineResult
)
from events.models import Event
from profiles.models import UserProfile
from .forms import (
    ResultUploadForm, LeagueForm, CSVColumnMappingForm, 
    BracketResultUploadForm, LeagueEventForm, DisciplineForm
)

@login_required
def upload_results(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    # Only event organizers can upload results
    if request.user.profile != event.organizer:
        messages.error(request, "You don't have permission to upload results for this event.")
        return redirect('events:event_details', slug=event.slug)
    
    if request.method == 'POST':
        result_type = request.POST.get('result_type')
        
        # For bracket results, use the special form
        if result_type == 'BRACKET':
            return redirect('results:upload_bracket_results', event_id=event.id)
            
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

@login_required
def upload_bracket_results(request, event_id):
    """Multi-step wizard for uploading bracket results"""
    event = get_object_or_404(Event, id=event_id)
    
    # Check permission
    if request.user.profile != event.organizer:
        messages.error(request, "You don't have permission to upload results for this event.")
        return redirect('events:event_details', slug=event.slug)
    
    # Step management
    step = request.session.get('bracket_upload_step', 1)
    temp_data = request.session.get('bracket_temp_data', {})
    
    if request.method == 'POST':
        if 'previous_step' in request.POST:
            step = max(1, step - 1)
            request.session['bracket_upload_step'] = step
            return render(request, 'results/upload_bracket_results.html', {
                'event': event, 
                'step': step, 
                'temp_data': temp_data
            })
            
        if step == 1:  # File upload and league selection
            form = BracketResultUploadForm(request.POST, request.FILES, event_id=event.id)
            if form.is_valid():
                league = form.cleaned_data['league']
                csv_file = request.FILES['results_file']
                is_final = form.cleaned_data.get('is_final', False)
                
                # Read and validate CSV
                try:
                    csv_data = csv_file.read().decode('utf-8')
                    reader = csv.reader(io.StringIO(csv_data))
                    headers = next(reader)
                    rows = list(reader)
                    
                    # Store in session
                    temp_data = {
                        'league_id': league.id,
                        'headers': headers,
                        'rows': rows,
                        'is_final': is_final,
                        'csv_data': csv_data
                    }
                    request.session['bracket_temp_data'] = temp_data
                    
                    # Move to step 2
                    step = 2
                    request.session['bracket_upload_step'] = step
                    
                    # Generate mapping form with headers
                    mapping_form = CSVColumnMappingForm(csv_headers=headers)
                    
                    return render(request, 'results/upload_bracket_results.html', {
                        'event': event, 
                        'step': step,
                        'temp_data': temp_data,
                        'mapping_form': mapping_form,
                        'league': league
                    })
                except Exception as e:
                    messages.error(request, f"Error reading CSV: {str(e)}")
        
        elif step == 2:  # Column mapping
            league = get_object_or_404(League, id=temp_data['league_id'])
            mapping_form = CSVColumnMappingForm(
                request.POST, 
                csv_headers=temp_data.get('headers', [])
            )
            
            if mapping_form.is_valid():
                # Create mapping dictionary
                mapping = {}
                for header in temp_data.get('headers', []):
                    field_id = f"map_{header.replace(' ', '_').lower()}"
                    mapped_value = mapping_form.cleaned_data.get(field_id)
                    if mapped_value and mapped_value != 'IGNORE':
                        mapping[header] = mapped_value
                
                # Check required fields
                required_fields = {'RANK', 'NAME'}
                mapped_fields = set(mapping.values())
                
                if not required_fields.issubset(mapped_fields):
                    missing = required_fields - mapped_fields
                    messages.error(
                        request, 
                        f"Missing required mappings: {', '.join(missing)}"
                    )
                else:
                    # Store mapping
                    temp_data['mapping'] = mapping
                    
                    # Auto-detect disciplines
                    disciplines = detect_disciplines(temp_data)
                    temp_data['disciplines'] = disciplines
                    
                    request.session['bracket_temp_data'] = temp_data
                    
                    # Move to preview
                    step = 3
                    request.session['bracket_upload_step'] = step
                    
                    # Process preview data
                    preview_data = process_bracket_preview(temp_data)
                    
                    return render(request, 'results/upload_bracket_results.html', {
                        'event': event,
                        'step': step,
                        'temp_data': temp_data,
                        'preview_data': preview_data,
                        'league': league,
                        'disciplines': disciplines
                    })
            
            # If form validation fails
            return render(request, 'results/upload_bracket_results.html', {
                'event': event, 
                'step': step,
                'temp_data': temp_data,
                'mapping_form': mapping_form,
                'league': league
            })
        
        elif step == 3:  # Confirmation and save
            try:
                league = get_object_or_404(League, id=temp_data['league_id'])
                
                # Create result record
                with transaction.atomic():
                    result = Result.objects.create(
                        event=event,
                        result_type='BRACKET',
                        uploaded_by=request.user.profile,
                        raw_data=ContentFile(
                            content=temp_data['csv_data'],
                            name=f"{event.slug}_bracket_{league.slug}.csv"
                        ),
                        is_final=temp_data['is_final']
                    )
                    
                    # Process the bracket results
                    disciplines_processed = save_bracket_results(result, temp_data)
                    
                    # Update league standings
                    for discipline in disciplines_processed:
                        update_league_standings_for_bracket(league, discipline, result)
                    
                    # Update event status
                    event.has_results = True
                    event.save()
                
                # Clear session data
                del request.session['bracket_upload_step']
                del request.session['bracket_temp_data']
                
                messages.success(request, "Bracket results uploaded and league standings updated successfully!")
                return redirect('results:view_results', event_id=event.id)
                
            except Exception as e:
                messages.error(request, f"Error saving results: {str(e)}")
    
    else:  # GET request
        if step == 1:
            form = BracketResultUploadForm(event_id=event.id)
            # Reset session on fresh start
            request.session['bracket_upload_step'] = 1
            request.session['bracket_temp_data'] = {}
            
            return render(request, 'results/upload_bracket_results.html', {
                'event': event,
                'step': step,
                'form': form
            })
        else:
            # If navigating directly to a later step, redirect to step 1
            return redirect('results:upload_bracket_results', event_id=event.id)


def detect_disciplines(temp_data):
    """Auto-detect disciplines from the CSV data"""
    disciplines = []
    mapping = temp_data['mapping']
    headers = temp_data['headers']
    rows = temp_data['rows']
    
    # Check if there's a discipline column
    discipline_header = None
    for header, field_type in mapping.items():
        if field_type == 'DISCIPLINE':
            discipline_header = header
            break
    
    if discipline_header:
        # Get discipline column index
        discipline_idx = headers.index(discipline_header)
        
        # Extract unique disciplines from that column
        unique_disciplines = set()
        for row in rows:
            if len(row) > discipline_idx and row[discipline_idx].strip():
                unique_disciplines.add(row[discipline_idx].strip())
        
        disciplines = sorted(list(unique_disciplines))
        
    else:
        # Check if we have headers that appear to be disciplines
        potential_disciplines = []
        for header in headers:
            if header.lower() not in ['rank', 'position', 'points', 'pnts', 'name']:
                potential_disciplines.append(header)
        
        # Filter out headers mapped to other fields
        disciplines = [h for h in potential_disciplines 
                      if h not in mapping.keys() or mapping[h] == 'DISCIPLINE']
    
    # If we still don't have disciplines, add a default one
    if not disciplines:
        disciplines = ['Open']
        
    return disciplines


def process_bracket_preview(temp_data):
    """Process bracket data for preview"""
    mapping = temp_data['mapping']
    headers = temp_data['headers']
    rows = temp_data['rows']
    disciplines = temp_data.get('disciplines', [])
    
    # Find indices for mapped columns
    indices = {}
    for header, field_type in mapping.items():
        indices[field_type] = headers.index(header)
    
    # If we have a discipline column, use it
    use_discipline_column = 'DISCIPLINE' in indices
    
    # Process each row and group by discipline
    preview_data = {}
    
    # Initialize preview data structure for each discipline
    for discipline in disciplines:
        preview_data[discipline] = []
    
    # Process each row
    for row in rows:
        if len(row) <= max(indices.values()):
            continue  # Skip rows with insufficient data
        
        # Get rank and name
        try:
            rank = int(row[indices.get('RANK')])
            name = row[indices.get('NAME')]
        except (ValueError, IndexError):
            continue  # Skip rows with invalid rank
        
        # Get points if available
        points = 0
        if 'POINTS' in indices and len(row) > indices['POINTS']:
            try:
                points = int(row[indices['POINTS']])
            except ValueError:
                points = PointsSystem.get_points_for_position(rank)
        else:
            points = PointsSystem.get_points_for_position(rank)
        
        # Determine which discipline this row belongs to
        if use_discipline_column:
            discipline = row[indices['DISCIPLINE']]
            if discipline not in preview_data:
                preview_data[discipline] = []
        else:
            # If no discipline column, assign to the first discipline
            discipline = disciplines[0] if disciplines else 'Open'
        
        # Add to preview data
        if discipline in preview_data:
            preview_data[discipline].append({
                'rank': rank,
                'name': name,
                'points': points
            })
    
    # Sort each discipline by rank
    for discipline in preview_data:
        preview_data[discipline] = sorted(
            preview_data[discipline], key=lambda x: x['rank']
        )
    
    return preview_data


def save_bracket_results(result, temp_data):
    """Save processed bracket results to database"""
    mapping = temp_data['mapping']
    headers = temp_data['headers']
    rows = temp_data['rows']
    disciplines = temp_data.get('disciplines', ['Open'])
    event = result.event
    
    # Find indices for mapped columns
    indices = {}
    for header, field_type in mapping.items():
        indices[field_type] = headers.index(header)
    
    # Check if we have a discipline column
    use_discipline_column = 'DISCIPLINE' in indices
    
    # Track which disciplines were processed
    processed_disciplines = set()
    
    # Process each row
    for row in rows:
        if len(row) <= max(indices.values()):
            continue  # Skip rows with insufficient data
        
        try:
            # Get rank and name
            rank = int(row[indices['RANK']])
            name = row[indices['NAME']].strip()
            
            if not name:  # Skip rows with empty names
                continue
                
            # Get points if available
            points = 0
            if 'POINTS' in indices and len(row) > indices['POINTS']:
                try:
                    points = int(row[indices['POINTS']])
                except ValueError:
                    points = PointsSystem.get_points_for_position(rank)
            else:
                points = PointsSystem.get_points_for_position(rank)
            
            # Determine discipline
            if use_discipline_column:
                discipline = row[indices['DISCIPLINE']].strip()
                if not discipline:
                    discipline = 'Open'
            else:
                # If multiple disciplines but no column, we can't determine
                # so use the first one
                discipline = disciplines[0]
            
            # Record that this discipline was processed
            processed_disciplines.add(discipline)
            
            # Try to find the user profile by name
            user_profile = None
            try:
                # Try to match by username, first/last name, or full name
                name_parts = name.split()
                if len(name_parts) >= 2:
                    user_profile = UserProfile.objects.filter(
                        Q(user__username__iexact=name) |
                        Q(user__first_name__iexact=name_parts[0], 
                          user__last_name__iexact=' '.join(name_parts[1:]))
                    ).first()
                else:
                    user_profile = UserProfile.objects.filter(
                        Q(user__username__iexact=name) |
                        Q(user__first_name__iexact=name) |
                        Q(user__last_name__iexact=name)
                    ).first()
            except:
                pass  # If error, continue without profile link
            
            # Create the bracket result
            BracketResult.objects.create(
                result=result,
                competitor_name=name,
                position=rank,
                discipline=discipline,
                points=points,
                competitor_profile=user_profile
            )
            
            # Create or update discipline result record
            EventDisciplineResult.objects.update_or_create(
                event=event,
                discipline=discipline,
                defaults={'result': result}
            )
            
        except (ValueError, IndexError) as e:
            # Log error but continue processing other rows
            print(f"Error processing row: {row}. Error: {e}")
    
    return processed_disciplines


def update_league_standings_for_bracket(league, discipline, result):
    """Update league standings based on bracket results"""
    # Get or create the discipline object
    discipline_obj, created = Discipline.objects.get_or_create(
        league=league,
        name=discipline,
        defaults={'slug': discipline.lower().replace(' ', '-')}
    )
    
    # Get the event and league event relationship
    event = result.event
    try:
        league_event = LeagueEvent.objects.get(league=league, event=event)
        multiplier = league_event.multiplier
    except LeagueEvent.DoesNotExist:
        # If this event isn't part of the league, create the relationship
        league_event = LeagueEvent.objects.create(
            league=league, 
            event=event,
            multiplier=1.0,
            weight=100
        )
        multiplier = 1.0
    
    # Get all bracket results for this discipline
    bracket_results = BracketResult.objects.filter(
        result=result,
        discipline=discipline
    ).order_by('position')
    
    # Process each result
    with transaction.atomic():
        for br in bracket_results:
            # Calculate adjusted points based on multiplier
            adjusted_points = int(br.points * multiplier)
            
            # Get or create standing
            standing, created = LeagueStanding.objects.get_or_create(
                league=league,
                discipline=discipline_obj,
                competitor_name=br.competitor_name,
                defaults={
                    'competitor': br.competitor_profile,
                    'points': adjusted_points,
                    'events_competed': 1,
                    'position': br.position,  # Initial position same as event position
                    'event_results': {
                        event.slug: {
                            'points': adjusted_points,
                            'position': br.position
                        }
                    }
                }
            )
            
            if not created:
                # Update existing standing
                event_results = standing.event_results
                event_results[event.slug] = {
                    'points': adjusted_points,
                    'position': br.position
                }
                
                # Count events and calculate total points
                standing.events_competed = len(event_results)
                standing.points += adjusted_points
                standing.event_results = event_results
                standing.save()
        
        # Recalculate positions and average rank
        recalculate_league_standings(league, discipline_obj)


def recalculate_league_standings(league, discipline):
    """Recalculate positions and stats for league standings"""
    standings = LeagueStanding.objects.filter(
        league=league,
        discipline=discipline
    ).order_by('-points')
    
    # Update positions
    position = 1
    for standing in standings:
        # Calculate average rank from event results
        if standing.event_results and standing.events_competed > 0:
            positions = [result.get('position', 0) for result in standing.event_results.values()]
            standing.average_rank = sum(positions) / len(positions)
        
        standing.position = position
        standing.save()
        position += 1


def view_results(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    # Get bracket results grouped by discipline
    bracket_results = {}
    bracket_result_records = Result.objects.filter(
        event=event,
        result_type='BRACKET'
    ).order_by('-is_final', '-uploaded_at')
    
    for result in bracket_result_records:
        disciplines = BracketResult.objects.filter(result=result).values_list(
            'discipline', flat=True
        ).distinct()
        
        for discipline in disciplines:
            if discipline not in bracket_results:
                bracket_results[discipline] = []
            
            discipline_results = BracketResult.objects.filter(
                result=result,
                discipline=discipline
            ).order_by('position')
            
            bracket_results[discipline].append({
                'result': result,
                'entries': discipline_results
            })
    
    context = {
        'event': event,
        'time_trial_results': event.results.filter(
            result_type='TIME_TRIAL'
        ).order_by('-is_final', '-uploaded_at'),
        'knockout_results': event.results.filter(
            result_type='KNOCKOUT'
        ).order_by('-is_final', '-uploaded_at'),
        'bracket_results': bracket_results
    }
    
    return render(request, 'results/view_results.html', context)

def league_standings(request, slug):
    league = get_object_or_404(League, slug=slug)
    
    # Get all disciplines for this league
    disciplines = Discipline.objects.filter(league=league)
    
    # Get standings for each discipline
    discipline_standings = {}
    for discipline in disciplines:
        discipline_standings[discipline] = LeagueStanding.objects.filter(
            league=league,
            discipline=discipline
        ).order_by('position')
    
    # If no disciplines found, get all standings grouped by discipline name
    if not disciplines:
        raw_standings = LeagueStanding.objects.filter(league=league).order_by('position')
        discipline_names = raw_standings.values_list('discipline__name', flat=True).distinct()
        
        for name in discipline_names:
            discipline_standings[name] = raw_standings.filter(discipline__name=name)
    
    # Get all events in this league
    events = Event.objects.filter(league_links__league=league).order_by('start_date')
    
    context = {
        'league': league,
        'discipline_standings': discipline_standings,
        'events': events,
    }
    
    return render(request, 'results/league_standings.html', context)

def results_list(request):
    time_trial_results = Result.objects.filter(
        result_type='TIME_TRIAL',
        is_final=True
    ).select_related('event').order_by('-uploaded_at')
    
    knockout_results = Result.objects.filter(
        result_type='KNOCKOUT',
        is_final=True
    ).select_related('event').order_by('-uploaded_at')
    
    bracket_results = Result.objects.filter(
        result_type='BRACKET',
        is_final=True
    ).select_related('event').order_by('-uploaded_at')
    
    context = {
        'time_trial_results': time_trial_results,
        'knockout_results': knockout_results,
        'bracket_results': bracket_results
    }
    
    return render(request, 'results/results_list.html', context)

def league_list(request):
    # Start with all leagues
    leagues_queryset = League.objects.all()
    
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
            total_events=Count('league_events')
        ).filter(total_events__gte=int(events_count_filter))
    
    # Order by name and season
    leagues = leagues_queryset.order_by('-season', 'name')
    
    # Get disciplines and top standings for each league
    for league in leagues:
        # Create new attribute for the template rather than trying to assign to the reverse relation
        league.discipline_list = Discipline.objects.filter(league=league)
        league.top_standings = {}
        
        for discipline in league.discipline_list:
            league.top_standings[discipline] = LeagueStanding.objects.filter(
                league=league, 
                discipline=discipline
            ).order_by('position')[:3]
    
    # Get all countries for the filter dropdown
    countries_list = list(countries)
    
    return render(request, 'results/league_list.html', {
        'leagues': leagues,
        'countries': countries_list,
        'continents': League.CONTINENT_CHOICES
    })


# --- LEAGUE MANAGEMENT VIEWS ---

@login_required
def manage_league(request, slug=None):
    """Create or edit a league"""
    if slug:
        league = get_object_or_404(League, slug=slug)
        title = f"Edit League: {league.name}"
    else:
        league = None
        title = "Create New League"
    
    if request.method == 'POST':
        form = LeagueForm(request.POST, request.FILES, instance=league)
        if form.is_valid():
            league = form.save()
            
            if slug:
                messages.success(request, f"League '{league.name}' updated successfully.")
            else:
                messages.success(request, f"League '{league.name}' created successfully.")
                
            return redirect('results:manage_league_events', slug=league.slug)
    else:
        form = LeagueForm(instance=league)
    
    return render(request, 'results/manage/league_form.html', {
        'form': form,
        'league': league,
        'title': title
    })


@login_required
def manage_league_events(request, slug):
    """Manage events in a league"""
    league = get_object_or_404(League, slug=slug)
    
    # Get current league events
    league_events = LeagueEvent.objects.filter(league=league)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_event':
            form = LeagueEventForm(request.POST)
            if form.is_valid():
                event = form.cleaned_data['event']
                multiplier = form.cleaned_data['multiplier']
                weight = form.cleaned_data['weight']
                
                # Check if event already exists
                if not LeagueEvent.objects.filter(league=league, event=event).exists():
                    LeagueEvent.objects.create(
                        league=league,
                        event=event,
                        multiplier=multiplier,
                        weight=weight
                    )
                    messages.success(request, f"Event '{event.title}' added to the league.")
                else:
                    messages.error(request, f"Event '{event.title}' is already in this league.")
                    
                return redirect('results:manage_league_events', slug=league.slug)
                
        elif action == 'remove_event':
            event_id = request.POST.get('event_id')
            if event_id:
                LeagueEvent.objects.filter(league=league, event_id=event_id).delete()
                messages.success(request, "Event removed from the league.")
                
            return redirect('results:manage_league_events', slug=league.slug)
                
        elif action == 'update_event':
            league_event_id = request.POST.get('league_event_id')
            if league_event_id:
                league_event = get_object_or_404(LeagueEvent, id=league_event_id, league=league)
                league_event.multiplier = float(request.POST.get('multiplier', 1.0))
                league_event.weight = int(request.POST.get('weight', 100))
                league_event.save()
                messages.success(request, "Event settings updated.")
                
            return redirect('results:manage_league_events', slug=league.slug)
    
    # Create form for adding new events
    # Exclude events already in the league
    existing_event_ids = league_events.values_list('event_id', flat=True)
    form = LeagueEventForm()
    form.fields['event'].queryset = Event.objects.exclude(id__in=existing_event_ids)
    
    return render(request, 'results/manage/league_events.html', {
        'league': league,
        'league_events': league_events,
        'form': form
    })


@login_required
def manage_league_disciplines(request, slug):
    """Manage disciplines in a league"""
    league = get_object_or_404(League, slug=slug)
    
    # Get current disciplines
    disciplines = Discipline.objects.filter(league=league)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_discipline':
            form = DisciplineForm(request.POST)
            if form.is_valid():
                name = form.cleaned_data['name']
                description = form.cleaned_data['description']
                
                # Create discipline with proper slug
                discipline = Discipline(
                    league=league,
                    name=name,
                    description=description,
                    slug=slugify(name)
                )
                discipline.save()
                
                messages.success(request, f"Discipline '{name}' added to the league.")
                return redirect('results:manage_league_disciplines', slug=league.slug)
                
        elif action == 'remove_discipline':
            discipline_id = request.POST.get('discipline_id')
            if discipline_id:
                Discipline.objects.filter(id=discipline_id, league=league).delete()
                messages.success(request, "Discipline removed from the league.")
                
            return redirect('results:manage_league_disciplines', slug=league.slug)
                
        elif action == 'update_discipline':
            discipline_id = request.POST.get('discipline_id')
            if discipline_id:
                discipline = get_object_or_404(Discipline, id=discipline_id, league=league)
                discipline.name = request.POST.get('name', discipline.name)
                discipline.description = request.POST.get('description', discipline.description)
                discipline.save()
                messages.success(request, "Discipline updated.")
                
            return redirect('results:manage_league_disciplines', slug=league.slug)
    
    # Create empty form for adding disciplines
    form = DisciplineForm()
    
    return render(request, 'results/manage/league_disciplines.html', {
        'league': league,
        'disciplines': disciplines,
        'form': form
    })


@login_required
def recalculate_league(request, slug):
    """Recalculate all league standings from scratch"""
    league = get_object_or_404(League, slug=slug)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Delete existing standings
                LeagueStanding.objects.filter(league=league).delete()
                
                # Get all disciplines
                disciplines = Discipline.objects.filter(league=league)
                
                # Get all events in this league
                league_events = LeagueEvent.objects.filter(league=league)
                
                # For each event and discipline, recalculate standings
                for league_event in league_events:
                    event = league_event.event
                    multiplier = league_event.multiplier
                    
                    # Get all bracket results for this event
                    bracket_results = Result.objects.filter(
                        event=event,
                        result_type='BRACKET',
                        is_final=True
                    )
                    
                    for result in bracket_results:
                        # Get disciplines from results
                        result_disciplines = BracketResult.objects.filter(
                            result=result
                        ).values_list('discipline', flat=True).distinct()
                        
                        for discipline_name in result_disciplines:
                            # Get or create discipline object
                            discipline, created = Discipline.objects.get_or_create(
                                league=league,
                                name=discipline_name,
                                defaults={'slug': slugify(discipline_name)}
                            )
                            
                            # Update league standings for this discipline
                            update_league_standings_for_bracket(
                                league, discipline_name, result
                            )
                
                messages.success(request, "League standings recalculated successfully.")
                
            return redirect('results:league_standings', slug=league.slug)
            
        except Exception as e:
            messages.error(request, f"Error recalculating standings: {str(e)}")
            return redirect('results:league_standings', slug=league.slug)
    
    # Show confirmation page for GET requests
    return render(request, 'results/manage/recalculate_confirmation.html', {
        'league': league
    })
