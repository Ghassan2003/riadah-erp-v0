# RIADAH ERP v0 — دليل التشغيل المحلي

## المتطلبات الأساسية

| المكتبة | الإصدار المطلوب | رابط التحميل |
|---------|----------------|-------------|
| Python | 3.10+ | https://www.python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org/ |
| npm | 9+ (يأتي مع Node.js) | — |
| Git | أي إصدار | https://git-scm.com/ |

> **ملاحظة:** Redis و PostgreSQL **غير مطلوبين** للتشغيل المحلي. النظام يعمل بـ SQLite وذاكرة محلية.

---

## طريقة التشغيل السريع (سطر واحد)

### Linux / macOS:
```bash
chmod +x run_local.sh
./run_local.sh
```

### Windows:
```
run_local.bat
```

---

## طريقة التشغيل اليدوي

### 1) إعداد الباك إند (Backend)

```bash
cd backend

# إنشاء بيئة افتراضية
python3 -m venv venv

# تفعيل البيئة
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# تثبيت المتطلبات
pip install -r requirements.txt

# إعداد قاعدة البيانات
python manage.py migrate

# إنشاء مستخدم المدير
python manage.py createsuperuser
# أو استخدم الأمر التالي لإنشاء مستخدم جاهز:
python manage.py shell -c "
from users.models import User
User.objects.create_superuser(
    username='admin',
    email='admin@riadah.com',
    password='Admin@123',
    role='owner',
    phone='+966500000000',
    full_name='مدير النظام'
)
"

# تشغيل الخادم
python manage.py runserver 0.0.0.0:8000
```

### 2) إعداد الفرونت إند (Frontend)

```bash
cd frontend

# تثبيت الحزم
npm install

# تشغيل خادم التطوير
npm run dev
```

---

## العناوين بعد التشغيل

| الخدمة | العنوان |
|--------|---------|
| **الفرونت إند** | http://localhost:5173 |
| **الباك إند API** | http://127.0.0.1:8000/api/ |
| **لوحة إدارة Django** | http://127.0.0.1:8000/admin/ |
| **مستندات API** | http://127.0.0.1:8000/api/schema/ |

---

## بيانات الدخول

| الحقل | القيمة |
|-------|--------|
| اسم المستخدم | `admin` |
| كلمة المرور | `Admin@123` |

---

## إعدادات البيئة

### ملف `backend/.env`

جميع الإعدادات جاهزة للتشغيل المحلي. القيم الافتراضية:

- **قاعدة البيانات:** SQLite (لا تحتاج أي تثبيت)
- **Redis:** غير مطلوب (يستخدم ذاكرة محلية)
- **DEBUG:** مفعل (True)
- **البريد:** Console Backend (الرسائل تظهر في Terminal)

### ملف `frontend/.env`

- **API:** يتصل تلقائياً بـ http://127.0.0.1:8000
- **WebSocket:** يتصل بـ ws://127.0.0.1:8000

---

## وحدات النظام (30 وحدة)

| # | الوحدة | الوصف |
|---|--------|-------|
| 1 | users | إدارة المستخدمين والصلاحيات |
| 2 | sales | المبيعات وأوامر البيع |
| 3 | purchases | المشتريات وأوامر الشراء |
| 4 | accounting | المحاسبة والقيد المزدوج |
| 5 | hr | الموارد البشرية |
| 6 | documents | إدارة المستندات |
| 7 | projects | إدارة المشاريع |
| 8 | notifications | الإشعارات (WebSocket) |
| 9 | auditlog | سجل التدقيق |
| 10 | maintenance | الصيانة والجدولة |
| 11 | videos | مكتبة الفيديوهات |
| 12 | payroll | الرواتب والأجور |
| 13 | invoicing | الفواتير |
| 14 | pos | نقاط البيع |
| 15 | assets | إدارة الأصول |
| 16 | contracts | العقود |
| 17 | payments | المدفوعات |
| 18 | attachments | المرفقات |
| 19 | budget | الميزانيات |
| 20 | tenders | المناقصات |
| 21 | insurance | التأمين |
| 22 | importexport | الاستيراد والتصدير |
| 23 | equipmaint | صيانة المعدات |
| 24 | crm | إدارة العملاء |
| 25 | internalaudit | التدقيق الداخلي |
| 26 | analytics | التحليلات والذكاء الاصطناعي |
| 27 | chatbot | المساعد الذكي (شات بوت) |
| 28 | startup_finance | تمويل الشركات الناشئة |

---

## ميزات خاصة

### الشات بوت الذكي
- يعمل بـ WebSocket في الوقت الحقيقي
- يدعم استعلامات البيانات (مبيعات، مالية، موارد بشرية)
- يحتاج `HUGGINGFACE_API_TOKEN` في `.env` للردود الذكية
- للحصول على توكن مجاني: https://huggingface.co/settings/tokens

### التحليلات
- التنبؤ بالمبيعات (sklearn)
- اكتشاف الشذوذ في المصروفات
- تصنيف مخاطر الفواتير
- تقسيم العملاء (Clustering)
- تقييم الموردين

---

## هيكل الملفات

```
riadah-erp-v0/
├── backend/                  # Django REST Backend
│   ├── core/                 # إعدادات Django الرئيسية
│   ├── users/                # نظام المستخدمين
│   ├── sales/                # المبيعات
│   ├── purchases/            # المشتريات
│   ├── accounting/           # المحاسبة
│   ├── hr/                   # الموارد البشرية
│   ├── crm/                  # إدارة العملاء
│   ├── analytics/            # التحليلات والذكاء الاصطناعي
│   ├── chatbot/              # المساعد الذكي
│   ├── ...                   # باقي الوحدات
│   ├── .env                  # إعدادات الباك إند
│   ├── requirements.txt      # متطلبات Python
│   └── manage.py             # نقطة دخول Django
│
├── frontend/                 # React 18 Frontend
│   ├── src/
│   │   ├── pages/            # الصفحات (80+ صفحة)
│   │   ├── components/       # المكونات المشتركة
│   │   ├── api/              # اتصال API
│   │   ├── context/          # Context (Auth, Theme, i18n)
│   │   └── i18n/             # الترجمة (عربي + إنجليزي)
│   ├── .env                  # إعدادات الفرونت إند
│   ├── package.json          # متطلبات Node.js
│   └── vite.config.js        # إعدادات Vite
│
├── run_local.sh              # سكريبت التشغيل (Linux/macOS)
├── run_local.bat             # سكريبت التشغيل (Windows)
└── README_LOCAL.md           # هذا الملف
```

---

## حل المشاكل الشائعة

### خطأ "Module not found"
```bash
# تأكد من تفعيل البيئة الافتراضية
source backend/venv/bin/activate
pip install -r backend/requirements.txt
```

### خطأ في قاعدة البيانات
```bash
cd backend
python manage.py migrate
```

### الفرونت إند لا يتصل بالباك إند
- تأكد أن الباك إند يعمل على المنفذ 8000
- تأكد من ملف `frontend/.env` يحتوي على العنوان الصحيح

### خطأ في WebSocket
- WebSocket يعمل بذاكرة محلية بدون Redis
- إذا أردت Redis، ثبتها وعدّل `backend/.env`
