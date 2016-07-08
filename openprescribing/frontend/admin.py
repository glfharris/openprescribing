from django.contrib import admin
from .models import SearchBookmark


@admin.register(SearchBookmark)
class SearchBookmarkAdmin(admin.ModelAdmin):
    pass
