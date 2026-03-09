# core/abduction.py
import os
import django
from django.db.models import Count, Min

# Setup Django if running as a standalone script
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "squid_system.settings")
django.setup()

from core.models import SquidPerson, SquidPersonToGenre

def explain_user_intent(example_names):
    """
    Input: List of actor names e.g. ['Jim Carrey', 'Adam Sandler']
    Output: The derived semantic filter.
    """
    print(f"Analyzing examples: {example_names}")
    
    # 1. Disambiguation (Map names to IDs)
    persons = SquidPerson.objects.filter(name__in=example_names)
    person_ids = [p.nconst_id for p in persons]
    
    if len(person_ids) != len(example_names):
        print("Warning: Some names could not be found in the database.")
        if not person_ids: return

    # 2. Abductive Reasoning (Find shared Derived Properties)
    # We look for a Genre where ALL provided actors have appeared.
    # We take the MINIMUM count to establish the 'threshold' (theta).
    shared_properties = (
        SquidPersonToGenre.objects
        .filter(person_id__in=person_ids)
        .values('genre__name')
        .annotate(
            hits=Count('person_id'), 
            strength=Min('count')
        )
        .filter(hits=len(person_ids)) # Strict intersection: Must apply to ALL
        .order_by('-strength')
    )

    # 3. Output Results
    if not shared_properties:
        print("No significant commonality found.")
    
    for prop in shared_properties:
        print(f"[FOUND INTENT] Filter: Genre = '{prop['genre__name']}'")
        print(f"               Logic:  Appeared in at least {prop['strength']} movies of this genre.")
        print("-" * 40)

if __name__ == "__main__":
    # Test Case
    explain_user_intent(['Jim Carrey', 'Eddie Murphy'])