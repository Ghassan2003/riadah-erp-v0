---
Task ID: 1
Agent: Main Agent
Task: نظام توجيه المستخدمين حسب الأدوار والصلاحيات (Role-Based Routing)

Work Log:
- فحص هيكل المشروع بالكامل (28+ تطبيق Django، 60+ صفحة React)
- مراجعة نماذج المستخدمين والأدوار (User, Permission, RolePermission)
- مراجعة نظام الصلاحيات (permissions.py) - 10+ permission classes
- مراجعة AuthContext - تسجيل الدخول، 2FA، الصلاحيات
- مراجعة ProtectedRoute - كان يوجه بصمت بدون رسالة
- مراجعة MainLayout - Sidebar filtering حسب الدور
- مراجعة App.jsx - تعريف المسارات مع الأدوار
- مراجعة LoginPage - كان يوجه الجميع لـ /dashboard

الإصلاحات المنفذة:
1. إنشاء صفحة AccessDeniedPage.jsx جديدة مع:
   - عرض واضح لرسالة "وصول مرفوض"
   - إظهار دور المستخدم الحالي وأقسامه
   - زر العودة للواجهة الرئيسية الخاصة بالدور
   - نصيحة بالتواصل مع المدير
   - رابط مباشر لإدارة الصلاحيات (للمدير)

2. تحديث ProtectedRoute.jsx:
   - بدل التوجيه الصامت (Navigate to /dashboard)
   - عرض رسالة "وصول مرفوض" مع تفاصيل الدور والصلاحية
   - توفير أزرار العودة للواجهة الرئيسية أو الرجوع

3. تحديث AuthContext.jsx:
   - إضافة ROLE_HOME_MAP (خريطة الصفحات الرئيسية لكل دور)
   - إضافة ROLE_DASHBOARD_NAMES (أسماء لوحات التحكم)
   - إضافة getDefaultRoute() - تحديد الصفحة الرئيسية حسب الدور
   - إضافة getDashboardName() - اسم لوحة التحكم حسب الدور
   - إضافة isHR, isPurchasing, isProjectManager

4. تحديث LoginPage.jsx:
   - بعد تسجيل الدخول → توجيه حسب الدور (getDefaultRoute)
   - بعد 2FA → توجيه حسب الدور
   - إذا كان مسجل الدخول → توجيه حسب الدور

5. تحديث App.jsx:
   - استيراد useNavigate و AccessDeniedPage
   - إضافة SmartDashboardRedirect

6. تحديث MainLayout.jsx:
   - استخدام getDashboardName() في الشريط الجانبي
   - ربط getDefaultRoute بالتوجيه

7. إضافة ترجمات عربية/إنجليزية جديدة

خريطة التوجيه حسب الدور:
- admin → /dashboard (لوحة تحكم شاملة - كل الأقسام)
- warehouse → /warehouse (المستودعات)
- sales → /orders (أوامر البيع)
- accountant → /accounts (الحسابات)
- hr → /employees (الموظفون)
- purchasing → /purchases (المشتريات)
- project_manager → /projects (المشاريع)

Stage Summary:
- نظام التوجيه الذكي حسب الأدوار تم تنفيذه بالكامل
- كل مستخدم يرى فقط الأقسام المصرح بها في الشريط الجانبي
- صفحة وصول مرفوض تعرض رسالة واضحة بدل التوجيه الصامت
- بعد تسجيل الدخول، يُوجه المستخدم تلقائياً للصفحة الرئيسية الخاصة بدوره
