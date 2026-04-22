# نظام RIADAH ERP

نظام تخطيط موارد المؤسسة (ERP) متكامل مبني بتقنيات حديثة.

## المتطلبات التقنية

| المكون | التقنية |
|---------|---------|
| Backend | Django 4.2 + Django REST Framework + Channels |
| Frontend | React 18 + Vite 5 + TailwindCSS 3 |
| Database | SQLite (محلي) / PostgreSQL (Docker) |
| Authentication | JWT (SimpleJWT) |
| Real-time | Django Channels + WebSocket |
| Containerization | Docker + Docker Compose |

## الوحدات المتاحة (20+ وحدة)

| الوحدة | الوصف |
|--------|-------|
| `users` | المصادقة والصلاحيات (7 أدوار) |
| `inventory` | إدارة المنتجات والمخزون |
| `sales` | المبيعات وإدارة العملاء |
| `purchases` | المشتريات والموردين |
| `accounting` | المحاسبة والقوائم المالية |
| `hr` | الموارد البشرية (موظفين، حضور، إجازات) |
| `payroll` | الرواتب والسلف والقروض |
| `warehouse` | إدارة المستودعات والتحويلات |
| `projects` | إدارة المشاريع والمهام |
| `contracts` | العقود والمراحل |
| `invoicing` | الفواتير والتذاكر |
| `payments` | المدفوعات والشيكات |
| `pos` | نقطة البيع |
| `assets` | الأصول الثابتة والإهلاك |
| `notifications` | الإشعارات (WebSocket) |
| `auditlog` | سجل التدقيق |
| `maintenance` | الصيانة والنسخ الاحتياطي |
| `documents` | إدارة المستندات |
| `videos` | مكتبة الفيديوهات التعليمية |
| `attachments` | نظام المرفقات العام |

## الأدوار (7 أدوار)

| الدور | الكود | الصلاحيات |
|-------|-------|-----------|
| مدير النظام | `admin` | كل شيء |
| المبيعات | `sales` | المبيعات والعملاء |
| المحاسب | `accountant` | المحاسبة والقوائم |
| المخازن | `warehouse` | المخزون والمستودعات |
| الموارد البشرية | `hr` | الموظفين والرواتب |
| المشتريات | `purchasing` | المشتريات والموردين |
| مدير المشاريع | `project_manager` | المشاريع والمهام |

---

## التشغيل المحلي (بدون Docker)

### المتطلبات المسبقة
- **Python 3.10+** — [تحميل](https://www.python.org/downloads/)
- **Node.js 18+** — [تحميل](https://nodejs.org/)
- **pip** و **npm**

### الطريقة السريعة (سكريبت تلقائي)

```bash
git clone https://github.com/Ghassan2003/riadah-erp-v0.git
cd riadah-erp-v0
bash setup.sh
```

### الطريقة اليدوية

#### الخطوة 1: Backend

افتح **طرفية (Terminal)** وانتقل لمجلد المشروع:

```bash
cd riadah-erp-v0/backend

# إنشاء بيئة افتراضية
python -m venv venv

# تفعيل البيئة الافتراضية
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows

# تثبيت المتطلبات
pip install -r requirements.txt

# إنشاء قاعدة البيانات
python manage.py migrate

# إنشاء مستخدم المدير
python manage.py create_admin

# (اختياري) بيانات تجريبية
python manage.py seed_products
python manage.py seed_sales
python manage.py seed_accounts
python manage.py seed_hr

# تشغيل الخادم
python manage.py runserver 0.0.0.0:8000
```

#### الخطوة 2: Frontend

افتح **طرفية جديدة**:

```bash
cd riadah-erp-v0/frontend

# تثبيت المتطلبات
npm install

# تشغيل خادم التطوير
npm run dev
```

#### الخطوة 3: افتح المتصفح

| الخدمة | الرابط |
|--------|--------|
| **الواجهة الأمامية** | http://localhost:5173 |
| **Backend API** | http://localhost:8000/api/ |
| **Django Admin** | http://localhost:8000/admin/ |

### بيانات الدخول

| البند | القيمة |
|-------|--------|
| اسم المستخدم | `admin` |
| كلمة المرور | `admin123` |

---

## التشغيل عبر Docker

```bash
cd riadah-erp-v0
docker-compose up --build
```

- **الواجهة:** http://localhost:3000
- **API:** http://localhost:8000/api/

---

## هيكل المشروع

```
riadah-erp-v0/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── core/               # إعدادات Django (settings, urls, wsgi, asgi)
│   ├── users/              # المصادقة والصلاحيات
│   ├── inventory/          # المنتجات والمخزون
│   ├── sales/              # المبيعات
│   ├── purchases/          # المشتريات
│   ├── accounting/         # المحاسبة
│   ├── hr/                 # الموارد البشرية
│   ├── payroll/            # الرواتب
│   ├── warehouse/          # المستودعات
│   ├── projects/           # المشاريع
│   ├── contracts/          # العقود
│   ├── invoicing/          # الفواتير
│   ├── payments/           # المدفوعات
│   ├── pos/                # نقطة البيع
│   ├── assets/             # الأصول
│   ├── notifications/      # الإشعارات
│   ├── auditlog/           # سجل التدقيق
│   ├── maintenance/        # الصيانة
│   ├── documents/          # المستندات
│   ├── videos/             # الفيديوهات
│   └── attachments/        # المرفقات
├── frontend/
│   ├── src/
│   │   ├── pages/          # 35+ صفحة
│   │   ├── components/     # 11 مكون مشترك
│   │   ├── api/index.js    # طبقة API
│   │   ├── context/        # Auth + Theme
│   │   └── i18n/           # الترجمة عربي/إنجليزي
│   ├── tailwind.config.js
│   └── vite.config.js
├── docker-compose.yml
├── setup.sh                # سكريبت الإعداد التلقائي
├── .env.example            # متغيرات البيئة
└── README.md
```

## الترخيص

مشروع خاص - RIADAH ERP
