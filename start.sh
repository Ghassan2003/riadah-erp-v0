#!/bin/bash
# ============================================
# RIADAH ERP v0 - Local Development Start Script
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   RIADAH ERP v0 - Local Development${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Python
if [ ! -f "$VENV_PYTHON" ]; then
    echo -e "${YELLOW}[1/5] Creating Python virtual environment...${NC}"
    python3 -m venv "$SCRIPT_DIR/.venv"
    source "$SCRIPT_DIR/.venv/bin/activate"
    pip install django djangorestframework djangorestframework-simplejwt \
        django-cors-headers django-channels celery redis daphne \
        colorlog pandas numpy scikit-learn pillow 2>&1 | tail -3
else
    echo -e "${GREEN}[1/5] Python virtual environment: OK${NC}"
fi

# Install missing packages
echo -e "${YELLOW}[2/5] Checking dependencies...${NC}"
source "$SCRIPT_DIR/.venv/bin/activate"
pip install celery redis 2>/dev/null | tail -1

# Backend setup
echo -e "${YELLOW}[3/5] Backend setup...${NC}"
cd "$BACKEND_DIR"

# Run migrations
DJANGO_DEBUG=True DJANGO_SECRET_KEY=local-dev-secret-key-2024 \
    "$VENV_PYTHON" manage.py migrate 2>&1 | tail -2

# Ensure admin user exists
DJANGO_DEBUG=True DJANGO_SECRET_KEY=local-dev-secret-key-2024 \
    "$VENV_PYTHON" manage.py shell -c "
from django.contrib.auth.hashers import make_password
from users.models import User
admin, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@riadah.com',
        'is_active': True,
        'is_staff': True,
        'role': 'admin',
    }
)
if created:
    admin.password = make_password('Admin@123456')
    admin.save(update_fields=['password'])
    print('Admin user created: admin / Admin@123456')
else:
    admin.is_active = True
    admin.is_staff = True
    admin.save(update_fields=['is_active', 'is_staff'])
    print('Admin user activated: admin / Admin@123456')
" 2>&1

# Start backend
echo -e "${YELLOW}[4/5] Starting Backend on port 8000...${NC}"
DJANGO_DEBUG=True DJANGO_SECRET_KEY=local-dev-secret-key-2024 \
    "$VENV_PYTHON" manage.py runserver 127.0.0.1:8000 --noreload &
BACKEND_PID=$!
sleep 4

# Check backend
if curl -s -m 3 http://127.0.0.1:8000/api/auth/login/ > /dev/null 2>&1; then
    echo -e "${GREEN}     Backend: Running on http://127.0.0.1:8000${NC}"
else
    echo -e "${RED}     Backend: Failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null
fi

# Start frontend
echo -e "${YELLOW}[5/5] Starting Frontend on port 5173...${NC}"
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    npm install 2>&1 | tail -3
fi
npx vite --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!
sleep 4

# Check frontend
if curl -s -m 3 http://localhost:5173/ > /dev/null 2>&1; then
    echo -e "${GREEN}     Frontend: Running on http://localhost:5173${NC}"
else
    echo -e "${RED}     Frontend: Failed to start${NC}"
    kill $FRONTEND_PID 2>/dev/null
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   RIADAH ERP is running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  ${BLUE}Frontend (UI):${NC}  http://localhost:5173"
echo -e "  ${BLUE}Backend (API):${NC}   http://127.0.0.1:8000"
echo -e "  ${BLUE}Login:${NC}           admin / Admin@123456"
echo -e "  ${BLUE}Admin Panel:${NC}     http://127.0.0.1:8000/admin/"
echo ""
echo -e "  ${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

wait
