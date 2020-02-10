#!/bin/env bash

python manage.py migrate
python manage.py loaddata activites labels equipement_malentendants erp erp_lyon
