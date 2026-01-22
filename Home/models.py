from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
import json
from datetime import timedelta

class Habit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def done_today(self):
      return HabitRecord.objects.filter(
        habit=self,
        date=date.today(),
        status=True
      ).exists()


    
class HabitRecord(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    status = models.BooleanField(default=False)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.habit.name} - {self.date}"

    class Meta:
        unique_together = ('habit', 'date')
        
        


class JournalEntry(models.Model):
    MOOD_CHOICES = [
        ('happy', '😊 Happy'),
        ('neutral', '😐 Neutral'),
        ('sad', '😔 Sad'),
        ('excited', '🤩 Excited'),
        ('calm', '😌 Calm'),
        ('grateful', '🙏 Grateful'),
        ('motivated', '💪 Motivated'),
        ('tired', '😴 Tired'),
        ('stressed', '😫 Stressed'),
        ('relaxed', '😎 Relaxed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    content = models.TextField(verbose_name="Journal Entry")
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, default='neutral')
    date = models.DateTimeField(default=timezone.now)
    tags = models.TextField(blank=True, help_text="Store tags as JSON array")  # Storing as JSON
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    word_count = models.IntegerField(default=0)
    
    # Optional: Add entry type
    ENTRY_TYPES = [
        ('daily', 'Daily Reflection'),
        ('gratitude', 'Gratitude Log'),
        ('goal', 'Goal Setting'),
        ('challenge', 'Challenge'),
        ('achievement', 'Achievement'),
        ('random', 'Random Thought'),
    ]
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES, default='daily')
    
    class Meta:
        ordering = ['-date']
        verbose_name = "Journal Entry"
        verbose_name_plural = "Journal Entries"
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['user', 'mood']),
        ]
    
    def __str__(self):
        return f"{self.user.username}'s entry - {self.date.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        # Calculate word count before saving
        self.word_count = len(self.content.split())
        super().save(*args, **kwargs)
    
    def get_tags_list(self):
        """Return tags as Python list"""
        if self.tags:
            try:
                return json.loads(self.tags)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_tags(self, tags_list):
        """Set tags from Python list"""
        self.tags = json.dumps(tags_list)
    
    def get_mood_icon(self):
        """Get emoji icon for mood"""
        mood_icons = {
            'happy': 'emoji-smile',
            'neutral': 'emoji-neutral',
            'sad': 'emoji-frown',
            'excited': 'emoji-heart-eyes',
            'calm': 'emoji-relaxed',
            'grateful': 'heart',
            'motivated': 'lightning',
            'tired': 'moon',
            'stressed': 'exclamation',
            'relaxed': 'sun',
        }
        return mood_icons.get(self.mood, 'emoji-neutral')
    
    def get_mood_color(self):
        """Get CSS class for mood"""
        mood_colors = {
            'happy': 'bg-success',
            'neutral': 'bg-warning',
            'sad': 'bg-danger',
            'excited': 'bg-info',
            'calm': 'bg-primary',
            'grateful': 'bg-success',
            'motivated': 'bg-warning',
            'tired': 'bg-secondary',
            'stressed': 'bg-danger',
            'relaxed': 'bg-info',
        }
        return mood_colors.get(self.mood, 'bg-secondary')


class JournalStats(models.Model):
    """Model to store aggregated journal statistics for faster queries"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='journal_stats')
    total_entries = models.IntegerField(default=0)
    total_words = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    mood_distribution = models.JSONField(default=dict)  # Store mood counts as JSON
    last_entry_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def update_stats(self):
        """Update all statistics"""
        entries = self.user.journal_entries.all()
        
        self.total_entries = entries.count()
        self.total_words = sum(entry.word_count for entry in entries)
        
        # Calculate streak
        self.current_streak = self.calculate_current_streak()
        
        # Update mood distribution
        mood_counts = {}
        for entry in entries:
            mood_counts[entry.mood] = mood_counts.get(entry.mood, 0) + 1
        
        # Convert to percentages
        mood_distribution = {}
        for mood, count in mood_counts.items():
            mood_distribution[mood] = {
                'count': count,
                'percentage': round((count / self.total_entries) * 100, 1) if self.total_entries > 0 else 0
            }
        
        self.mood_distribution = mood_distribution
        
        # Update last entry date
        latest_entry = entries.order_by('-date').first()
        if latest_entry:
            self.last_entry_date = latest_entry.date.date()
        
        self.save()
    
    def calculate_current_streak(self):
        """Calculate current consecutive days with entries"""
        entries = self.user.journal_entries.order_by('-date')
        if not entries:
            return 0
        
        streak = 0
        current_date = timezone.now().date()
        
        for entry in entries:
            entry_date = entry.date.date()
            
            # Check if entries are consecutive
            if streak == 0:
                if entry_date == current_date or entry_date == current_date - timedelta(days=1):
                    streak = 1
                    current_date = entry_date
                else:
                    break
            else:
                if entry_date == current_date - timedelta(days=1):
                    streak += 1
                    current_date = entry_date
                else:
                    break
        
        return streak
    
    def __str__(self):
        return f"Stats for {self.user.username}"


# Optional: For generating journal prompts
class JournalPrompt(models.Model):
    PROMPT_CATEGORIES = [
        ('gratitude', 'Gratitude'),
        ('reflection', 'Self-Reflection'),
        ('goal', 'Goal Setting'),
        ('challenge', 'Challenges'),
        ('creative', 'Creative Writing'),
        ('mindfulness', 'Mindfulness'),
    ]
    
    category = models.CharField(max_length=20, choices=PROMPT_CATEGORIES)
    prompt_text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category']
    
    def __str__(self):
        return f"{self.get_category_display()}: {self.prompt_text[:50]}..."


# Optional: For habit-journal connections
class HabitJournalLink(models.Model):
    """Link habits with journal entries for deeper insights"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    habit = models.ForeignKey('Habit', on_delete=models.CASCADE)  
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['habit', 'journal_entry']
    
    def __str__(self):
        return f"{self.habit.name} - {self.journal_entry.date.date()}"
