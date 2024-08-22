from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from django_apscheduler.jobstores import DjangoJobStore
import logging

logger = logging.getLogger(__name__)
scheduler = None

def get_scheduler():
    global scheduler
    if scheduler is None:
        initialize()
    return scheduler

def initialize():
    global scheduler
    if scheduler is None:
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")
        scheduler.start()
        logger.info("Scheduler initialized and started successfully.")

def update_job_schedule(job):
    scheduler = get_scheduler()
    if not scheduler:
        logger.error("Scheduler not initialized")
        return

    job_id = f'import_job_{job.id}'
    
    # Remove existing job if it's scheduled
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Removed existing job {job_id} from scheduler")
    except JobLookupError:
        logger.info(f"Job {job_id} not found in scheduler for removal")
    
    # If job has a schedule, add it to the scheduler
    if job.schedule_time and job.schedule_days:
        days = job.get_schedule_days()
        time = job.schedule_time
        
        # Convert days to cron-style day of week (0-6 where 0 is Monday)
        day_mapping = {'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6}
        cron_days = ','.join(str(day_mapping[day]) for day in days if day in day_mapping)
        
        if cron_days:
            scheduler.add_job(
                execute_import_job,
                'cron',
                id=job_id,
                day_of_week=cron_days,
                hour=time.hour,
                minute=time.minute,
                args=[job.id],
                replace_existing=True
            )
            
            logger.info(f"Import Job {job.raw_data_file} (ID: {job_id}) scheduled for {cron_days} at {time}")
        else:
            logger.warning(f"No valid schedule days provided for job {job.raw_data_file} (ID: {job_id})")
    else:
        logger.info(f"Import Job {job.raw_data_file} (ID: {job_id}) has no schedule")

def execute_import_job(job_id):
    from .views import import_file  # Import here to avoid circular import
    try:
        import_file(job_id=job_id)
    except Exception as e:
        logger.error(f"Error executing import job {job_id}: {str(e)}")