from django.contrib import admin
from .models import Habit, HabitRecord
from .models import JournalEntry, JournalStats, JournalPrompt, HabitJournalLink

admin.site.site_header = "Habit Tracker Admin"
admin.site.site_title = "Habit Tracker Portal"
admin.site.index_title = "Dashboard"


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'user__username')
    ordering = ('-created_at',)


@admin.register(HabitRecord)
class HabitRecordAdmin(admin.ModelAdmin):
    list_display = ('habit', 'date', 'status')
    list_filter = ('status', 'date')
    search_fields = ('habit__name', 'habit__user__username')
    date_hierarchy = 'date'
    ordering = ('-date',)


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'mood', 'word_count', 'entry_type']
    list_filter = ['mood', 'entry_type', 'date', 'user']
    search_fields = ['content', 'user__username']
    readonly_fields = ['word_count', 'created_at', 'updated_at']
    
    def get_tags_display(self, obj):
        return ", ".join(obj.get_tags_list())
    get_tags_display.short_description = "Tags"

@admin.register(JournalStats)
class JournalStatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_entries', 'total_words', 'current_streak', 'longest_streak']
    readonly_fields = ['updated_at']

@admin.register(JournalPrompt)
class JournalPromptAdmin(admin.ModelAdmin):
    list_display = ['category', 'prompt_text', 'is_active']
    list_filter = ['category', 'is_active']

@admin.register(HabitJournalLink)
class HabitJournalLinkAdmin(admin.ModelAdmin):
    list_display = ['user', 'habit', 'journal_entry']