web: gunicorn --chdir core core.wsgi --log-file -

postdeploy: bash bin/post_deploy

worker: celery -A core worker -l info --max-tasks-per-child=500
