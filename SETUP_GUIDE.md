# ═══════════════════════════════════════════════════════════════════
# RIADAH ERP v0 — دليل التشغيل المحلي الشامل
# Comprehensive Local Setup Guide (No Docker)
# ═══════════════════════════════════════════════════════════════════

---

## المحتويات / Table of Contents

1. [نظرة عامة على المشروع](#1--نظرة-عامة-على-المشروع)
2. [المتطلبات الأساسية](#2--المتطلبات-الأساسية)
3. [إعداد الباك إند (Django)](#3--إعداد-الباك-إند-django)
4. [إعداد الفرونت إند (React)](#4--إعداد-الفرونت-إند-react)
5. [زرع البيانات التجريبية (Data Seeding)](#5--زرع-البيانات-التجريبية-data-seeding)
6. [تدريب النماذج الذكية (ML Model Training)](#6--تدريب-النماذج-الذكية-ml-model-training)
7. [إعداد الشات بوت الذكي](#7--إعداد-الشات-بوت-الذكي)
8. [تشغيل المشروع](#8--تشغيل-المشروع)
9. [بيانات الدخول](#9--بيانات-الدخول)
10. [هيكل المشروع](#10--هيكل-المشروع)
11. [حل المشاكل الشائعة](#11--حل-المشاكل-الشائعة)

---

## 1. نظرة عامة على المشروع

| العنصر | التفاصيل |
|--------|----------|
| **اسم المشروع** | ريادة ERP v0 |
| **النوع** | نظام تخطيط موارد المؤسسات (ERP) |
| **اللغة** | عربي (RTL) + إنجليزي |
| **الباك إند** | Django 4.2 + Django REST Framework |
| **الفرونت إند** | React 18 + Vite 5 + TailwindCSS |
| **قاعدة البيانات** | SQLite (تطوير) / PostgreSQL (إنتاج) |
| **الذكاء الاصطناعي** | scikit-learn + statsmodels + HuggingFace API |
| **عدد الوحدات** | 26 وحدة Django |

### الوحدات المتاحة:

| # | الوحدة | الوصف |
|---|--------|-------|
| 1 | users | إدارة المستخدمين والصلاحيات والأدوار |
| 2 | sales | المبيعات وأوامر البيع والعملاء |
| 3 | purchases | المشتريات وأوامر الشراء والموردين |
| 4 | accounting | المحاسبة والقيد المزدوج والدليل المحاسبي |
| 5 | hr | الموارد البشرية (موظفين، حضور، إجازات، رواتب) |
| 6 | crm | إدارة العلاقات (عملاء محتملين، فرص، تذاكر) |
| 7 | analytics | التحليلات الذكية (تنبؤات، شذوذ، تقسيم) |
| 8 | chatbot | المساعد الذكي (شات بوت مع RAG) |
| 9 | documents | إدارة المستندات |
| 10 | projects | إدارة المشاريع والمخاطر |
| 11 | notifications | الإشعارات (WebSocket) |
| 12 | auditlog | سجل التدقيق |
| 13 | maintenance | الصيانة والجدولة |
| 14 | videos | مكتبة الفيديوهات التعليمية |
| 15 | payroll | الرواتب والأجور |
| 16 | invoicing | الفواتير والمدفوعات |
| 17 | pos | نقاط البيع |
| 18 | payments | المدفوعات والتحويلات |
| 19 | attachments | المرفقات |
| 20 | tenders | المناقصات والعطاءات |
| 21 | importexport | الاستيراد والتصدير |
| 22 | equipmaint | صيانة المعدات |
| 23 | startup_finance | تمويل الشركات الناشئة |

---

## 2. المتطلبات الأساسية

### البرمجيات المطلوبة:

| البرنامج | الإصدار المطلوب | رابط التحميل |
|----------|----------------|-------------|
| **Python** | 3.10 أو أحدث | https://www.python.org/downloads/ |
| **Node.js** | 18 أو أحدث | https://nodejs.org/ |
| **npm** | 9+ (يأتي مع Node.js) | — |
| **Git** | أي إصدار | https://git-scm.com/ |

### ملاحظات مهمة:

> - **لا يحتاج Redis** للتشغيل المحلي. النظام يستخدم ذاكرة محلية (InMemory).
> - **لا يحتاج PostgreSQL** للتشغيل المحلي. النظام يستخدم SQLite.
> - **لا يحتاج Docker** للتشغيل المحلي.
> - بالنسبة للشات بوت الذكي يحتاج فقط مفتاح HuggingFace API مجاني.

---

## 3. إعداد الباك إند (Django)

### الخطوة 1: فك الضغط والانتقال للمجلد

```bash
# فك ضغط المشروع
unzip riadah-erp-v0.zip
cd riadah-erp-v0/backend
```

### الخطوة 2: إنشاء بيئة افتراضية (Virtual Environment)

```bash
# Linux / macOS:
python3 -m venv venv
source venv/bin/activate

# Windows:
python -m venv venv
venv\Scripts\activate
```

### الخطوة 3: تثبيت المتطلبات (Requirements)

```bash
pip install -r requirements.txt
```

المكتبات التي سيتم تثبيتها:
- Django 4.2 + djangorestframework + simplejwt
- pandas + numpy + scikit-learn + statsmodels (للتحليلات)
- celery + redis (اختياري)
- channels + daphne (WebSocket)
- reportlab + openpyxl (التقارير)
- requests (API calls)

### الخطوة 4: إعداد ملف البيئة (.env)

ملف `.env` موجود مسبقاً في المجلد `backend/` مع الإعدادات المناسبة للتشغيل المحلي.
لا حاجة لتعديله إلا إذا أردت تغيير الإعدادات.

الإعدادات الافتراضية:
- **قاعدة البيانات:** SQLite (تُنشأ تلقائياً)
- **Redis:** غير مطلوب (يستخدم ذاكرة محلية)
- **DEBUG:** مفعل (True)
- **البريد:** Console Backend (الرسائل تظهر في Terminal)

### الخطوة 5: إنشاء قاعدة البيانات وتطبيق Migration

```bash
python manage.py migrate
```

هذا الأمر سيُنشئ ملف `db.sqlite3` وجميع الجداول تلقائياً.

### الخطوة 6: إنشاء مستخدم المدير (Superuser)

#### الطريقة السريعة (موصى بها):

```bash
python manage.py create_admin
```

أو عبر Django Shell:

```bash
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
```

#### الطريقة اليدوية:

```bash
python manage.py createsuperuser
```
ثم اتبع التعليمات (اسم المستخدم، البريد، كلمة المرور).

---

## 4. إعداد الفرونت إند (React)

### الخطوة 1: الانتقال لمجلد الفرونت إند

```bash
cd ../frontend
```

### الخطوة 2: تثبيت الحزم

```bash
npm install
```

### الخطوة 3: التحقق من التشغيل

```bash
npm run dev
```

الفرونت إند سيعمل على: http://localhost:5173

---

## 5. زرع البيانات التجريبية (Data Seeding)

زرع البيانات التجريبية مهم جداً لاختبار جميع وحدات النظام والتحليلات الذكية.
يوجد نوعان من زرع البيانات:

### 5.1 زرع البيانات الأساسية (لكل وحدة على حدة)

كل وحدة Django تحتوي على أمر seed خاص بها. يمكنك زرع بيانات أي وحدة:

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate

# زرع بيانات المحاسبة (الدليل المحاسبي)
python manage.py seed_accounts

# زرع بيانات الموارد البشرية
python manage.py seed_hr

# زرع بيانات المبيعات
python manage.py seed_sales

# زرع بيانات المشتريات
python manage.py seed_purchases

# زرع بيانات الرواتب
python manage.py seed_payroll

# زرع بيانات الفواتير
python manage.py seed_invoicing

# زرع بيانات نقاط البيع
python manage.py seed_pos

# زرع بيانات المشاريع
python manage.py seed_projects

# زرع بيانات CRM
python manage.py seed_crm

# زرع بيانات المناقصات
python manage.py seed_tenders

# زرع بيانات المستندات
python manage.py seed_documents

# زرع بيانات الصيانة
python manage.py seed_maintenance

# زرع بيانات المعدات
python manage.py seed_equipmaint

# زرع بيانات المدفوعات
python manage.py seed_payments

# زرع بيانات المرفقات
python manage.py seed_attachments

# زرع بيانات الاستيراد والتصدير
python manage.py seed_importexport

# زرع بيانات الفيديوهات
python manage.py seed_videos

# زرع بيانات الإشعارات
python manage.py seed_notifications

# زرع بيانات سجل التدقيق
python manage.py seed_auditlog

# زرع بيانات تمويل الشركات الناشئة
python manage.py seed_startup_finance
```

### 5.2 زرع بيانات التحليلات الذكية (الأهم)

هذا الأمر يُنشئ **12 شهراً** من البيانات الواقعية التي تستخدمها نماذج الذكاء الاصطناعي:

```bash
python manage.py generate_ml_seed_data
```

**ما يُنشئه هذا الأمر:**

| البيانات | العدد التقريبي | الوصف |
|----------|---------------|-------|
| الأقسام | 5 | الإدارة العليا، المبيعات، المحاسبة، الموارد البشرية، المخازن |
| الموظفين | 30 | مع رواتب وحضور وبدلات |
| المنتجات | 100 | إلكترونيات + أثاث + قرطاسية + مواد خام + خدمات |
| العملاء | 50 | مقسمين: VIP + عادي + عرضي + جديد + مهدد |
| الموردين | 20 | ببيانات واقعية |
| أوامر البيع | 500+ | مع أنماط موسمية (رمضان، الصيف، نهاية السنة) |
| بنود أوامر البيع | 1500+ | كل أمر يحتوي 1-6 منتجات |
| الفواتير | 300+ | مع ضريبة القيمة المضافة 15% |
| المدفوعات | 200+ | بأنماط مختلفة (في الوقت، متأخر، جزئي) |
| القيود المحاسبية | 500+ | مع القيد المزدوج الكامل |
| أوامر الشراء | 100+ | مع بنود طلبات |
| سجلات الحضور | 3000+ | يومي لكل موظف |
| سجلات الرواتب | 360 | 12 شهر x 30 موظف |
| بيانات CRM | متعددة | حملات، فرص، تذاكر دعم |
| حالات شذوذ | 15+ | مصروفات غير طبيعية عمداً (لاختبار كشف الشذوذ) |

**خيارات إضافية:**

```bash
# زرع مع حذف البيانات السابقة أولاً
python manage.py generate_ml_seed_data --clear
```

### 5.3 ترتيب زرع البيانات الموصى به

للحصول على أفضل تجربة، اتبع هذا الترتيب:

```bash
# 1) زرع البيانات الأساسية لكل وحدة
python manage.py seed_accounts
python manage.py seed_hr
python manage.py seed_sales
python manage.py seed_purchases
python manage.py seed_payroll
python manage.py seed_invoicing
python manage.py seed_pos
python manage.py seed_projects
python manage.py seed_crm
python manage.py seed_tenders
python manage.py seed_documents
python manage.py seed_maintenance
python manage.py seed_payments

# 2) زرع بيانات التحليلات الذكية (يشمل بيانات المبيعات والمحاسبة والـ CRM)
python manage.py generate_ml_seed_data --clear

# 3) إنشاء المستخدم المدير
python manage.py create_admin
```

---

## 6. تدريب النماذج الذكية (ML Model Training)

نظام ريادة ERP يتضمن عدة نماذج ذكاء اصطناعي مدمجة. هذه النماذج **لا تحتاج تدريب خارجي** —
فهي تعمل مباشرة باستخدام البيانات المزرعة في قاعدة البيانات.

### 6.1 تصنيف نوايا المستخدم (Intent Classifier) — الشات بوت

**الموقع:** `chatbot/intent_classifier.py`

**التقنية:** TF-IDF + Cosine Similarity (scikit-learn)

**كيف يعمل:**
- يستخدم TF-IDF Vectorization على مستوى الحروف العربية
- N-gram: (2, 5) للتعامل مع الكلمات العربية المقطوعة
- 11 نية مدربة: تحية، وداع، استعلام مبيعات، موارد بشرية، مالية، مشتريات، CRM، مشاريع، نقاط بيع، رواتب، سؤال عام
- **تدريب تلقائي** عند أول استخدام (lazy fitting)

**لا يحتاج أي إعداد إضافي** — النموذج يُدرّب نفسه تلقائياً عند أول رسالة من المستخدم.

### 6.2 محرك الاستعلامات الذكية (Smart Query Engine)

**الموقع:** `chatbot/smart_query_engine.py`

**التقنية:** Natural Language to SQL (قواعد محددة مسبقاً)

**كيف يعمل:**
- يستقبل النص الطبيعي من المستخدم بالعربي
- يُصنفه حسب النية (باستخدام Intent Classifier)
- يُرجع استعلام SQL محدد مسبقاً حسب المجال
- يدعم 8 مجالات: مبيعات، موارد بشرية، مالية، مشتريات، CRM، مشاريع، نقاط بيع، رواتب

**لا يحتاج أي إعداد إضافي** — يعمل مباشرة مع البيانات الموجودة.

### 6.3 التنبؤ بالمبيعات (Sales Forecasting)

**الموقع:** `analytics/services/forecasting/sales_forecast.py`

**التقنية:** Holt-Winters Exponential Smoothing (statsmodels)

**كيف يعمل:**
- يحلل بيانات المبيعات الشهرية
- يبني نموذج Holt-Winters مع trend + seasonality
- يتنبأ بـ 6 أشهر قادمة
- يُحسب فترات الثقة (confidence intervals)
- Fallback: Simple Average Growth إذا البيانات أقل من 4 أشهر

**التشغيل اليدوي:**

```bash
cd backend
source venv/bin/activate

python manage.py shell -c "
from analytics.services.forecasting.sales_forecast import run_sales_forecast
result = run_sales_forecast(months_ahead=6)
print('النتيجة:', result)
"
```

### 6.4 التنبؤ بالطلب (Demand Forecasting)

**الموقع:** `analytics/services/forecasting/demand_forecast.py`

**التقنية:** Holt-Winters Exponential Smoothing

**التشغيل اليدوي:**

```bash
python manage.py shell -c "
from analytics.services.forecasting.demand_forecast import run_demand_forecast
result = run_demand_forecast()
print('النتيجة:', result)
"
```

### 6.5 التنبؤ بالتدفق النقدي (Cashflow Forecast)

**الموقع:** `analytics/services/forecasting/cashflow_forecast.py`

**التشغيل اليدوي:**

```bash
python manage.py shell -c "
from analytics.services.forecasting.cashflow_forecast import run_cashflow_forecast
result = run_cashflow_forecast()
print('النتيجة:', result)
"
```

### 6.6 تقسيم العملاء (Customer Segmentation)

**الموقع:** `analytics/services/clustering/customer_segmentation.py`

**التقنية:** RFM Analysis (Recency, Frequency, Monetary)

**كيف يعمل:**
- Recency: كم مضى منذ آخر عملية شراء
- Frequency: عدد عمليات الشراء
- Monetary: إجمالي الإنفاق
- التقسيم: VIP / Loyal / Regular / At Risk / Lost

**التشغيل اليدوي:**

```bash
python manage.py shell -c "
from analytics.services.clustering.customer_segmentation import run_customer_segmentation
result = run_customer_segmentation()
print('النتيجة:', result)
"
```

### 6.7 تقييم الموردين (Supplier Evaluation)

**الموقع:** `analytics/services/clustering/supplier_evaluation.py`

**التقنية:** Clustering (scikit-learn)

**التشغيل اليدوي:**

```bash
python manage.py shell -c "
from analytics.services.clustering.supplier_evaluation import run_supplier_evaluation
result = run_supplier_evaluation()
print('النتيجة:', result)
"
```

### 6.8 كشف الشذوذ في المبيعات (Sales Anomaly Detection)

**الموقع:** `analytics/services/anomaly/sales_anomaly.py`

**التقنية:** Z-Score + IQR (scikit-learn)

**التشغيل اليدوي:**

```bash
python manage.py shell -c "
from analytics.services.anomaly.sales_anomaly import run_sales_anomaly
result = run_sales_anomaly()
print('النتيجة:', result)
"
```

### 6.9 كشف الشذوذ في المصروفات (Expense Anomaly Detection)

**الموقع:** `analytics/services/anomaly/expense_anomaly.py`

**التشغيل اليدوي:**

```bash
python manage.py shell -c "
from analytics.services.anomaly.expense_anomaly import run_expense_anomaly
result = run_expense_anomaly()
print('النتيجة:', result)
"
```

### 6.10 تصنيف مخاطر الفواتير (Invoice Risk Classification)

**الموقع:** `analytics/services/classification/invoice_risk.py`

**التقنية:** Rule-based classification

### 6.11 تشغيل جميع النماذج دفعة واحدة

لتشغيل جميع نماذج التحليلات دفعة واحدة:

```bash
python manage.py shell << 'EOF'
from analytics.services.forecasting.sales_forecast import run_sales_forecast
from analytics.services.forecasting.demand_forecast import run_demand_forecast
from analytics.services.forecasting.cashflow_forecast import run_cashflow_forecast
from analytics.services.clustering.customer_segmentation import run_customer_segmentation
from analytics.services.clustering.supplier_evaluation import run_supplier_evaluation
from analytics.services.anomaly.sales_anomaly import run_sales_anomaly
from analytics.services.anomaly.expense_anomaly import run_expense_anomaly

print("=" * 60)
print("تشغيل جميع نماذج التحليلات الذكية...")
print("=" * 60)

models = [
    ("التنبؤ بالمبيعات", run_sales_forecast),
    ("التنبؤ بالطلب", run_demand_forecast),
    ("التدفق النقدي", run_cashflow_forecast),
    ("تقسيم العملاء", run_customer_segmentation),
    ("تقييم الموردين", run_supplier_evaluation),
    ("شذوذ المبيعات", run_sales_anomaly),
    ("شذوذ المصروفات", run_expense_anomaly),
]

for name, func in models:
    try:
        result = func()
        print(f"[OK] {name}: {result}")
    except Exception as e:
        print(f"[ERR] {name}: {e}")

print("=" * 60)
print("تم تشغيل جميع النماذج!")
print("=" * 60)
EOF
```

### 6.12 ملاحظات عن النماذج

| النموذج | يحتاج بيانات مسبقة؟ | مدة التدريب | تلقائي؟ |
|---------|---------------------|------------|---------|
| Intent Classifier | لا (بيانات داخلية) | < 1 ثانية | نعم (lazy) |
| Smart Query Engine | نعم (sales, hr, ...) | فوري | نعم |
| Sales Forecast | نعم (3+ أشهر مبيعات) | < 5 ثواني | عبر Celery |
| Demand Forecast | نعم (3+ أشهر) | < 5 ثواني | عبر Celery |
| Cashflow Forecast | نعم (3+ أشهر) | < 5 ثواني | عبر Celery |
| Customer Segmentation | نعم (عملاء + مبيعات) | < 10 ثواني | عبر Celery |
| Supplier Evaluation | نعم (موردين + مشتريات) | < 10 ثواني | عبر Celery |
| Sales Anomaly | نعم (مبيعات) | < 5 ثواني | عبر Celery |
| Expense Anomaly | نعم (مصروفات) | < 5 ثواني | عبر Celery |

---

## 7. إعداد الشات بوت الذكي

الشات بوت يعمل بثلاث مكونات:

### المكون 1: تصنيف النوايا (يعمل تلقائياً)
- TF-IDF Intent Classifier — لا يحتاج إعداد

### المكون 2: محرك الاستعلامات (يعمل تلقائياً)
- Natural Language to SQL — يحتاج بيانات مزرعة

### المكون 3: الردود الذكية (يحتاج HuggingFace API Token)

لتفعيل الردود الذكية بالذكاء الاصطناعي:

1. **الحصول على توكن مجاني:**
   - اذهب إلى: https://huggingface.co/settings/tokens
   - أنشئ حساب مجاني
   - أنشئ توكن جديد (Access Token)
   - انسخ التوكن

2. **إضافة التوكن لملف .env:**
   ```bash
   # في ملف backend/.env
   HUGGINGFACE_API_TOKEN=hf_XXXXXXXXXXXXXXXXXXXXXXXXXX
   ```

3. **بدون التوكن:** الشات بوت سيعمل ولكن الردود الذكية ستكون:
   > "عذراً، خدمة الذكاء الاصطناعي غير متاحة حالياً. يمكنك الاستعلام عن بيانات النظام (المبيعات، الموارد البشرية، المحاسبة...)."

### اختبار الشات بوت

بعد زرع البيانات وتشغيل الخادم:

1. افتح http://localhost:5173
2. سجّل الدخول ببيانات المدير
3. اضغط على أيقونة الشات بوت في الزاوية
4. جرّب هذه الاستعلامات:
   - "كم المبيعات اليوم؟"
   - "كم عدد الموظفين؟"
   - "ما هي الأرباح؟"
   - "أفضل المنتجات مبيعاً؟"
   - "تقرير الموردین"

---

## 8. تشغيل المشروع

### التشغيل السريع (طرفيتين)

#### الطرفية 1 — الباك إند:

```bash
cd backend
source venv/bin/activate        # Windows: venv\Scripts\activate
python manage.py runserver 0.0.0.0:8000
```

#### الطرفية 2 — الفرونت إند:

```bash
cd frontend
npm run dev
```

### التشغيل بالسكريبت الجاهز

#### Linux / macOS:
```bash
chmod +x run_local.sh
./run_local.sh
```

#### Windows:
```
run_local.bat
```

### العناوين بعد التشغيل:

| الخدمة | العنوان |
|--------|---------|
| **الفرونت إند** | http://localhost:5173 |
| **الباك إند API** | http://127.0.0.1:8000/api/ |
| **لوحة إدارة Django** | http://127.0.0.1:8000/admin/ |
| **مستندات API** | http://127.0.0.1:8000/api/schema/ |

---

## 9. بيانات الدخول

| الحقل | القيمة |
|-------|--------|
| اسم المستخدم | `admin` |
| كلمة المرور | `Admin@123` |
| البريد | `admin@riadah.com` |
| الدور | `owner` (مالك النظام) |

---

## 10. هيكل المشروع

```
riadah-erp-v0/
├── backend/                          # Django REST Backend
│   ├── core/                         # إعدادات Django الرئيسية
│   │   ├── settings.py               # إعدادات النظام
│   │   ├── urls.py                   # مسارات API الرئيسية
│   │   ├── wsgi.py                   # WSGI entry point
│   │   ├── asgi.py                   # ASGI entry point (WebSocket)
│   │   └── validators.py             # قواعد التحقق
│   ├── users/                        # نظام المستخدمين
│   │   ├── models.py                 # User model مخصص
│   │   ├── views.py                  # تسجيل، دخول، 2FA
│   │   ├── serializers.py            # JWT tokens
│   │   └── permissions.py            # صلاحيات مخصصة
│   ├── sales/                        # المبيعات
│   ├── purchases/                    # المشتريات
│   ├── accounting/                   # المحاسبة (قيد مزدوج)
│   ├── hr/                           # الموارد البشرية
│   ├── crm/                          # إدارة العلاقات
│   ├── analytics/                    # التحليلات الذكية
│   │   ├── services/
│   │   │   ├── forecasting/          # التنبؤات (Holt-Winters)
│   │   │   │   ├── sales_forecast.py
│   │   │   │   ├── demand_forecast.py
│   │   │   │   └── cashflow_forecast.py
│   │   │   ├── clustering/           # التقسيم (RFM)
│   │   │   │   ├── customer_segmentation.py
│   │   │   │   └── supplier_evaluation.py
│   │   │   ├── anomaly/              # كشف الشذوذ
│   │   │   │   ├── sales_anomaly.py
│   │   │   │   └── expense_anomaly.py
│   │   │   └── classification/       # التصنيف
│   │   │       └── invoice_risk.py
│   │   ├── management/commands/
│   │   │   └── generate_ml_seed_data.py  # زرع بيانات ML
│   │   └── tasks.py                  # مهام Celery
│   ├── chatbot/                      # المساعد الذكي
│   │   ├── intent_classifier.py      # تصنيف النوايا (TF-IDF)
│   │   ├── smart_query_engine.py     # محرك الاستعلامات (NL-to-SQL)
│   │   ├── ai_service.py             # خدمة AI (HuggingFace)
│   │   ├── chat_service.py           # خدمة الشات
│   │   ├── consumers.py              # WebSocket consumers
│   │   └── views.py                  # API endpoints
│   ├── ...                           # باقي الوحدات (26 وحدة)
│   ├── .env                          # إعدادات الباك إند
│   ├── requirements.txt              # متطلبات Python
│   └── manage.py                     # نقطة دخول Django
│
├── frontend/                         # React 18 Frontend
│   ├── src/
│   │   ├── pages/                    # الصفحات (80+ صفحة)
│   │   │   ├── DashboardPage.jsx     # لوحة التحكم الرئيسية
│   │   │   ├── AnalyticsPage.jsx     # صفحة التحليلات
│   │   │   ├── ChatbotPage.jsx       # صفحة الشات بوت
│   │   │   ├── SalesDashboard.jsx    # لوحة المبيعات
│   │   │   ├── HRDashboard.jsx       # لوحة الموارد البشرية
│   │   │   └── ...                   # باقي الصفحات
│   │   ├── components/               # المكونات المشتركة
│   │   │   ├── ChatWidget.jsx        # ويدجت الشات
│   │   │   ├── DataTable.jsx         # جدول البيانات
│   │   │   └── ...
│   │   ├── api/index.js              # اتصال API
│   │   ├── context/                  # Context (Auth, Theme, i18n)
│   │   └── i18n/                     # الترجمة (عربي + إنجليزي)
│   ├── .env                          # إعدادات الفرونت إند
│   ├── package.json                  # متطلبات Node.js
│   └── vite.config.js                # إعدادات Vite
│
├── run_local.sh                      # سكريبت التشغيل (Linux/macOS)
├── run_local.bat                     # سكريبت التشغيل (Windows)
├── SETUP_GUIDE.md                    # هذا الدليل
└── README.md                         # وصف المشروع
```

---

## 11. حل المشاكل الشائعة

### خطأ "Module not found"

```bash
# تأكد من تفعيل البيئة الافتراضية
source backend/venv/bin/activate   # Linux/macOS
# أو
backend\venv\Scripts\activate      # Windows

# أعد تثبيت المتطلبات
pip install -r backend/requirements.txt
```

### خطأ في قاعدة البيانات

```bash
cd backend
# حذف قاعدة البيانات القديمة وإعادة بنائها
rm db.sqlite3
python manage.py migrate

# إعادة زرع البيانات
python manage.py generate_ml_seed_data --clear
python manage.py create_admin
```

### الفرونت إند لا يتصل بالباك إند

1. تأكد أن الباك إند يعمل على المنفذ 8000
2. تأكد من ملف `frontend/.env` يحتوي على العنوان الصحيح
3. تحقق من إعدادات CORS في `backend/.env`

### خطأ في WebSocket

- WebSocket يعمل بذاكرة محلية بدون Redis
- هذا كافي للتطوير المحلي

### خطأ في الشات بوت ("خدمة AI غير متاحة")

- أضف `HUGGINGFACE_API_TOKEN` في ملف `backend/.env`
- احصل على التوكن من: https://huggingface.co/settings/tokens

### النماذج تعيد "insufficient_data"

- تأكد من زرع البيانات أولاً:
  ```bash
  python manage.py generate_ml_seed_data --clear
  ```
- النماذج تحتاج 3+ أشهر من البيانات كحد أدنى

### خطأ "No module named 'core'" عند تشغيل shell

```bash
cd backend
python manage.py shell
# وليس:
python shell
```

### خطأ في الترخيص (Permission denied)

```bash
# Linux/macOS
chmod +x run_local.sh
chmod +x start_backend.sh
chmod +x start_frontend.sh
```

### تحديث بيانات التحليلات

```bash
# لإعادة تشغيل جميع النماذج
python manage.py shell << 'EOF'
from analytics.services.forecasting.sales_forecast import run_sales_forecast
from analytics.services.clustering.customer_segmentation import run_customer_segmentation
from analytics.services.anomaly.sales_anomaly import run_sales_anomaly
run_sales_forecast()
run_customer_segmentation()
run_sales_anomaly()
EOF
```

---

## ملخص سريع للبدء

```bash
# 1) فك الضغط
unzip riadah-erp-v0.zip
cd riadah-erp-v0

# 2) إعداد الباك إند
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py generate_ml_seed_data --clear
python manage.py create_admin

# 3) إعداد الفرونت إند (طرفية جديدة)
cd ../frontend
npm install
npm run dev

# 4) تشغيل الباك إند (طرفية ثالثة)
cd ../backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000

# 5) افتح المتصفح
# http://localhost:5173
# اسم المستخدم: admin
# كلمة المرور: Admin@123
```
