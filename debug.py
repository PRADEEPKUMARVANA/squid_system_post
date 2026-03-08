import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "squid_system_post.settings")
django.setup()

from core.models import SquidPerson, SquidPersonToGenre

def check_actor(name):
    print(f"\n--- Checking: {name} ---")
    person = SquidPerson.objects.filter(name=name).first()
    
    if not person:
        print(f"❌ MISSING: '{name}' is not in the database.")
        print("   -> Reason: The 'load_imdb' script didn't finish loading all rows.")
        return

    # Check if they have derived stats
    stats = SquidPersonToGenre.objects.filter(person=person)
    if stats.count() == 0:
        print(f"❌ EMPTY BRAIN: '{name}' exists but has no genre stats.")
        print("   -> Reason: 'build_squid_db' needs to run again.")
    else:
        print(f"✅ OK: '{name}' is ready. (Has {stats.count()} genre stats)")

# Run the check
names = ["Jim Carrey", "Adam Sandler", "Eddie Murphy"]
for n in names:
    check_actor(n)