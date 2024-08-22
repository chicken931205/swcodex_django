import os
import pandas as pd
import numpy as np
import sqlite3
import logging
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django import forms
from .forms import ImportJobForm
from .models import ImportJob
from scheduler.scheduler import update_job_schedule, get_scheduler
from apscheduler.jobstores.base import JobLookupError


# Set up logging
logger = logging.getLogger(__name__)


def import_file(request=None, job_id=None):
    if job_id:
        import_job = get_object_or_404(ImportJob, id=job_id)
    elif request and request.method == 'POST':
        form = ImportJobForm(request.POST)
        if form.is_valid():
            import_job = form.save(commit=False)
            if 'schedule_days' in form.cleaned_data:
                import_job.set_schedule_days(form.cleaned_data['schedule_days'])
            import_job.save()
            update_job_schedule(import_job)
            messages.success(request, 'Import job created and scheduled successfully.')
            return redirect('importer:import_job_list')
    elif request:
        form = ImportJobForm()
        return render(request, 'pages/importer/import_file.html', {'form': form})
    else:
        logger.error("Invalid call to import_file")
        return

    try:
        # File path
        file_path = os.path.join(settings.BASE_DIR, 'collection', import_job.raw_data_file)
        logger.info(f"File path: {file_path}")
        
        # Read the file
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
            logger.info("Reading CSV file")
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
            logger.info("Reading Excel file")
        else:
            raise ValueError("Invalid file type")

        logger.info(f"DataFrame shape: {df.shape}")
        logger.info(f"DataFrame columns: {df.columns.tolist()}")

        # Use custom column names if provided
        if import_job.column_names:
            custom_columns = [col.strip() for col in import_job.column_names.split(',')]
            if len(custom_columns) == len(df.columns):
                df.columns = custom_columns
                logger.info(f"Using custom columns: {custom_columns}")
            else:
                raise ValueError("Number of custom columns doesn't match the file")

        # Connect to the database
        db_path = os.path.join(settings.BASE_DIR, 'itam.sqlite3')
        logger.info(f"Connecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create the table
        columns = [f"[{col}] TEXT" for col in df.columns]
        create_table_sql = f"CREATE TABLE IF NOT EXISTS [{import_job.table_name}] ({', '.join(columns)})"
        logger.info(f"Creating table with SQL: {create_table_sql}")
        cursor.execute(create_table_sql)

        # Insert data
        df = df.replace({np.nan: None})
        data = [tuple(x) for x in df.to_numpy()]
        placeholders = ','.join(['?' for _ in df.columns])
        insert_sql = f"INSERT INTO [{import_job.table_name}] VALUES ({placeholders})"
        logger.info(f"Inserting data with SQL: {insert_sql}")
        logger.info(f"Number of rows to insert: {len(data)}")
        cursor.executemany(insert_sql, data)

        conn.commit()
        logger.info("Committed changes to database")
        conn.close()
        logger.info("Closed database connection")

        # Verify the data was inserted
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM [{import_job.table_name}]")
        row_count = cursor.fetchone()[0]
        logger.info(f"Rows in table after insert: {row_count}")
        conn.close()

        if request:
            messages.success(request, f"Successfully imported {len(df)} rows into {import_job.table_name}")
            return redirect('importer:import_job_list')
        else:
            logger.info(f"Executed scheduled import job {import_job.raw_data_file}")
    except Exception as e:
        if job_id:
            logger.error(f"Error during scheduled import for job {job_id}: {str(e)}", exc_info=True)
        else:
            import_job.delete()
            logger.error(f"Error during import: {str(e)}", exc_info=True)
            messages.error(request, f"Error during import: {str(e)}")
            return redirect('importer:import_file')

def import_job_list(request):
    jobs = ImportJob.objects.all()
    return render(request, 'pages/importer/import_job_list.html', {'jobs': jobs})

def edit_import_job(request, job_id):
    job = get_object_or_404(ImportJob, id=job_id)
    if request.method == 'POST':
        form = ImportJobForm(request.POST, instance=job)
        if form.is_valid():
            job = form.save(commit=False)
            if 'schedule_days' in form.cleaned_data:
                job.set_schedule_days(form.cleaned_data['schedule_days'])
            job.save()
            update_job_schedule(job)
            messages.success(request, 'Import job updated successfully.')
            return redirect('importer:import_job_list')
    else:
        form = ImportJobForm(instance=job)
    return render(request, 'pages/importer/edit_import_job.html', {'form': form, 'job': job})

def delete_import_job(request, job_id):
    job = get_object_or_404(ImportJob, id=job_id)
    
    # Delete the job from the database
    job.delete()

    # Remove the job from the scheduler
    scheduler = get_scheduler()
    if scheduler:
        try:
            scheduler.remove_job(f'import_job_{job_id}')
            print(f"Import Job {job_id} removed from scheduler")
        except JobLookupError:
            print(f"Import Job {job_id} not found in scheduler")
        
        # Print all jobs in the scheduler for debugging
        print("Current jobs in scheduler:")
        for job in scheduler.get_jobs():
            print(f"- {job.id}")
    else:
        print("Scheduler not initialized")

    messages.success(request, 'Import job deleted successfully.')
    return redirect('importer:import_job_list')