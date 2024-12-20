from django.shortcuts import render
from django.views.generic import ListView
from django.db.models import Q
from itertools import chain
from .models import SearchQuery
from events.models import Event
from profiles.models import UserProfile  # Changed from Profile to UserProfile

class GlobalSearchView(ListView):
    template_name = 'search/search_results.html'
    context_object_name = 'results'
    paginate_by = 20

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        if not query:
            return []

        # Record the search query
        SearchQuery.objects.create(query=query)
        
        # Updated searchable models list with UserProfile
        searchable_models = [Event, UserProfile]
        
        results = []
        for model in searchable_models:
            results.extend(model.search(query))
        
        return sorted(results, key=lambda x: x.rank, reverse=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context

# Create your views here.
