# core/models.py
from django.db import models

# ==============================================================================
# LAYER 1: RAW INGESTION (Staging Tables)
# Load your TSV files into these tables first.
# ==============================================================================

class RawTitle(models.Model):
    """Maps to title.basics.tsv.gz"""
    tconst = models.CharField(max_length=20, primary_key=True)
    primary_title = models.CharField(max_length=500)
    start_year = models.IntegerField(null=True, db_index=True)
    genres = models.CharField(max_length=255, null=True) # Raw string "Action,Comedy"

class RawPerson(models.Model):
    """Maps to name.basics.tsv.gz"""
    nconst = models.CharField(max_length=20, primary_key=True)
    primary_name = models.CharField(max_length=255, db_index=True)

class RawPrincipal(models.Model):
    """Maps to title.principals.tsv.gz"""
    tconst = models.ForeignKey(RawTitle, on_delete=models.CASCADE)
    nconst = models.ForeignKey(RawPerson, on_delete=models.CASCADE)
    category = models.CharField(max_length=100, db_index=True) # Raw string "actor"

# ==============================================================================
# LAYER 2: SQUID NORMALIZED SCHEMA (Paper A)
# Clean entities for logical reasoning.
# ==============================================================================

class SquidGenre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name.title

class SquidRole(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name.title


class SquidMovie(models.Model):
    tconst = models.OneToOneField(RawTitle, on_delete=models.CASCADE, primary_key=True)
    title = models.CharField(max_length=500)
    year = models.IntegerField(null=True)
    genres = models.ManyToManyField(SquidGenre, through='SquidMovieToGenre')
    def __str__(self):
        return self.title


class SquidPerson(models.Model):
    nconst = models.OneToOneField(RawPerson, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name

class SquidMovieToGenre(models.Model):
    movie = models.ForeignKey(SquidMovie, on_delete=models.CASCADE)
    genre = models.ForeignKey(SquidGenre, on_delete=models.CASCADE)
    class Meta:
        unique_together = ('movie', 'genre')
    def __str__(self):
        return f"{self.movie.title} - {self.genre.name}"
    

class SquidCastInfo(models.Model):
    person = models.ForeignKey(SquidPerson, on_delete=models.CASCADE)
    movie = models.ForeignKey(SquidMovie, on_delete=models.CASCADE)
    role = models.ForeignKey(SquidRole, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.person.name} - {self.movie.title} - {self.role.name}"


# ==============================================================================
# LAYER 3: ABDUCTION-READY DATABASE (@DB) (Paper B)
# Pre-computed statistics for fast intent discovery.
# ==============================================================================

class SquidPersonToGenre(models.Model):
    """
    Derived Relation: Stores 'Association Strength'
    e.g., Person X has appeared in Y movies of Genre Z.
    """
    person = models.ForeignKey(SquidPerson, on_delete=models.CASCADE)
    genre = models.ForeignKey(SquidGenre, on_delete=models.CASCADE)
    count = models.IntegerField(db_index=True) # The specific stat used for abduction

    class Meta:
        unique_together = ('person', 'genre')
        indexes = [
            models.Index(fields=['genre', 'count']),
        ]
    def __str__(self):
        return f"{self.person.name} - {self.genre.name}"