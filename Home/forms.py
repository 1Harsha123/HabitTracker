from .models import Habit,HabitRecord
from django import forms

class HabitForm(forms.ModelForm):
    class Meta:
        model=Habit
        fields=['name','is_active']
        
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Habit name is required.")

        if len(name) < 5:
            raise forms.ValidationError("Habit name must be at least 5 characters long.")

        if name.isdigit():
            raise forms.ValidationError("Habit name cannot be only numbers.")
        return name
    
    def clean(self):
        cleaned_data = super().clean()
        habit = cleaned_data.get('habit')
        date = cleaned_data.get('date')

        if habit and date:
            exists = HabitRecord.objects.filter(
                habit=habit,
                date=date
            ).exclude(pk=self.instance.pk).exists()
            if exists:
                raise forms.ValidationError("Record already exists for this date.")
        return cleaned_data
    