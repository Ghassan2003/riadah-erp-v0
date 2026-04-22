#!/bin/bash
# ============================================
# RIADAH ERP - Local Setup Script
# Run: chmod +x setup.sh && ./setup.sh
# ============================================

set -e

echo "============================================"
echo "  RIADAH ERP - Local Setup"
echo "============================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check Python
echo -n "Checking Python 3... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}Found $PYTHON_VERSION${NC}"
else
    echo -e "${RED}Python 3 is not installed!${NC}"
    echo "Install it from: https://www.python.org/downloads/"
    exit 1
fi

# Check Node.js
echo -n "Checking Node.js... "
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version 2>&1)
    echo -e "${GREEN}Found $NODE_VERSION${NC}"
else
    echo -e "${RED}Node.js is not installed!${NC}"
    echo "Install it from: https://nodejs.org/ (v18+)"
    exit 1
fi

echo ""
echo "============================================"
echo "  Step 1: Backend Setup"
echo "============================================"

cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created.${NC}"
else
    echo -e "${GREEN}Virtual environment already exists.${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt -q
echo -e "${GREEN}Dependencies installed.${NC}"

# Apply migrations
echo -e "${YELLOW}Applying database migrations...${NC}"
python manage.py migrate --run-syncdb 2>&1 | tail -3
echo -e "${GREEN}Migrations applied.${NC}"

# Create superuser
echo ""
echo "============================================"
echo "  Create Admin User"
echo "============================================"
echo ""

if python manage.py shell -c "
from users.models import User
if User.objects.filter(username='admin').exists():
    print('EXISTS')
else:
    User.objects.create_superuser(
        username='admin',
        email='admin@riadah.com',
        password='admin123',
        role='admin',
        full_name='مدير النظام',
        phone='+966500000000',
        is_active=True
    )
    print('CREATED')
" 2>&1 | grep -q "CREATED"; then
    echo -e "${GREEN}Admin user created successfully!${NC}"
else
    echo -e "${YELLOW}Admin user already exists.${NC}"
fi

echo ""
echo -e "${GREEN}Login credentials:${NC}"
echo "  Username: admin"
echo "  Password: admin123"
echo ""

# Seed data
echo -e "${YELLOW}Seeding demo data...${NC}"
for seed_cmd in seed_products seed_sales seed_accounts seed_hr; do
    if python manage.py help "$seed_cmd" &> /dev/null 2>&1; then
        python manage.py "$seed_cmd" 2>&1 | tail -1
    fi
done
echo -e "${GREEN}Demo data seeded.${NC}"

cd ..

echo ""
echo "============================================"
echo "  Step 2: Frontend Setup"
echo "============================================"

cd frontend

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
    npm install --silent
    echo -e "${GREEN}Dependencies installed.${NC}"
else
    echo -e "${GREEN}Node modules already exist.${NC}"
fi

cd ..

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo -e "${GREEN}To start the project:${NC}"
echo ""
echo -e "${YELLOW}Terminal 1 - Backend (from project root):${NC}"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo -e "${YELLOW}Terminal 2 - Frontend (from project root):${NC}"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo -e "${GREEN}URLs:${NC}"
echo "  Frontend:  http://localhost:5173"
echo "  Backend:   http://localhost:8000"
echo "  Admin:     http://localhost:8000/admin/"
echo "  Login:     admin / admin123"
echo ""
