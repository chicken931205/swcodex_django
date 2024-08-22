from django import forms
from .models import ImportJob

class ImportJobForm(forms.ModelForm):
    DAYS_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    ]

    schedule_days = forms.MultipleChoiceField(
        choices=DAYS_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )


    class Meta:
        model = ImportJob
        fields = ['raw_data_file', 'table_name', 'column_names', 'order', 'description', 'schedule_time', 'schedule_days']
        widgets = {
            'raw_data_file': forms.TextInput(attrs={'class': 'form-control'}),
            'table_name': forms.TextInput(attrs={'class': 'form-control'}),
            'column_names': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
            'schedule_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.schedule_days:
            self.initial['schedule_days'] = self.instance.get_schedule_days()