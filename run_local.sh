#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# RIADAH ERP v0 — سكريبت التشغيل المحلي (بدون Docker)
# Local Run Script
# ═══════════════════════════════════════════════════════════════

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# ألوان للطباعة
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       RIADAH ERP v0 - التشغيل المحلي           ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ── التحقق من Python ──────────────────────────────────────
echo -e "${YELLOW}[1/8] التحقق من المتطلبات...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}خطأ: Python 3 غير مثبت. يرجى تثبيت Python 3.10+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}  ✓ Python: $PYTHON_VERSION${NC}"

if ! command -v node &> /dev/null; then
    echo -e "${RED}خطأ: Node.js غير مثبت. يرجى تثبيت Node.js 18+${NC}"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}  ✓ Node.js: $NODE_VERSION${NC}"

if ! command -v npm &> /dev/null; then
    echo -e "${RED}خطأ: npm غير مثبت.${NC}"
    exit 1
fi

echo -e "${GREEN}  ✓ npm: $(npm --version)${NC}"
echo ""

# ── إعداد البيئة الافتراضية للباك إند ─────────────────────
echo -e "${YELLOW}[2/8] إعداد بيئة الباك إند...${NC}"

if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo -e "  إنشاء بيئة افتراضية..."
    python3 -m venv "$BACKEND_DIR/venv"
    echo -e "${GREEN}  ✓ تم إنشاء البيئة الافتراضية${NC}"
else
    echo -e "${GREEN}  ✓ البيئة الافتراضية موجودة${NC}"
fi

# تفعيل البيئة الافتراضية
source "$BACKEND_DIR/venv/bin/activate"

# تثبيت المتطلبات
echo -e "  تثبيت المتطلبات..."
pip install --upgrade pip -q
pip install -r "$BACKEND_DIR/requirements.txt" -q
echo -e "${GREEN}  ✓ تم تثبيت جميع المتطلبات${NC}"
echo ""

# ── إعداد الفرونت إند ────────────────────────────────────
echo -e "${YELLOW}[3/8] إعداد الفرونت إند...${NC}"

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "  تثبيت الحزم..."
    cd "$FRONTEND_DIR"
    npm install
    echo -e "${GREEN}  ✓ تم تثبيت جميع الحزم${NC}"
else
    echo -e "${GREEN}  ✓ الحزم مثبتة${NC}"
fi
cd "$PROJECT_DIR"
echo ""

# ── التحقق من ملف .env ───────────────────────────────────
echo -e "${YELLOW}[4/8] التحقق من إعدادات البيئة...${NC}"

if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${RED}خطأ: ملف backend/.env غير موجود!${NC}"
    echo -e "${YELLOW}  يرجى نسخ backend/.env.example إلى backend/.env${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ ملف backend/.env موجود${NC}"

if [ ! -f "$FRONTEND_DIR/.env" ]; then
    echo -e "${RED}خطأ: ملف frontend/.env غير موجود!${NC}"
    echo -e "${YELLOW}  يرجى نسخ frontend/.env.example إلى frontend/.env${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ ملف frontend/.env موجود${NC}"
echo ""

# ── إعداد قاعدة البيانات ─────────────────────────────────
echo -e "${YELLOW}[5/8] إعداد قاعدة البيانات...${NC}"

cd "$BACKEND_DIR"
python manage.py makemigrations --noinput 2>/dev/null || true
python manage.py migrate --noinput
echo -e "${GREEN}  ✓ تم تهيئة قاعدة البيانات${NC}"
echo ""

# ── إنشاء المستخدم المدير ─────────────────────────────────
echo -e "${YELLOW}[6/8] إنشاء مستخدم المدير...${NC}"

ADMIN_EXISTS=$(python manage.py shell -c "
from users.models import User
print(User.objects.filter(role='owner').exists())
" 2>/dev/null)

if [ "$ADMIN_EXISTS" = "False" ]; then
    echo -e "  إنشاء حساب المدير..."
    python manage.py shell -c "
from users.models import User
if not User.objects.filter(role='owner').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@riadah.com',
        password='Admin@123',
        role='owner',
        phone='+966500000000',
        full_name='مدير النظام'
    )
    print('تم إنشاء المدير بنجاح')
" 2>/dev/null
    echo -e "${GREEN}  ✓ تم إنشاء المدير${NC}"
    echo -e "${BLUE}  ┌──────────────────────────────────────┐${NC}"
    echo -e "${BLUE}  │  اسم المستخدم: admin                 │${NC}"
    echo -e "${BLUE}  │  كلمة المرور: Admin@123              │${NC}"
    echo -e "${BLUE}  │  العنوان: http://localhost:5173       │${NC}"
    echo -e "${BLUE}  └──────────────────────────────────────┘${NC}"
else
    echo -e "${GREEN}  ✓ المدير موجود بالفعل${NC}"
fi
cd "$PROJECT_DIR"
echo ""

# ── جمع الملفات الثابتة ───────────────────────────────────
echo -e "${YELLOW}[7/8] جمع الملفات الثابتة...${NC}"
cd "$BACKEND_DIR"
python manage.py collectstatic --noinput 2>/dev/null || true
echo -e "${GREEN}  ✓ تم جمع الملفات الثابتة${NC}"
cd "$PROJECT_DIR"
echo ""

# ── تشغيل المشروع ────────────────────────────────────────
echo -e "${YELLOW}[8/8] تشغيل المشروع...${NC}"
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          تم الإعداد بنجاح!                      ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║                                                   ║${NC}"
echo -e "${GREEN}║  Backend:  http://127.0.0.1:8000                ║${NC}"
echo -e "${GREEN}║  Frontend: http://localhost:5173                 ║${NC}"
echo -e "${GREEN}║  Admin:    http://127.0.0.1:8000/admin          ║${NC}"
echo -e "${GREEN}║                                                   ║${NC}"
echo -e "${GREEN}║  المستخدم: admin                                 ║${NC}"
echo -e "${GREEN}║  كلمة المرور: Admin@123                          ║${NC}"
echo -e "${GREEN}║                                                   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}سيتم تشغيل الباك إند والفرونت إند في النوافذ التالية...${NC}"
echo -e "${YELLOW}اضغط Ctrl+C في كل نافذة لإيقاف الخدمة${NC}"
echo ""

# تشغيل الباك إند في الخلفية
cd "$BACKEND_DIR"
source "$BACKEND_DIR/venv/bin/activate"
echo -e "${BLUE}► تشغيل Backend على المنفذ 8000...${NC}"
python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!

# تشغيل الفرونت إند في الخلفية
cd "$FRONTEND_DIR"
echo -e "${BLUE}► تشغيل Frontend على المنفذ 5173...${NC}"
npm run dev &
FRONTEND_PID=$!

# انتظار للحصول على PID الفعلي
sleep 3

echo ""
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}  المشروع يعمل الآن!                        ${NC}"
echo -e "${GREEN}  Backend PID: $BACKEND_PID                       ${NC}"
echo -e "${GREEN}  Frontend PID: $FRONTEND_PID                     ${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}لإيقاف المشروع: kill $BACKEND_PID $FRONTEND_PID${NC}"
echo -e "${YELLOW}أو اضغط Ctrl+C${NC}"
echo ""

# التعامل مع الإيقاف النظيف
trap "echo -e '\n${YELLOW}جاري إيقاف المشروع...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; wait; echo -e '${GREEN}تم الإيقاف بنجاح${NC}'; exit 0" SIGINT SIGTERM

# انتظار حتى يتم إنهاء العمليات
wait
