#!/bin/env bash

python manage.py sass static/scss/style.scss static/css/style.css -t compressed
python manage.py collectstatic --noinput
python manage.py migrate
