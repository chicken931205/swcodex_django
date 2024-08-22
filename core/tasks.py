import os
import time
import subprocess
import datetime
import shlex
from os import listdir
from os.path import isfile, join

from core.celery import app
from celery.contrib.abortable import AbortableTask
from django_celery_results.models import TaskResult

from django.conf import settings

def get_scripts():
    """
    Returns all scripts from 'ROOT_DIR/celery_scripts'
    """
    raw_scripts = []
    scripts = []
    ignored_ext = ['db', 'txt']

    try:
        raw_scripts = [f for f in listdir(settings.CELERY_SCRIPTS_DIR) if isfile(join(settings.CELERY_SCRIPTS_DIR, f))]
    except Exception as e:
        return None, 'Error CELERY_SCRIPTS_DIR: ' + str(e)

    for filename in raw_scripts:
        ext = filename.split(".")[-1]
        if ext not in ignored_ext:
            scripts.append(filename)

    return scripts, None

def write_to_log_file(logs, script_name):
    """
    Writes logs to a log file with formatted name in the CELERY_LOGS_DIR directory.
    """
    script_base_name = os.path.splitext(script_name)[0]  # Remove the .py extension
    current_time = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
    log_file_name = f"{script_base_name}-{current_time}.log"
    log_file_path = os.path.join(settings.CELERY_LOGS_DIR, log_file_name)
    
    with open(log_file_path, 'w') as log_file:
        log_file.write(logs)
    
    return log_file_path

@app.task(bind=True, base=AbortableTask)
def execute_script(self, data: dict):
    """
    This task executes scripts found in settings.CELERY_SCRIPTS_DIR and logs are later generated and stored in settings.CELERY_LOGS_DIR
    :param data dict: contains data needed for task execution. Example `input` which is the script to be executed.
    :rtype: None
    """
    script = data.get("script")
    args = data.get("args", "")
    
    print('> EXEC [' + script + '] -> (' + args + ')')

    scripts, ErrInfo = get_scripts()

    if script and script in scripts:
        # Executing related script
        script_path = os.path.join(settings.CELERY_SCRIPTS_DIR, script)
        
        # Convert args to a list if it is a string
      # Split args string into a list

        if args:
            command = [
                'python', script_path,
                '--url', 'caskdemo6.service-now.com'
            ]
        else:
            command = ['python', script_path]
        
        # Start the process
        process = subprocess.run(command, check=True, capture_output=True, text=True)
        time.sleep(8)
        
        exit_code = process.returncode
        error = False
        status = "STARTED"
        
        # Read and process the logs
        if exit_code == 0:  # If script execution is successful
            logs = process.stdout
            status = "SUCCESS"
        else:
            logs = process.stderr
            error = True
            status = "FAILURE"
        
        # Print debug information
        
        # Write logs to a file
        log_file = write_to_log_file(logs, script_path)
        
        return {"logs": logs, "input": script_path, "error": error, "output": "", "status": status, "log_file": log_file}
