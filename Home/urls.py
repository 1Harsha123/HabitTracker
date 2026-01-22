from django.contrib import admin
from django.urls import path,include
from . import views
from Home.views import *

urlpatterns = [
   path("dashboard/",views.dashboard,name="dashboard"),
   path("add/",views.tracker,name='Habbit Tracker'),
   path('edit/<int:habit_id>/', views.tracker_edit, name='tracker_edit'),
   path('delete/<int:habit_id>/', views.delete_habit, name='delete_habit'),
   path('today-habit-done/<int:habit_id>/', views.today_habit_done, name='today_habit_done'),
   path('calender', views.calender, name='calender'),
   path('habit_stats/', views.habit_stats,name='habit_stats'),
   path('blog/', views.blog, name='blog'),
   path('blog/edit/<int:entry_id>/', views.edit_journal_entry, name='edit_journal_entry'),
   path('blog/delete/<int:entry_id>/', views.delete_journal_entry, name='delete_journal_entry'),
   path('stop_study_timer/',views.stop_study_timer, name='stop_study_timer'),
   path('start_study_timer/',views.start_study_timer,name='start_study_timer'),  
   path('mark_habit_done/<int:habit_id>/', views.mark_habit_done, name='mark_habit_done'),
   

]