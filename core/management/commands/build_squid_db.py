# core/management/commands/build_squid_db.py
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Builds the SQUID Abduction-Ready Database from Raw Tables'

    def handle(self, *args, **kwargs):
        self.stdout.write("--- Starting SQUID @DB Construction ---")
        
        # 1. Genres
        self.run_sql("""
            INSERT INTO core_squidgenre (name)
            SELECT DISTINCT unnest(string_to_array(genres, ',')) 
            FROM core_rawtitle WHERE genres IS NOT NULL
            ON CONFLICT (name) DO NOTHING;
        """, "Extracted Genres")

        # 2. Roles
        self.run_sql("""
            INSERT INTO core_squidrole (name)
            SELECT DISTINCT category FROM core_rawprincipal
            ON CONFLICT (name) DO NOTHING;
        """, "Extracted Roles")

        # 3. Normalized Movies
        self.run_sql("""
            INSERT INTO core_squidmovie (tconst_id, title, year)
            SELECT tconst, primary_title, start_year FROM core_rawtitle
            ON CONFLICT DO NOTHING;
        """, "Normalized Movies")

        # 4. Normalized Persons
        self.run_sql("""
            INSERT INTO core_squidperson (nconst_id, name)
            SELECT nconst, primary_name FROM core_rawperson
            ON CONFLICT DO NOTHING;
        """, "Normalized Persons")

        # 5. Link Movies to Genres
        self.run_sql("""
            INSERT INTO core_squidmovietogenre (movie_id, genre_id)
            SELECT t.tconst, g.id
            FROM core_rawtitle t
            CROSS JOIN LATERAL unnest(string_to_array(t.genres, ',')) AS genre_name
            JOIN core_squidgenre g ON g.name = genre_name
            ON CONFLICT DO NOTHING;
        """, "Linked Movies to Genres")

        # 6. Link Cast to Movies
        self.run_sql("""
            INSERT INTO core_squidcastinfo (person_id, movie_id, role_id)
            SELECT p.nconst_id, p.tconst_id, r.id
            FROM core_rawprincipal p
            JOIN core_squidrole r ON p.category = r.name
            ON CONFLICT DO NOTHING;
        """, "Linked Cast Info")

        # 7. Build Derived Table (@DB) - CRITICAL STEP
        self.run_sql("DELETE FROM core_squidpersontogenre;", "Cleared old derived data")
        self.run_sql("""
            INSERT INTO core_squidpersontogenre (person_id, genre_id, count)
            SELECT 
                c.person_id, 
                mg.genre_id, 
                COUNT(*) as count
            FROM core_squidcastinfo c
            JOIN core_squidmovietogenre mg ON c.movie_id = mg.movie_id
            GROUP BY c.person_id, mg.genre_id;
        """, "Built Derived Table: PersonToGenre")

        self.stdout.write(self.style.SUCCESS("--- SQUID Database Ready ---"))

    def run_sql(self, query, msg):
        self.stdout.write(f"... {msg}")
        with connection.cursor() as cursor:
            cursor.execute(query)