web: gunicorn --chdir core core.wsgi --log-file -

postdeploy: bash bin/post_deploy

clock: python manage.py check_closed_erps

