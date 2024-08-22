from django.db import models


class ImportJob(models.Model):
    raw_data_file = models.CharField(max_length=255)
    table_name = models.CharField(max_length=255)
    column_names = models.TextField(blank=True, null=True)
    order = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)  # New field
    schedule_time = models.TimeField(null=True, blank=True)
    schedule_days = models.CharField(max_length=21, blank=True)  # Store as comma-separated string

    def get_schedule_days(self):
        return self.schedule_days.split(',') if self.schedule_days else []

    def set_schedule_days(self, days):
        self.schedule_days = ','.join(days)