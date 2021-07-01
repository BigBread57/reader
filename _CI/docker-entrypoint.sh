#!/bin/bash

python manage.py migrate --no-input

python manage.py collectstatic --no-input

celery -A reader worker --beat -l info &
gunicorn --bind 0.0.0.0:8000 reader.wsgi:application --workers=4 &
python ws/server.py
