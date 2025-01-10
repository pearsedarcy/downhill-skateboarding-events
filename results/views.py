from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
import csv
import io
from datetime import datetime
from .models import Result, TimeTrialResult, KnockoutResult, League, LeagueStanding
from events.models import Event
from profiles.models import UserProfile

@login_required
def upload_results(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST' and request.FILES.get('results_file'):
        try:
            csv_file = request.FILES['results_file']
            result_type = request.POST.get('result_type')
            is_final = request.POST.get('is_final', False)
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a CSV file.')
                return redirect('events:event_details', slug=event.slug)

            # If this is final result, unmark other results of same type as final
            if is_final:
                Result.objects.filter(
                    event=event,
                    result_type=result_type,
                    is_final=True
                ).update(is_final=False)

            result = Result.objects.create(
                event=event,
                result_type=result_type,
                uploaded_by=request.user.profile,
                raw_data=csv_file,
                is_final=is_final
            )

            # Process CSV file
            decoded_file = csv_file.read().decode('utf-8')
            csv_data = csv.DictReader(io.StringIO(decoded_file))

            if result_type == 'TIME_TRIAL':
                process_time_trial_results(csv_data, result)
            else:
                process_knockout_results(csv_data, result)

            event.has_results = True
            event.save()

            messages.success(request, 'Results uploaded successfully!')
            return redirect('events:event_details', slug=event.slug)

        except Exception as e:
            messages.error(request, f'Error uploading results: {str(e)}')
            return redirect('events:event_details', slug=event.slug)

    return render(request, 'results/upload_results.html', {'event': event})

def process_time_trial_results(csv_data, result):
    for row in csv_data:
        competitor = UserProfile.objects.get(user__username=row['competitor'])
        time_parts = row['time'].split(':')
        time = datetime.strptime(row['time'], '%M:%S.%f').time()
        
        TimeTrialResult.objects.create(
            result=result,
            competitor=competitor,
            position=int(row['position']),
            time=time,
            points=int(row.get('points', 0))
        )

def process_knockout_results(csv_data, result):
    for row in csv_data:
        winner = UserProfile.objects.get(user__username=row['winner'])
        loser = UserProfile.objects.get(user__username=row['loser'])
        
        KnockoutResult.objects.create(
            result=result,
            round=row['round'],
            winner=winner,
            loser=loser,
            match_number=int(row['match_number'])
        )

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

def league_standings(request, slug):
    league = get_object_or_404(League, slug=slug)
    standings = league.standings.all()
    
    return render(request, 'results/league_standings.html', {
        'league': league,
        'standings': standings
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
    leagues = League.objects.all().order_by('name').prefetch_related(
        'standings__competitor__user'
    )
    
    # Add top 3 standings to each league
    for league in leagues:
        league.top_standings = league.standings.all()[:3]
    
    return render(request, 'results/league_list.html', {
        'leagues': leagues
    })
