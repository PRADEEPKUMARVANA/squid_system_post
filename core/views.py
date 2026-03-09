from django.shortcuts import render, redirect
from django.db.models import Count, Min
from .models import (
    SquidPerson, 
    SquidPersonToGenre, 
    SquidMovie, 
    SquidGenre
)

# ==========================================
# 1. HOME PAGE
# ==========================================
def home(request):
    """
    Renders the main search landing page.
    """
    return render(request, 'home.html')


# ==========================================
# 2. DASHBOARD (System Health)
# ==========================================
def dashboard(request):
    """
    Displays the real-time statistics of the SQUID Knowledge Base.
    """
    context = {
        'counts': {
            'movies': SquidMovie.objects.count(),
            'people': SquidPerson.objects.count(),
            'genres': SquidGenre.objects.count(),
            'derived': SquidPersonToGenre.objects.count(), 
        }
    }
    return render(request, 'dashboard.html', context)


# ==========================================
# 3. SEARCH ENGINE (Abduction Logic)
# ==========================================
def search(request):
    """
    The Core SQUID Logic.
    Includes 'Smart Disambiguation' to handle duplicate names in IMDb.
    """
    if request.method == "POST":
        # --- Step A: Parse Input ---
        raw_input = request.POST.get('examples', '')
        example_names = [x.strip() for x in raw_input.split(',') if x.strip()]
        
        if not example_names:
            return render(request, 'home.html', {'error': 'Please enter at least one name.'})

        # --- Step B: Smart Disambiguation (THE FIX) ---
        # IMDb has multiple people with the same name.
        # We loop through each name and pick the ONE ID that has the most data.
        
        target_ids = []
        
        for name in example_names:
            # 1. Find all candidates with this name (e.g. all "Adam Sandlers")
            candidates = SquidPerson.objects.filter(name__iexact=name)
            
            if not candidates.exists():
                return render(request, 'home.html', {
                    'error': f"Could not find any actor named '{name}' in the database."
                })

            # 2. Pick the 'Best' candidate
            best_id = None
            max_links = -1
            
            for person in candidates:
                # Check how much data this specific ID has in the 'Brain' table
                link_count = SquidPersonToGenre.objects.filter(person=person).count()
                
                # Keep the ID with the most connections (The famous one)
                if link_count > max_links:
                    max_links = link_count
                    best_id = person.nconst_id
            
            # 3. Add the winner to our target list
            if best_id and max_links > 0:
                target_ids.append(best_id)
            else:
                # If we found the name but they have 0 stats, we can't use them
                return render(request, 'home.html', {
                    'error': f"Found '{name}', but they have no movie data analyzed. Try a more famous example."
                })

        # --- Step C: Abductive Reasoning ---
        # Now we search using ONLY the confirmed 'Best' IDs
        
        shared_properties = (
            SquidPersonToGenre.objects
            .filter(person_id__in=target_ids)       
            .values('genre__name')                  
            .annotate(
                hits=Count('person_id'),            
                strength=Min('count')               
            )
            .filter(hits=len(target_ids)) # Strict intersection: Must apply to ALL confirmed IDs
            .order_by('-strength')                  
        )

        if not shared_properties:
            return render(request, 'home.html', {
                'error': f"No common pattern found for: {', '.join(example_names)}. Try picking people who clearly share a genre (e.g. all Comedy actors)."
            })

        # --- Step D: Construct Query & Results ---
        best_fit = shared_properties[0]
        genre_name = best_fit['genre__name']
        min_count = best_fit['strength']
        
        explanation = (
            f"All these actors have appeared in at least {min_count} "
            f"movies belonging to the '{genre_name}' genre."
        )

        final_results = (
            SquidPersonToGenre.objects
            .filter(genre__name=genre_name, count__gte=min_count) 
            .exclude(person_id__in=target_ids) # Don't show the user's input in the results
            .values('person__name', 'count')
            .order_by('-count')[:50]
        )

        context = {
            'user_examples': example_names,
            'explanation': explanation,
            'filter_genre': genre_name,
            'results': final_results,
        }
        return render(request, 'results.html', context)
    
    return redirect('home')