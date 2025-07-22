#!/bin/bash
# Script to run the Django development server with local settings

export DJANGO_SETTINGS_MODULE=downhill_skateboarding_events.settings_local
export DJANGO_DEVELOPMENT=True

echo "Using local development settings..."
python manage.py runserver "$@"
