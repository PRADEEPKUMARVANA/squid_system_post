import gzip
import csv
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from core.models import RawPerson, RawTitle, RawPrincipal

class Command(BaseCommand):
    help = 'Loads compressed IMDb .tsv.gz files into the Raw database tables'

    def handle(self, *args, **kwargs):
        base_dir = settings.BASE_DIR
        data_dir = os.path.join(base_dir, 'data')

        self.stdout.write("--- Step 1: Loading Persons (name.basics) ---")
        self.load_persons(os.path.join(data_dir, 'name.basics.tsv.gz'))

        self.stdout.write("--- Step 2: Loading Titles (title.basics) ---")
        self.load_titles(os.path.join(data_dir, 'title.basics.tsv.gz'))

        self.stdout.write("--- Step 3: Loading Principals (title.principals) ---")
        self.load_principals(os.path.join(data_dir, 'title.principals.tsv.gz'))

        self.stdout.write(self.style.SUCCESS("All data loaded successfully!"))

    def load_persons(self, filepath):
        batch = []
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader) # Skip header
            for row in reader:
                # Row format: nconst(0), primaryName(1), ...
                batch.append(RawPerson(
                    nconst=row[0], 
                    primary_name=row[1]
                ))
                if len(batch) >= 5000:
                    RawPerson.objects.bulk_create(batch, ignore_conflicts=True)
                    batch = []
            if batch: RawPerson.objects.bulk_create(batch, ignore_conflicts=True)

    def load_titles(self, filepath):
        batch = []
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader) 
            for row in reader:
                # Row: tconst(0), titleType(1), primaryTitle(2), ..., startYear(5), ..., genres(8)
                
                # Filter: Only load movies to keep DB small/fast (Optional optimization)
                if row[1] != 'movie': continue 

                year = row[5] if row[5] != '\\N' else None
                genres = row[8] if row[8] != '\\N' else None
                
                batch.append(RawTitle(
                    tconst=row[0],
                    primary_title=row[2][:500], # Truncate if title is too long
                    start_year=year,
                    genres=genres
                ))
                if len(batch) >= 5000:
                    RawTitle.objects.bulk_create(batch, ignore_conflicts=True)
                    batch = []
            if batch: RawTitle.objects.bulk_create(batch, ignore_conflicts=True)

    def load_principals(self, filepath):
        batch = []
        # Cache valid Foreign Keys to avoid IntegrityErrors
        valid_titles = set(RawTitle.objects.values_list('tconst', flat=True))
        valid_people = set(RawPerson.objects.values_list('nconst', flat=True))

        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            next(reader) 
            for row in reader:
                # Row: tconst(0), ordering(1), nconst(2), category(3), ...
                tconst, nconst, category = row[0], row[2], row[3]
                
                # Only add if both Title and Person exist in our DB
                if tconst in valid_titles and nconst in valid_people:
                    batch.append(RawPrincipal(
                        tconst_id=tconst,
                        nconst_id=nconst,
                        category=category
                    ))
                
                if len(batch) >= 5000:
                    RawPrincipal.objects.bulk_create(batch, ignore_conflicts=True)
                    batch = []
            if batch: RawPrincipal.objects.bulk_create(batch, ignore_conflicts=True)