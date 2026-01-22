from django.shortcuts import render,redirect
from django.http import HttpResponse
from .forms import HabitForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import *
from django.shortcuts import get_object_or_404
from .utils import streak_count
from datetime import date,datetime
from calendar import monthrange
from django.db.models import Count
from datetime import timedelta
from calendar import monthrange, month_name
from django.db.models import Count, Q,F
import json
from .models import JournalEntry, JournalStats, JournalPrompt
from collections import defaultdict
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse

####Add habit,edit and delete funcions.....
@login_required
def tracker(request):
    today = timezone.localdate()

    if request.method == 'POST':
        form = HabitForm(request.POST, initial={'user': request.user})
        if form.is_valid():
            habit_name = form.cleaned_data['name'] 
            if Habit.objects.filter(user=request.user, name__iexact=habit_name).exists():
                messages.error(request, 'Habit Already exists!')
            else:
                habit = form.save(commit=False)
                habit.user = request.user
                habit.save()
                messages.success(request, "Record Added successfully!")
            return redirect('Habbit Tracker')  
        else:
            messages.warning(request, 'Kindly fill the form correctly!')
    else:
        form = HabitForm(initial={'user': request.user})
    user_habits = Habit.objects.filter(user=request.user)
    today_records = HabitRecord.objects.filter(
        habit__in=user_habits,
        date=today,
        status=True
    )
    done_today = set(today_records.values_list('habit_id', flat=True))
    return render(request, 'home.html', {
        'form': form,
        'user_habits': user_habits,
        'done_today': done_today, 
    })

@login_required
def tracker_edit(request,habit_id):
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    if request.method=='POST':
        form=HabitForm(request.POST,instance=habit)
        if form.is_valid():
           form.save()
           messages.success(request,'Data updated successfully!')
           return redirect('Habbit Tracker')
    else:
        form = HabitForm(instance=habit)
        messages.error(request,'kindly updated the data carefully!')
    return render(request, 'home.html', {'form': form, 'habits': Habit.objects.filter(user=request.user)})
        
@login_required
def delete_habit(request, habit_id):
    habit = Habit.objects.filter(id=habit_id, user=request.user).first()
    if habit:
        habit.delete()
        messages.success(request, f"Habit '{habit.name}' deleted successfully!")
    return redirect('Habbit Tracker') 



##dashboard functions starts from here................
@login_required
def dashboard(request):
    today = timezone.localdate()
    habit_data = []
    habits = Habit.objects.filter(user=request.user, is_active=True)
    study_habit = Habit.objects.filter(
        user=request.user,
        name__iexact="Study One Hour Daily After Office",
        is_active=True
    ).first()
    record = None
    start_time = None
    elapsed_seconds = 0
    timer_running = False
    if study_habit:
        try:
            record = HabitRecord.objects.get(
                habit=study_habit,
                habit__user=request.user,
                date=today
            )
            if record.start_time and not record.end_time:
                timer_running = True
                start_time = int(record.start_time.timestamp()) 
                elapsed_seconds = ((record.duration_seconds or 0) +int((timezone.now() - record.start_time).total_seconds()))
        except HabitRecord.DoesNotExist:
            record = None
    today_records = HabitRecord.objects.filter(
        habit__in=habits,
        date=today,
        status=True
    )
    done_today = set(today_records.values_list('habit_id', flat=True))
    total_habits = habits.count()
    done_count = len(done_today)
    not_done_count = total_habits - done_count
    for habit in habits:
        habit_data.append({
            'habit': habit,
            'streak': streak_count(habit),
            'done': habit.id in done_today
        })
    study_message = None
    if study_habit and record and record.duration_seconds:
        remaining = max(0, 3600 - record.duration_seconds)
        if remaining > 0:
            minutes_remaining = remaining // 60
            study_message = f"⏱ Only {record.duration_seconds // 60} min studied. {minutes_remaining} min more needed!"

    return render(request, 'dashboard.html', {
        'habits': habits,
        'today': today,
        'done_today': done_today,
        'total_habits': total_habits,
        'done_count': done_count,
        'not_done_count': not_done_count,
        'habit_data': habit_data,
        'record': record,
        'start_time': start_time,  
        'elapsed_seconds': elapsed_seconds,
        'timer_running': timer_running,
        'study_message': study_message,
        'study_habit': study_habit,
    })

@login_required
@require_POST
def mark_habit_done(request, habit_id):
    habit = Habit.objects.filter(id=habit_id, user=request.user).first()
    if not habit:
        return JsonResponse({'success': False, 'error': 'Habit not found'})
    today = timezone.localdate()
    record, created = HabitRecord.objects.get_or_create(
        habit=habit,
        date=today,
        defaults={'status': True}
    )
    if not created:
        record.status = True
        record.save()
    return JsonResponse({'success': True, 'habit_id': habit.id})

@login_required
def start_study_timer(request):
    habit = Habit.objects.filter(
        user=request.user,
        name__iexact="Study One Hour Daily After Office"
    ).first()
    if not habit:
        return JsonResponse({"error": "Habit not found"}, status=404)
    today = timezone.localdate()
    record, created = HabitRecord.objects.get_or_create(
        habit=habit,
        date=today
    )
    if record.start_time and not record.end_time:
        return JsonResponse({"success": False, "error": "Timer already running"})
    if record.duration_seconds and record.duration_seconds >= 3600:
        return JsonResponse({
            "success": False,
            "message": "Great job! You've already completed 1+ hour 🎉"
        })
    record.start_time = timezone.now()
    record.end_time = None
    record.save()
    return JsonResponse({
        "success": True,
        "start_time": int(record.start_time.timestamp()),
        "previous_duration": record.duration_seconds or 0
    })

 
@require_POST
@login_required
def stop_study_timer(request):
    habit = Habit.objects.filter(
        user=request.user,
        name="Study One Hour Daily After Office"
    ).first()
    if not habit:
        return JsonResponse({"error": "Habit not found"}, status=404)
    try:
        record = HabitRecord.objects.get(
            habit=habit,
            date=timezone.localdate()
        )
    except HabitRecord.DoesNotExist:
        return JsonResponse({"error": "Timer not started"}, status=400)
    if record.end_time:
        return JsonResponse({
            "success": False,
            "message": "Timer already stopped"
        })
    record.end_time = timezone.now()
    session_duration = (record.end_time - record.start_time).total_seconds()
    current_total = record.duration_seconds or 0
    record.duration_seconds = current_total + int(session_duration)
    record.status = record.duration_seconds >= 3600
    record.save()
    return JsonResponse({
        "success": True,
        "session_duration": int(session_duration),
        "total_duration": record.duration_seconds,
        "completed": record.status,
        "remaining_seconds": max(0, 3600 - record.duration_seconds)
    })
    
    
@login_required
def today_habit_done(request, habit_id):
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    if habit.name == "Study One Hour Daily After Office":
        record, created = HabitRecord.objects.get_or_create(
            habit=habit,
            date=timezone.localdate(),
            defaults={'start_time': timezone.now()}
        )
        if not record.start_time:
            record.start_time = timezone.now()
            record.save()
            messages.info(request, "⏱ Study timer started.")
            return redirect("dashboard")
        record.end_time = timezone.now()
        duration = (record.end_time - record.start_time).total_seconds()
        record.duration_seconds = int(duration)
        if duration >= 3600:
            record.status = True
            messages.success(request, "🎉 One hour completed! Great job!")
        else:
            record.status = False
            remaining = int((3600 - duration) / 60)
            messages.warning(
                request,
                f"⏱ Only {int(duration/60)} min studied. {remaining} min more needed!"
            )
        record.save()
        return redirect("dashboard")
    HabitRecord.objects.update_or_create(
        habit=habit,
        date=timezone.localdate(),
        defaults={'status': True}
    )
    messages.success(request, f"✅ '{habit.name}' marked as done!")
    return redirect("dashboard")



@login_required
def calender(request):
    habits = Habit.objects.filter(user=request.user, is_active=True)
    today = timezone.localdate()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    # Validate month range
    if month > 12:
        month = 12
        year += 1
    elif month < 1:
        month = 12
        year -= 1
    # Calculate previous and next months for navigation
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    # Get days in month
    days_in_month = monthrange(year, month)[1]
    # Get all habit records for the month
    records = HabitRecord.objects.filter(
        habit__in=habits,
        date__year=year,
        date__month=month,
        status=True
    )
    # Get dates with completed habits
    done_dates = set(records.values_list('date', flat=True))
    # Prepare calendar data
    calendar_data = []
    total_days = 0
    completed_days = 0
    # Calculate first weekday of the month (0=Monday, 6=Sunday)
    first_weekday = date(year, month, 1).weekday()
    # Add empty days for the first week
    for _ in range(first_weekday):
        calendar_data.append({
            'day': '',
            'in_current_month': False,
            'is_today': False,
            'completed': False,
            'partial': False,
            'total_habits': 0,
            'completed_count': 0,
            'completion_percentage': 0
        })
    for day in range(1, days_in_month + 1):
        current_date = date(year, month, day)
        # Count habits for this day
        day_records = records.filter(date=current_date)
        total_habits_for_day = habits.filter(created_at__date__lte=current_date,is_active=True).count()
        completed_count = day_records.count()
        is_completed = completed_count > 0
        is_partial = completed_count > 0 and completed_count < total_habits_for_day
        completion_percentage = int((completed_count / total_habits_for_day) * 100) if total_habits_for_day > 0 else 0
        calendar_data.append({
            'day': day,
            'date': current_date,
            'in_current_month': True,
            'is_today': current_date == today,
            'completed': is_completed,
            'completed_count': completed_count,
            'pending_count': total_habits_for_day - completed_count,
            'total_habits': total_habits_for_day,
            'completion_percentage': completion_percentage,
            'partial': is_partial,
            'is_sunday': current_date.weekday() == 6  
        })
        total_days += 1
        if is_completed:
            completed_days += 1
    
    completion_rate = int((completed_days / total_days) * 100) if total_days > 0 else 0
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    current_streak = 0
    check_date = today
    while True:
        if check_date in done_dates:
            current_streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    context = {
        'calendar_data': calendar_data,
        'month': month,
        'year': year,
        'month_name': month_name[month],
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'weekdays': weekdays,
        'completed_days': completed_days,
        'total_days': total_days,
        'completion_rate': completion_rate,
        'current_streak': current_streak,
        'total_completed_habits': records.count(),
        'today': today,
    }
    return render(request, 'habit_calendar.html', context)


@login_required
def habit_stats(request):
    today = timezone.localdate()
    start_date = today - timedelta(days=30)
    records = (HabitRecord.objects.filter(habit__user=request.user,status=True,date__gte=start_date)
        .values('date')
        .annotate(total=Count('id'))
        .order_by('date')
    )
    # chart data
    labels = [r['date'].strftime('%d %b') for r in records]
    data = [r['total'] for r in records]
    # Get user's habits
    habits = Habit.objects.filter(user=request.user, is_active=True)
    # Calculate total habits completed
    total_habits_completed = HabitRecord.objects.filter(habit__user=request.user,status=True,date__gte=start_date).count()
    # Calculate completion rate
    total_possible = habits.count() * 30  # 30 days
    completion_rate = round((total_habits_completed / total_possible) * 100, 1) if total_possible > 0 else 0
    # Current streak
    current_streak = 0
    check_date = today
    while True:
        day_records = HabitRecord.objects.filter(
            habit__user=request.user,
            status=True,
            date=check_date
        )
        if day_records.exists():
            current_streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    # Streak change (compared to previous 30 days)
    prev_start_date = start_date - timedelta(days=30)
    prev_end_date = start_date - timedelta(days=1)
    prev_streak_records = HabitRecord.objects.filter(
        habit__user=request.user,
        status=True,
        date__range=[prev_start_date, prev_end_date]
    ).count()
    current_streak_records = total_habits_completed
    if prev_streak_records > 0:
        streak_change = round(((current_streak_records - prev_streak_records) / prev_streak_records) * 100, 1)
    else:
        streak_change = 100 if current_streak_records > 0 else 0
    # Average completion time (simplified - you might need to adjust based on your model)
    avg_completion_time = "10:30 AM"  # Placeholder - implement based on your data
    # Consistency score (days with at least one habit completed)
    days_with_completion = HabitRecord.objects.filter(
        habit__user=request.user,
        status=True,
        date__gte=start_date
    ).values('date').distinct().count()
    consistency_score = round((days_with_completion / 30) * 100)
    # Weekly pattern data
    weekly_pattern = [0, 0, 0, 0, 0, 0, 0]  # Monday to Sunday
    weekly_records = HabitRecord.objects.filter(
        habit__user=request.user,
        status=True,
        date__gte=start_date
    )
    for record in weekly_records:
        weekday = record.date.weekday()  # Monday=0, Sunday=6
        weekly_pattern[weekday] += 1
    # Most and least productive days
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    max_index = weekly_pattern.index(max(weekly_pattern))
    min_index = weekly_pattern.index(min(weekly_pattern))
    most_productive_day = days[max_index]
    least_productive_day = days[min_index]
    # Habit performance by name
    habit_performance_data = []
    habit_names_data = []
    for habit in habits:
        habit_completed = HabitRecord.objects.filter(
            habit=habit,
            status=True,
            date__gte=start_date
        ).count()
        habit_percentage = round((habit_completed / 30) * 100) if 30 > 0 else 0
        habit_names_data.append(habit.name)
        habit_performance_data.append(habit_percentage)
    # Best streak
    best_streak = 0
    temp_streak = 0
    date_iterator = start_date
    while date_iterator <= today:
        day_records = HabitRecord.objects.filter(
            habit__user=request.user,
            status=True,
            date=date_iterator
        )
        if day_records.exists():
            temp_streak += 1
            best_streak = max(best_streak, temp_streak)
        else:
            temp_streak = 0
        
        date_iterator += timedelta(days=1)
    # Perfect days (days where all habits were completed)
    perfect_days = 0
    total_habits_count = habits.count()
    date_iterator = start_date
    while date_iterator <= today:
        day_completed = HabitRecord.objects.filter(
            habit__user=request.user,
            status=True,
            date=date_iterator
        ).count()
        if day_completed >= total_habits_count:
            perfect_days += 1
        
        date_iterator += timedelta(days=1)
    # Improvement rate
    first_half_start = start_date
    first_half_end = start_date + timedelta(days=15)
    second_half_start = first_half_end + timedelta(days=1)
    first_half_completed = HabitRecord.objects.filter(
        habit__user=request.user,
        status=True,
        date__range=[first_half_start, first_half_end]
    ).count()
    second_half_completed = HabitRecord.objects.filter(
        habit__user=request.user,
        status=True,
        date__range=[second_half_start, today]
    ).count()
    if first_half_completed > 0:
        improvement_rate = round(((second_half_completed - first_half_completed) / first_half_completed) * 100, 1)
    else:
        improvement_rate = 100 if second_half_completed > 0 else 0
    # Strongest habit (highest completion rate)
    if habit_performance_data:
        max_perf_index = habit_performance_data.index(max(habit_performance_data))
        strong_habit = habit_names_data[max_perf_index] if max_perf_index < len(habit_names_data) else "Morning Routine"
    else:
        strong_habit = "Morning Routine"
    # Best time slot (placeholder - implement based on your time data)
    best_time_slot = "8:00 - 10:00 AM"
    # Improvement area (lowest completion rate)
    if habit_performance_data:
        min_perf_index = habit_performance_data.index(min(habit_performance_data))
        improvement_area = habit_names_data[min_perf_index] if min_perf_index < len(habit_names_data) else "Evening Exercise"
    else:
        improvement_area = "Evening Exercise"
    # Next goal
    next_goal = f"Achieve {current_streak + 7} day streak"
    context = {
        'labels': labels,
        'data': data,
        'total_habits_completed': total_habits_completed,
        'completion_rate': completion_rate,
        'current_streak': current_streak,
        'streak_change': streak_change,
        'avg_completion_time': avg_completion_time,
        'consistency_score': consistency_score,
        'weekly_pattern': weekly_pattern,
        'most_productive_day': most_productive_day,
        'least_productive_day': least_productive_day,
        'habit_names': habit_names_data,
        'habit_performance': habit_performance_data,
        'best_streak': best_streak,
        'perfect_days': perfect_days,
        'improvement_rate': improvement_rate,
        'strong_habit': strong_habit,
        'best_time_slot': best_time_slot,
        'improvement_area': improvement_area,
        'next_goal': next_goal,
    }
    return render(request, 'habit_stats.html', context)


@login_required
def blog(request):
    # Get or create journal stats for the user
    stats, created = JournalStats.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Handle new journal entry submission
        entry_text = request.POST.get('entry', '').strip()
        mood = request.POST.get('mood', 'neutral')
        tags_input = request.POST.get('tags', '')
        entry_type = request.POST.get('entry_type', 'daily')
        
        if entry_text:
            # Convert tags string to list
            tags_list = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            
            # Create journal entry
            JournalEntry.objects.create(
                user=request.user,
                content=entry_text,
                mood=mood,
                tags=json.dumps(tags_list),
                entry_type=entry_type,
                date=timezone.now()
            )
            
            # Update statistics
            stats.update_stats()
            
            messages.success(request, '✨ Journal entry saved successfully!')
            return redirect('blog')
        else:
            messages.error(request, 'Please write something in your journal entry.')
    
    # Get all journal entries for the current user
    journal_entries = JournalEntry.objects.filter(user=request.user).order_by('-date')
    
    # Get today's entries
    today = timezone.now().date()
    today_entries = journal_entries.filter(date__date=today)
    
    # Get this week's entries
    week_ago = today - timedelta(days=7)
    week_entries = journal_entries.filter(date__date__gte=week_ago)
    
    # Get mood distribution for this month
    month_ago = today - timedelta(days=30)
    month_entries = journal_entries.filter(date__date__gte=month_ago)
    
    # Calculate mood percentages
    mood_counts = defaultdict(int)
    for entry in month_entries:
        mood_counts[entry.mood] += 1
    
    total_month_entries = sum(mood_counts.values())
    
    mood_percentages = {}
    for mood, count in mood_counts.items():
        if total_month_entries > 0:
            mood_percentages[mood] = round((count / total_month_entries) * 100, 1)
        else:
            mood_percentages[mood] = 0
    
    # Get mood percentages for specific moods (for the template)
    happy_percentage = mood_percentages.get('happy', 0)
    neutral_percentage = mood_percentages.get('neutral', 0)
    sad_percentage = mood_percentages.get('sad', 0)
    
    # Get random journal prompt
    try:
        journal_prompt = JournalPrompt.objects.filter(is_active=True).order_by('?').first()
    except:
        journal_prompt = None
    
    # Calculate streak days
    streak_days = stats.current_streak
    
    # Get entry count by type for the current month
    entry_types_count = {}
    for entry in month_entries:
        entry_types_count[entry.entry_type] = entry_types_count.get(entry.entry_type, 0) + 1
    
    # Prepare context data for entries
    processed_entries = []
    for entry in journal_entries[:10]:  # Show last 10 entries
        processed_entries.append({
            'id': entry.id,
            'content': entry.content,
            'mood': entry.get_mood_display(),
            'mood_icon': entry.get_mood_icon(),
            'mood_class': f"mood-{entry.mood}",
            'date': entry.date,
            'formatted_date': entry.date.strftime("%B %d, %Y"),
            'time': entry.date.strftime("%I:%M %p"),
            'word_count': entry.word_count,
            'tags': entry.get_tags_list(),
            'entry_type': entry.get_entry_type_display(),
            'entry_type_class': entry.entry_type,
        })
    # Get most used tags
    all_tags = []
    for entry in journal_entries:
        all_tags.extend(entry.get_tags_list())
    
    from collections import Counter
    tag_counts = Counter(all_tags)
    popular_tags = tag_counts.most_common(10)
    
    # Get weekly writing pattern (entries per day of week)
    weekly_pattern = {}
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for day in days:
        weekly_pattern[day] = 0
    
    for entry in journal_entries.filter(date__date__gte=today - timedelta(days=90)):
        day_name = entry.date.strftime('%A')
        weekly_pattern[day_name] = weekly_pattern.get(day_name, 0) + 1
    
    context = {
        'journal_entries': processed_entries,
        'today_entries': today_entries,
        'total_entries': stats.total_entries,
        'total_words': stats.total_words,
        'streak_days': streak_days,
        'longest_streak': stats.longest_streak,
        'happy_percentage': happy_percentage,
        'neutral_percentage': neutral_percentage,
        'sad_percentage': sad_percentage,
        'mood_distribution': mood_percentages,
        'journal_prompt': journal_prompt,
        'entry_types_count': entry_types_count,
        'popular_tags': popular_tags,
        'weekly_pattern': weekly_pattern,
        'has_today_entry': today_entries.exists(),
        'mood_choices': JournalEntry.MOOD_CHOICES,
        'entry_type_choices': JournalEntry.ENTRY_TYPES,
        'current_date': today.strftime("%A, %B %d, %Y"),
        'current_time': timezone.now().strftime("%I:%M %p"),
        'avg_words_per_entry': round(stats.total_words / stats.total_entries, 1) if stats.total_entries > 0 else 0,
        'entries_this_week': week_entries.count(),
        'entries_this_month': month_entries.count(),
    }
    return render(request, 'blog.html', context)


@login_required
def edit_journal_entry(request, entry_id):
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    if request.method == 'POST':
        entry_text = request.POST.get('entry', '').strip()
        mood = request.POST.get('mood', entry.mood)
        tags_input = request.POST.get('tags', '')
        entry_type = request.POST.get('entry_type', entry.entry_type)
        if entry_text:
            tags_list = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            entry.content = entry_text
            entry.mood = mood
            entry.tags = json.dumps(tags_list)
            entry.entry_type = entry_type
            entry.save()
            stats = JournalStats.objects.get_or_create(user=request.user)[0]
            stats.update_stats()
            messages.success(request, '📝 Journal entry updated successfully!')
            return redirect('blog')
        else:
            messages.error(request, 'Journal entry cannot be empty.')
    entry_data = {
        'id': entry.id,
        'content': entry.content,
        'mood': entry.mood,
        'tags': ', '.join(entry.get_tags_list()),
        'entry_type': entry.entry_type,
        'date': entry.date.strftime("%Y-%m-%d"),
        'time': entry.date.strftime("%H:%M"),
    }
    context = {
        'entry': entry_data,
        'mood_choices': JournalEntry.MOOD_CHOICES,
        'entry_type_choices': JournalEntry.ENTRY_TYPES,
        'is_edit': True,
    }
    return render(request, 'blog.html', context)


@login_required
def delete_journal_entry(request, entry_id):
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    if request.method == 'POST':
        entry.delete()
        stats = JournalStats.objects.get_or_create(user=request.user)[0]
        stats.update_stats()
        messages.success(request, '🗑️ Journal entry deleted successfully!')
        return redirect('blog')
    return render(request, 'blog.html', {
        'entry_to_delete': entry,
        'is_delete': True,
    })
