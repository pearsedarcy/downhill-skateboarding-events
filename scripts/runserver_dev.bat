@echo off
REM Script to run the Django development server with local settings

set DJANGO_SETTINGS_MODULE=downhill_skateboarding_events.settings_local
set DJANGO_DEVELOPMENT=True

echo Using local development settings...
python manage.py runserver %*
