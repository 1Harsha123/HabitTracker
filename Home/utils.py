from .models import *
from datetime import timedelta
import datetime

# def streak_count(habit):
#     streak = 0
#     today = timezone.now().date()
#     while True:
#         date = today - timedelta(days=streak)
#         habit_present = HabitRecord.objects.filter(
#             habit=habit,
#             date=date,
#             status=True
#         ).exists()
#         if habit_present:
#             streak += 1
#         else:
#             break
#     return streak



def streak_count(habit):
    streak = 0
    today = timezone.localdate()

    # ✅ Start from today IF done, else from yesterday
    start_date = today
    if not HabitRecord.objects.filter(
        habit=habit,
        date=today,
        status=True
    ).exists():
        start_date = today - timedelta(days=1)

    current_date = start_date

    while True:
        if HabitRecord.objects.filter(
            habit=habit,
            date=current_date,
            status=True
        ).exists():
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break

    return streak


    