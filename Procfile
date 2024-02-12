web: gunicorn --chdir core core.wsgi --log-file -

postdeploy: bash bin/post_deploy

clock: python manage.py start_scheduler

worker: celery -A core worker -l info --max-tasks-per-child=500
