web: gunicorn --chdir core core.wsgi --log-file -

postdeploy: bash bin/post_deploy

clock: python manage.py start_scheduler
