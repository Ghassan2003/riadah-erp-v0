# نظام ERP - المرحلة 2: وحدة إدارة المخزون

## وصف المشروع

نظام تخطيط موارد المؤسسة (ERP) مبسط وقابل للتوسع بشكل تدريجي. يتم تطويره على 5 مراحل، وهذه هي **المرحلة 2** التي تتضمن وحدة إدارة المخزون (Inventory).

## المتطلبات التقنية

| المكون | التقنية |
|---------|---------|
| Backend | Django 4.2 + Django REST Framework |
| Frontend | React 18 + Vite 5 + TailwindCSS 3 |
| Database | PostgreSQL 15 (Docker) / SQLite (محلي) |
| Authentication | JWT (djangorestframework-simplejwt) |
| API Documentation | Django REST Framework Browsable API |
| Containerization | Docker + Docker Compose |

---

## طريقة التشغيل

### الخيار 1: التشغيل عبر Docker (موصى به)

#### المتطلبات المسبقة
- Docker Desktop أو Docker Engine
- Docker Compose

#### الخطوات

1. **انتقل إلى مجلد المشروع:**
   ```bash
   cd erp-system
   ```

2. **شغّل المشروع بالكامل:**
   ```bash
   docker-compose up --build
   ```

3. **انتظر حتى تظهر الرسائل التالية في الـ logs:**
   ```
   Admin user created successfully!
   Seeding complete!
   ```

4. **افتح المتصفح على:**
   - **الواجهة الأمامية:** [http://localhost:3000](http://localhost:3000)
   - **Django Admin:** [http://localhost:8000/admin/](http://localhost:8000/admin/)
   - **API Documentation:** [http://localhost:8000/api/](http://localhost:8000/api/)

5. **بيانات الدخول الافتراضية:**
   - **اسم المستخدم:** `admin`
   - **كلمة المرور:** `admin123`

---

### الخيار 2: التشغيل المحلي (بدون Docker)

#### المتطلبات المسبقة
- Python 3.10+
- Node.js 18+
- pip
- npm

#### الخطوات

##### 1. إعداد Backend

```bash
# انتقل إلى مجلد Backend
cd backend

# إنشاء بيئة افتراضية (اختياري ولكن موصى به)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate     # Windows

# تثبيت المتطلبات
pip install -r requirements.txt

# إنشاء قاعدة البيانات (SQLite)
python manage.py migrate

# إنشاء مستخدم المدير الافتراضي
python manage.py create_admin

# إنشاء بيانات تجريبية للمنتجات (10 منتجات)
python manage.py seed_products

# تشغيل الخادم
python manage.py runserver 0.0.0.0:8000
```

##### 2. إعداد Frontend (في نافذة طرفية جديدة)

```bash
# انتقل إلى مجلد Frontend
cd frontend

# تثبيت المتطلبات
npm install

# تشغيل خادم التطوير
npm run dev
```

##### 3. افتح المتصفح
- **الواجهة الأمامية:** [http://localhost:5173](http://localhost:5173)
- **Django Admin:** [http://localhost:8000/admin/](http://localhost:8000/admin/)

---

## هيكل المشروع

```
erp-system/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── core/                      # Django project settings
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── users/                     # Users app (Phase 1)
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py              # Custom User model
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── permissions.py
│   │   └── management/commands/
│   │       ├── create_admin.py
│   │       └── ...
│   └── inventory/                 # Inventory app (Phase 2 - NEW)
│       ├── __init__.py
│       ├── admin.py               # Django admin config
│       ├── apps.py
│       ├── models.py              # Product model with soft delete
│       ├── managers.py            # Custom query managers
│       ├── serializers.py         # Product serializers
│       ├── views.py               # CRUD + stats views
│       ├── urls.py                # Inventory API URLs
│       └── management/commands/
│           └── seed_products.py   # Sample data seeder
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── nginx.conf
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── index.html
│   ├── public/
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── api/
│       │   └── index.js           # API client + inventory endpoints
│       ├── context/
│       │   └── AuthContext.jsx
│       ├── components/
│       │   ├── MainLayout.jsx     # Updated with inventory nav
│       │   ├── ProtectedRoute.jsx
│       │   └── LoadingSpinner.jsx
│       └── pages/
│           ├── LoginPage.jsx
│           ├── DashboardPage.jsx  # Updated with real stats
│           ├── ProductsPage.jsx   # NEW - full product management
│           ├── ProfilePage.jsx
│           └── UsersPage.jsx
├── docker-compose.yml
└── README.md
```

---

## API Endpoints - المرحلة 2

### المصادقة (Authentication) - من المرحلة 1

| الطريقة | المسار | الوصف | الصلاحية |
|---------|--------|-------|----------|
| POST | `/api/auth/login/` | تسجيل الدخول (JWT) | عام |
| POST | `/api/auth/refresh/` | تجديد Access Token | مع Refresh Token |
| GET | `/api/auth/profile/` | عرض بيانات المستخدم | مسجل الدخول |
| PATCH | `/api/auth/profile/` | تحديث الملف الشخصي | صاحب الحساب |
| POST | `/api/auth/change-password/` | تغيير كلمة المرور | مسجل الدخول |
| POST | `/api/auth/register/` | إنشاء مستخدم جديد | Admin فقط |
| GET | `/api/auth/users/` | قائمة المستخدمين | Admin فقط |

### إدارة المخزون (Inventory) - جديد في المرحلة 2

| الطريقة | المسار | الوصف | الصلاحية |
|---------|--------|-------|----------|
| GET | `/api/inventory/stats/` | إحصائيات المخزون | مسجل الدخول |
| GET | `/api/inventory/products/` | قائمة المنتجات (مع بحث) | مسجل الدخول |
| POST | `/api/inventory/products/` | إضافة منتج جديد | Admin + Warehouse |
| GET | `/api/inventory/products/{id}/` | تفاصيل منتج | مسجل الدخول |
| PATCH | `/api/inventory/products/{id}/` | تحديث منتج | Admin + Warehouse |
| DELETE | `/api/inventory/products/{id}/soft-delete/` | حذف ناعم (تعطيل) | Admin + Warehouse |
| POST | `/api/inventory/products/{id}/restore/` | استعادة منتج محذوف | Admin + Warehouse |

#### معاملات البحث (Query Parameters)
- `search`: بحث بالاسم أو SKU
- `show_deleted=true`: عرض المنتجات المحذوفة أيضاً
- `ordering`: ترتيب (`name`, `sku`, `quantity`, `unit_price`, `-created_at`)
- `page`: رقم الصفحة

---

## نظام الأدوار والصلاحيات (مُحدّث)

| الدور | الكود | صلاحيات المرحلة 2 |
|-------|-------|-------------------|
| مدير النظام | `admin` | كل شيء + إدارة المستخدمين + إدارة المنتجات |
| موظف المخازن | `warehouse` | عرض المنتجات + إضافة/تعديل/حذف المنتجات |
| موظف المبيعات | `sales` | عرض المنتجات فقط (قراءة) |
| المحاسب | `accountant` | عرض المنتجات فقط (قراءة) |

---

## اختبار المرحلة 2 خطوة بخطوة

### 1. تسجيل الدخول
- افتح [http://localhost:3000](http://localhost:3000)
- أدخل: `admin` / `admin123`
- ✅ يجب أن تنتقل إلى لوحة التحكم

### 2. لوحة التحكم (Dashboard)
- ✅ يجب أن ترى إحصائيات المخزون الحقيقية (10 منتجات)
- ✅ يجب أن ترى تنبيه عن المنتجات منخفضة المخزون (3 منتجات)
- ✅ اضغط على بطاقة "إجمالي المنتجات" لتنتقل لصفحة المنتجات

### 3. إدارة المنتجات (Crud كامل)
- اضغط "إدارة المنتجات" في القائمة الجانبية
- ✅ يجب أن ترى جدول بـ 10 منتجات مع أعمدة (الاسم، SKU، الكمية، السعر، القيمة، الحالة)
- ✅ المنتجات منخفضة المخزون يجب أن تظهر بلون برتقالي
- ✅ اضغط على زر "إضافة منتج جديد" وأضف منتج جديد
- ✅ اضغط على زر التعديل (قلم) لتعديل منتج موجود
- ✅ اضغط على زر الحذف (سلة) وأكد الحذف
- ✅ فعّل "عرض المحذوفة" لرؤية المنتجات المحذوفة
- ✅ اضغط زر الاستعادة لمنتج محذوف
- ✅ استخدم خانة البحث للبحث بالاسم أو SKU
- ✅ يجب أن تظهر إشعارات Toast لكل عملية

### 4. اختبار الصلاحيات
- أنشئ مستخدم `warehouse` من Django Admin أو عبر API
- سجّل دخول بمستخدم `warehouse`
- ✅ يجب أن يرى زر "إضافة منتج جديد"
- ✅ يجب أن يرى أزرار التعديل والحذف
- أنشئ مستخدم `sales`
- سجّل دخول بمستخدم `sales`
- ✅ يجب أن يرى المنتجات لكن بدون أزرار الإضافة/التعديل/الحذف

### 5. Django Admin
- افتح [http://localhost:8000/admin/](http://localhost:8000/admin/)
- ✅ يمكنك رؤية وإدارة المنتجات (بما فيها المحذوفة)
- ✅ يمكنك استعادة المنتجات المحذوفة من Admin

---

## المراحل القادمة

| المرحلة | الوحدة | الحالة |
|---------|--------|--------|
| المرحلة 1 | الهيكل الأساسي والمصادقة | ✅ مكتملة |
| المرحلة 2 | وحدة إدارة المخزون (Inventory) | ✅ مكتملة |
| المرحلة 3 | وحدة المبيعات وإدارة العملاء | ⏳ قادمة |
| المرحلة 4 | وحدة المحاسبة البسيطة | ⏳ قادمة |
| المرحلة 5 | وحدة الموارد البشرية والتقارير | ⏳ قادمة |
