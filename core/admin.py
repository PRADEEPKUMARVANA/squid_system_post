from django.contrib import admin
from .models import (SquidCastInfo, SquidGenre, SquidMovie, SquidMovieToGenre,
                     SquidPerson, SquidPersonToGenre, SquidRole)
# Register your models here.
admin.site.register(SquidCastInfo)
admin.site.register(SquidGenre)
admin.site.register(SquidMovie)
admin.site.register(SquidMovieToGenre)
admin.site.register(SquidPerson)
admin.site.register(SquidPersonToGenre)
admin.site.register(SquidRole)
