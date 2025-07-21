@echo off
REM Reset Development Environment Script

echo === Resetting Development Environment ===

REM Delete SQLite database if it exists
if exist db.sqlite3 (
    echo Deleting existing database...
    del /f db.sqlite3
) else (
    echo No existing database found.
)

REM Set environment variables for local development
echo Setting development environment variables...
set DJANGO_SETTINGS_MODULE=downhill_skateboarding_events.settings_local
set DJANGO_DEVELOPMENT=True

REM Run migrations to create a fresh database
echo Creating fresh database with migrations...
python manage.py migrate

echo === Development Environment Reset Complete ===
echo.
echo Next steps:
echo 1. Create a superuser: python manage.py createsuperuser
echo 2. Start the development server: python manage.py runserver
