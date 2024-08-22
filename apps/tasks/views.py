import os
import time
import json
import re

from django.http import HttpResponse
from django.shortcuts import render, redirect

from celery import current_app
from core.tasks import execute_script, get_scripts
from django_celery_results.models import TaskResult
from celery.contrib.abortable import AbortableAsyncResult
from core.celery import app
from django.http import HttpResponse, Http404
from os import listdir
from os.path import isfile, join
from django.conf import settings

from django.template  import loader
from django_celery_beat.models import PeriodicTask, CrontabSchedule
# Create your views here.

def is_valid_url(url: str) -> bool:
    # Regular expression for validating a URL
    regex = re.compile(
        r'^(https?:\/\/)?'  # optional scheme
        r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'  # domain
        r'(:\d+)?'  # optional port
        r'(\/\S*)?$',  # optional path
        re.IGNORECASE
    )
    
    return re.match(regex, url) is not None


def index(request):
    return HttpResponse("INDEX Tasks")

# @login_required(login_url="/login/")
def tasks(request):

    scripts, ErrInfo = get_scripts()
 
    context = {
        'cfgError' : ErrInfo,
        'tasks'    : get_celery_all_tasks(),
        'scripts'  : scripts,
        'segment'  : 'tasks',
        'parent'   : 'apps',
    }

    # django_celery_results_task_result
    task_results = TaskResult.objects.all()
    context["task_results"] = task_results

    html_template = loader.get_template('pages/apps/tasks.html')
    tasks = PeriodicTask.objects.all()
    
    # Prepare the task details to return in the response
    tasks_details = []
    for task in tasks:
        task_details = {
            'id': task.id,
            'name': task.name,
            'task': task.task,
            'interval': str(task.interval) if task.interval else None,
            'crontab': str(task.crontab) if task.crontab else None,
            'solar': str(task.solar) if task.solar else None,
            'clocked': str(task.clocked) if task.clocked else None,
            'start_time': task.start_time,
            'last_run_at': task.last_run_at,
            'total_run_count': task.total_run_count,
            'date_changed': task.date_changed,
            'enabled': task.enabled,
            'description': task.description,
        }
    tasks_details.append(task_details)
    context["tasks_details"] = tasks_details
    return HttpResponse(html_template.render(context, request)) 
app.conf.timezone = 'UTC'


def add_periodic_task(task_name, script, args, schedule_type, day_of_week, time, day_of_month):
    hour, minute = map(int, time.split(':'))

    if schedule_type == 'daily':
        schedule, created = CrontabSchedule.objects.get_or_create(hour=hour, minute=minute)
    elif schedule_type == 'weekly':
        schedule, created = CrontabSchedule.objects.get_or_create(hour=hour, minute=minute, day_of_week=day_of_week)
    elif schedule_type == 'monthly':
        schedule, created = CrontabSchedule.objects.get_or_create(hour=hour, minute=minute, day_of_month=day_of_month)

    task_id = f'{task_name}_{script}_{args}_{schedule_type}_{day_of_week}_{time}'

    # Check if the task already exists
    task, created = PeriodicTask.objects.get_or_create(
        name=task_id,
        defaults={
            'crontab': schedule,
            'task': 'core.tasks.execute_script',
            'args': json.dumps([{"script": script, "args": args}]),
        }
    )
    
    if not created:
        # Update existing task
        task.crontab = schedule
        task.task = 'core.tasks.execute_script'
        task.args = json.dumps([{"script": script, "args": args}])
        task.save()
    print_scheduled_tasks()

def print_scheduled_tasks():
    print("Scheduled Tasks:")
    for task_name, task_info in app.conf.beat_schedule.items():
        print(f"Task Name: {task_name}")
        print(f"Task: {task_info['task']}")
        print(f"Schedule: {task_info['schedule']}")
        print(f"Args: {task_info['args']}")
        print()

def run_task(request, task_name):
    '''
    Runs a celery task
    :param request HttpRequest: Request
    :param task_name str: Name of task to execute
    :rtype: (HttpResponseRedirect | HttpResponsePermanentRedirect)
    '''
    _script = request.POST.get("script")
    print("request.POST.get", request.POST.get)
    _args = request.POST.get("args")
    if _args:
        check_valid_url = is_valid_url(_args)
        if  not check_valid_url:
            return redirect('tasks')
    schedule_type = request.POST.get("schedule_type")
    day_of_week = request.POST.get("day_of_week")
    day_of_month = request.POST.get("day_of_month")
    time = request.POST.get("time")
    tasks = [execute_script]
    for task in tasks:
        if task.__name__ == task_name:
            if schedule_type and day_of_week and time:
                add_periodic_task(task_name, _script, _args, schedule_type, day_of_week, time, day_of_month)
            else:
                task.delay({"script": _script, "args": _args})

    return redirect('tasks')

from django.http import JsonResponse
from django_celery_beat.models import PeriodicTask

def get_all_periodic_tasks(request):
    return app.conf.beat_schedule
    # Retrieve all periodic tasks
    tasks = PeriodicTask.objects.all()
    
    # Prepare the task details to return in the response
    tasks_details = []
    for task in tasks:
        task_details = {
            'id': task.id,
            'name': task.name,
            'task': task.task,
            'interval': str(task.interval) if task.interval else None,
            'crontab': str(task.crontab) if task.crontab else None,
            'solar': str(task.solar) if task.solar else None,
            'clocked': str(task.clocked) if task.clocked else None,
            'start_time': task.start_time,
            'last_run_at': task.last_run_at,
            'total_run_count': task.total_run_count,
            'date_changed': task.date_changed,
            'enabled': task.enabled,
            'description': task.description,
        }
        tasks_details.append(task_details)

    # Return the task details as a JSON response
    return JsonResponse(tasks_details, safe=False)

def cancel_task(request, task_id):
    '''
    Cancels a celery task using its task id
    :param request HttpRequest: Request
    :param task_id str: task_id of result to cancel execution
    :rtype: (HttpResponseRedirect | HttpResponsePermanentRedirect)
    '''
    result = TaskResult.objects.get(task_id=task_id)
    abortable_result = AbortableAsyncResult(
        result.task_id, task_name=result.task_name, app=app)
    if not abortable_result.is_aborted():
        abortable_result.revoke(terminate=True)
    time.sleep(1)
    return redirect("tasks")

def get_celery_all_tasks():
    current_app.loader.import_default_modules()
    tasks = list(sorted(name for name in current_app.tasks
                        if not name.startswith('celery.')))
    tasks = [{"name": name.split(".")[-1], "script":name} for name in tasks]
    for task in tasks:
        last_task = TaskResult.objects.filter(
            task_name=task["script"]).order_by("date_created").last()
        if last_task:
            task["id"] = last_task.task_id
            task["has_result"] = True
            task["status"] = last_task.status
            task["successfull"] = last_task.status == "SUCCESS" or last_task.status == "STARTED"
            task["date_created"] = last_task.date_created
            task["date_done"] = last_task.date_done
            task["result"] = last_task.result

            try:
                task["input"] = json.loads(last_task.result).get("input")
            except:
                task["input"] = ''
                
    return tasks

def task_output(request):
    '''
    Returns a task output 
    '''

    task_id = request.GET.get('task_id')
    task    = TaskResult.objects.get(id=task_id)

    if not task:
        return ''

    # task.result -> JSON Format
    return HttpResponse( task.result )

def task_log(request):
    '''
    Returns a task LOG file (if located on disk) 
    '''

    task_id  = request.GET.get('task_id')
    task     = TaskResult.objects.get(id=task_id)
    task_log = 'NOT FOUND'

    if not task: 
        return ''

    try: 
        # Get logs file
        all_logs = [f for f in listdir(settings.CELERY_LOGS_DIR) if isfile(join(settings.CELERY_LOGS_DIR, f))]
        
        for log in all_logs:

            # Task HASH name is saved in the log name
            if task.task_id in log:
                
                with open( os.path.join( settings.CELERY_LOGS_DIR, log) ) as f:
                    
                    # task_log -> JSON Format
                    task_log = f.readlines() 

                break    
    
    except Exception as e:
        task_log = json.dumps( { 'Error CELERY_LOGS_DIR: ' : str( e) } )

    return HttpResponse(task_log)

def download_log_file(request, file_path):
    path = file_path.replace('%slash%', '/')
    if os.path.exists(path):
        with open(path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(path)
            return response
    raise Http404