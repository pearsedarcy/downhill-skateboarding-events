from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from functools import reduce
from operator import add
from django.db.models import Q

class SearchableModel(models.Model):
    search_fields = []
    search_field_weights = {}

    class Meta:
        abstract = True

    @classmethod
    def search(cls, query_string):
        if not cls.search_fields or not query_string:
            return cls.objects.none()
            
        vectors = [
            SearchVector(
                field, 
                weight=cls.search_field_weights.get(field, 'D'),
            
            ) 
            for field in cls.search_fields
        ]
        
        # Combine vectors using reduce
        search_vector = reduce(add, vectors)
        search_query = SearchQuery(query_string)
        
        # First try exact matches
        results = cls.objects.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query)
        ).filter(search=search_query).order_by('-rank')

        # If no exact matches, try partial matches
        if not results.exists():
            # Split query into words for partial matching
            query_words = query_string.split()
            q_objects = Q()
            for word in query_words:
                for field in cls.search_fields:
                    q_objects |= Q(**{f"{field}__icontains": word})
            results = cls.objects.filter(q_objects).annotate(
                rank=SearchRank(search_vector, search_query)
            ).order_by('-rank')

        return results

class SearchQuery(models.Model):
    query = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    result_count = models.IntegerField(default=0)
