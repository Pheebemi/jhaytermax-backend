#!/bin/bash

# Django Backend Deployment Script for PythonAnywhere
# Run this script in your PythonAnywhere bash console

echo "🚀 Starting Django Backend Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: manage.py not found. Please run this script from the Django project root.${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Setting up virtual environment...${NC}"
python3.10 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}Step 2: Installing dependencies...${NC}"
pip install -r requirements.txt

echo -e "${YELLOW}Step 3: Running database migrations...${NC}"
python manage.py migrate

echo -e "${YELLOW}Step 4: Collecting static files...${NC}"
python manage.py collectstatic --noinput

echo -e "${YELLOW}Step 5: Creating media directory...${NC}"
mkdir -p media

echo -e "${GREEN}✅ Deployment setup complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Create a .env file with your configuration (see env-sample.txt)"
echo "2. Configure your web app in PythonAnywhere dashboard"
echo "3. Set up SSL certificate"
echo "4. Update your frontend to use the production API URL"
echo ""
echo -e "${GREEN}Your Django backend is ready for deployment!${NC}"