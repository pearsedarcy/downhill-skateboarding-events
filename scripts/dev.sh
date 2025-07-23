#!/bin/bash
# Start Django development server with local settings

# Define colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Starting Django Development Server ===${NC}"
echo -e "${YELLOW}Using local development settings${NC}"

# Set environment variables
export DJANGO_SETTINGS_MODULE=downhill_skateboarding_events.settings_local
export DJANGO_DEVELOPMENT=True

# Run migrations if needed
echo -e "${CYAN}Checking for pending migrations...${NC}"
python manage.py migrate

# Start server
echo -e "${CYAN}Starting development server...${NC}"
python manage.py runserver "$@"
