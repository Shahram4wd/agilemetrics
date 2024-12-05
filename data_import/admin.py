from django.contrib import admin
from .models import IssueType


@admin.register(IssueType)
class IssueTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'icon_url', 'hierarchy_level', 'subtask')
    search_fields = ('id', 'name', 'description')
    list_filter = ('subtask', 'hierarchy_level')
    ordering = ('id',)
