"""
Recruitment & Hiring Models for ERP System.
Manages Job Requisitions, Postings, Applications, Interviews, and Job Offers.
"""

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


# =============================================
# Helper Functions
# =============================================

def create_requisition_number():
    """Auto-generate unique requisition number: REQ-YYYYMMDD-XXXX."""
    today = timezone.now().strftime('%Y%m%d')
    prefix = f'REQ-{today}-'
    last_req = JobRequisition.objects.filter(
        requisition_number__startswith=prefix,
    ).order_by('-requisition_number').first()

    if last_req:
        try:
            seq = int(last_req.requisition_number.split('-')[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1

    return f'{prefix}{seq:04d}'


def create_posting_number():
    """Auto-generate unique posting number: POST-YYYYMMDD-XXXX."""
    today = timezone.now().strftime('%Y%m%d')
    prefix = f'POST-{today}-'
    last_posting = JobPosting.objects.filter(
        posting_number__startswith=prefix,
    ).order_by('-posting_number').first()

    if last_posting:
        try:
            seq = int(last_posting.posting_number.split('-')[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1

    return f'{prefix}{seq:04d}'


def create_application_number():
    """Auto-generate unique application number: APP-YYYYMMDD-XXXX."""
    today = timezone.now().strftime('%Y%m%d')
    prefix = f'APP-{today}-'
    last_app = JobApplication.objects.filter(
        application_number__startswith=prefix,
    ).order_by('-application_number').first()

    if last_app:
        try:
            seq = int(last_app.application_number.split('-')[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1

    return f'{prefix}{seq:04d}'


def create_offer_number():
    """Auto-generate unique offer number: OFR-YYYYMMDD-XXXX."""
    today = timezone.now().strftime('%Y%m%d')
    prefix = f'OFR-{today}-'
    last_offer = JobOffer.objects.filter(
        offer_number__startswith=prefix,
    ).order_by('-offer_number').first()

    if last_offer:
        try:
            seq = int(last_offer.offer_number.split('-')[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1

    return f'{prefix}{seq:04d}'


def hire_candidate(offer, user):
    """
    Create an Employee record from an accepted JobOffer and update
    the related requisition's filled_count.
    """
    from hr.models import Employee, EmploymentHistory

    application = offer.application

    # Create the Employee record
    employee = Employee(
        first_name=application.first_name,
        last_name=application.last_name,
        email=application.email,
        phone=application.phone,
        gender=application.gender,
        national_id=application.national_id,
        department=offer.department,
        position=offer.position,
        hire_date=offer.start_date,
        salary=offer.proposed_salary,
        housing_allowance=offer.housing_allowance,
        transport_allowance=offer.transport_allowance,
        status='active',
    )
    employee.save()

    # Create an employment history record
    EmploymentHistory.objects.create(
        employee=employee,
        action_type='hire',
        department=offer.department,
        position=offer.position,
        salary=offer.proposed_salary,
        effective_date=offer.start_date,
        reason=f'تم التعيين بناءً على العرض الوظيفي {offer.offer_number}',
        created_by=user,
    )

    # Update application status
    application.status = 'hired'
    application.save(update_fields=['status', 'updated_at'])

    # Update requisition filled_count
    requisition = offer.requisition
    if requisition:
        requisition.filled_count = (requisition.filled_count or 0) + 1
        if requisition.filled_count >= requisition.required_count:
            requisition.status = 'filled'
        requisition.save(update_fields=['filled_count', 'status', 'updated_at'])

    return employee


# =============================================
# Job Requisition (طلب توظيف)
# =============================================

class JobRequisition(models.Model):
    """Formal request to open a new position or fill a vacancy."""

    PRIORITY_CHOICES = (
        ('urgent', 'عاجل'),
        ('high', 'عالية'),
        ('medium', 'متوسطة'),
        ('low', 'منخفضة'),
    )

    EMPLOYMENT_TYPE_CHOICES = (
        ('full_time', 'دوام كامل'),
        ('part_time', 'دوام جزئي'),
        ('contract', 'عقد'),
        ('intern', 'تدريب تعاوني'),
        ('temporary', 'مؤقت'),
    )

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('submitted', 'مُقدّم'),
        ('approved', 'مُوافق عليه'),
        ('cancelled', 'ملغي'),
        ('filled', 'مملوء'),
    )

    requisition_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم طلب التوظيف',
        db_index=True,
        editable=False,
    )
    department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_requisitions',
        verbose_name='القسم',
    )
    position = models.CharField(
        max_length=255,
        verbose_name='المسمى الوظيفي',
    )
    job_description = models.TextField(
        verbose_name='وصف الوظيفة',
    )
    required_count = models.IntegerField(
        verbose_name='عدد الوظائف المطلوبة',
        validators=[MinValueValidator(1)],
    )
    filled_count = models.IntegerField(
        default=0,
        verbose_name='عدد الوظائف المملوءة',
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='الأولوية',
        db_index=True,
    )
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        verbose_name='نوع التوظيف',
        db_index=True,
    )
    min_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='الحد الأدنى للراتب',
        help_text='بالريال السعودي',
    )
    max_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='الحد الأقصى للراتب',
        help_text='بالريال السعودي',
    )
    required_qualifications = models.TextField(
        blank=True,
        default='',
        verbose_name='المؤهلات المطلوبة',
    )
    required_experience = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='الخبرة المطلوبة',
        help_text='مثال: 3-5 سنوات',
    )
    skills_required = models.JSONField(
        default=list,
        blank=True,
        verbose_name='المهارات المطلوبة',
        help_text='قائمة بالمهارات المطلوبة',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    requested_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requisitions_requested',
        verbose_name='مُقدم الطلب',
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requisitions_approved',
        verbose_name='وافق بواسطة',
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الموافقة',
    )
    deadline = models.DateField(
        null=True,
        blank=True,
        verbose_name='الموعد النهائي',
        db_index=True,
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        verbose_name = 'طلب توظيف'
        verbose_name_plural = 'طلبات التوظيف'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.requisition_number} - {self.position}'

    def save(self, *args, **kwargs):
        if not self.requisition_number:
            self.requisition_number = create_requisition_number()
        super().save(*args, **kwargs)

    @property
    def remaining_count(self):
        """Number of positions still to be filled."""
        return max((self.required_count or 0) - (self.filled_count or 0), 0)

    @property
    def salary_range_display(self):
        """Formatted salary range string."""
        if self.min_salary and self.max_salary:
            return f'{self.min_salary:,.0f} - {self.max_salary:,.0f} ر.س'
        elif self.min_salary:
            return f'من {self.min_salary:,.0f} ر.س'
        elif self.max_salary:
            return f'حتى {self.max_salary:,.0f} ر.س'
        return ''


# =============================================
# Job Posting (إعلان وظيفي)
# =============================================

class JobPosting(models.Model):
    """Published job advertisement linked to a requisition."""

    EMPLOYMENT_TYPE_CHOICES = JobRequisition.EMPLOYMENT_TYPE_CHOICES

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('published', 'منشور'),
        ('closed', 'مغلق'),
        ('expired', 'منتهي الصلاحية'),
    )

    posting_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم الإعلان الوظيفي',
        db_index=True,
        editable=False,
    )
    requisition = models.ForeignKey(
        JobRequisition,
        on_delete=models.CASCADE,
        related_name='postings',
        verbose_name='طلب التوظيف',
    )
    title = models.CharField(
        max_length=255,
        verbose_name='عنوان الإعلان',
    )
    description = models.TextField(
        verbose_name='الوصف',
    )
    requirements = models.TextField(
        verbose_name='المتطلبات',
    )
    benefits = models.TextField(
        blank=True,
        default='',
        verbose_name='المزايا والبدلات',
    )
    location = models.CharField(
        max_length=255,
        verbose_name='موقع العمل',
    )
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        verbose_name='نوع التوظيف',
        db_index=True,
    )
    salary_range = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='نطاق الراتب',
        help_text='مثال: 8,000 - 12,000 ر.س',
    )
    is_internal = models.BooleanField(
        default=False,
        verbose_name='إعلان داخلي',
        help_text='عرض الإعلان للموظفين الحاليين فقط',
    )
    is_external = models.BooleanField(
        default=True,
        verbose_name='إعلان خارجي',
        help_text='عرض الإعلان للجمهور',
    )
    posted_on = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='منصة النشر',
        help_text='اسم المنصة: LinkedIn، Bayt، إلخ',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ النشر',
    )
    closes_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإغلاق',
        db_index=True,
    )
    applications_count = models.IntegerField(
        default=0,
        verbose_name='عدد الطلبات',
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='postings_created',
        verbose_name='أنشئ بواسطة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        verbose_name = 'إعلان وظيفي'
        verbose_name_plural = 'الإعلانات الوظيفية'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.posting_number} - {self.title}'

    def save(self, *args, **kwargs):
        if not self.posting_number:
            self.posting_number = create_posting_number()
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """Check if the posting is currently accepting applications."""
        if self.status != 'published':
            return False
        if self.closes_at and self.closes_at < timezone.now():
            return False
        return True


# =============================================
# Job Application (طلب توظيف / سيرة ذاتية)
# =============================================

class JobApplication(models.Model):
    """Candidate application for a job posting or direct application."""

    SOURCE_CHOICES = (
        ('website', 'الموقع الإلكتروني'),
        ('referral', 'إحالة'),
        ('linkedin', 'لينكد إن'),
        ('other', 'أخرى'),
    )

    STATUS_CHOICES = (
        ('new', 'جديد'),
        ('screening', 'فرز أولي'),
        ('interview', 'مقابلة'),
        ('offer', 'عرض وظيفي'),
        ('hired', 'مُعَيّن'),
        ('rejected', 'مرفوض'),
        ('withdrawn', 'منسحب'),
    )

    application_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم الطلب',
        db_index=True,
        editable=False,
    )
    posting = models.ForeignKey(
        JobPosting,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications',
        verbose_name='الإعلان الوظيفي',
        help_text='يمكن أن يكون التقديم مباشراً بدون إعلان',
    )
    requisition = models.ForeignKey(
        JobRequisition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications',
        verbose_name='طلب التوظيف',
    )
    first_name = models.CharField(
        max_length=100,
        verbose_name='الاسم الأول',
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name='اسم العائلة',
    )
    email = models.EmailField(
        verbose_name='البريد الإلكتروني',
        db_index=True,
    )
    phone = models.CharField(
        max_length=30,
        verbose_name='رقم الهاتف',
    )
    national_id = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='رقم الهوية',
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الميلاد',
    )
    gender = models.CharField(
        max_length=10,
        blank=True,
        default='',
        verbose_name='الجنس',
    )
    education = models.TextField(
        blank=True,
        default='',
        verbose_name='المؤهلات التعليمية',
    )
    experience_years = models.IntegerField(
        default=0,
        verbose_name='سنوات الخبرة',
        validators=[MinValueValidator(0)],
    )
    current_company = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='الشركة الحالية',
    )
    current_position = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='المسمى الوظيفي الحالي',
    )
    expected_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='الراتب المتوقع',
        help_text='بالريال السعودي',
    )
    cv_file = models.FileField(
        upload_to='resumes/',
        blank=True,
        verbose_name='ملف السيرة الذاتية',
    )
    cover_letter = models.TextField(
        blank=True,
        default='',
        verbose_name='خطاب التغطية',
    )
    linkedin_profile = models.URLField(
        blank=True,
        default='',
        verbose_name='رابط ملف لينكد إن',
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='website',
        verbose_name='مصدر التقديم',
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='الحالة',
        db_index=True,
    )
    rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='التقييم',
        help_text='من 1 إلى 5',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications_assigned',
        verbose_name='المسؤول عن الطلب',
        help_text='مسؤول التوظيف المكلف',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    rejection_reason = models.TextField(
        blank=True,
        default='',
        verbose_name='سبب الرفض',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        verbose_name = 'طلب توظيف'
        verbose_name_plural = 'طلبات التوظيف'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.application_number} - {self.full_name}'

    def save(self, *args, **kwargs):
        if not self.application_number:
            self.application_number = create_application_number()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        """Return the candidate's full name."""
        return f'{self.first_name} {self.last_name}'

    @property
    def interviews_count(self):
        """Number of interviews scheduled for this application."""
        return self.interviews.count()


# =============================================
# Interview (مقابلة)
# =============================================

class Interview(models.Model):
    """Interview session for a job application with evaluation scores."""

    INTERVIEW_TYPE_CHOICES = (
        ('phone', 'هاتفية'),
        ('video', 'عن بُعد (فيديو)'),
        ('onsite', 'حضورية'),
        ('technical', 'فنية'),
        ('behavioral', 'سلوكية'),
        ('panel', 'لجنة'),
    )

    STATUS_CHOICES = (
        ('scheduled', 'مجدولة'),
        ('completed', 'مكتملة'),
        ('cancelled', 'ملغاة'),
        ('no_show', 'لم يحضر'),
    )

    RECOMMENDATION_CHOICES = (
        ('strong_hire', 'ترشيح قوي'),
        ('hire', 'ترشيح'),
        ('no_hire', 'لا يُرشح'),
        ('strong_no_hire', 'رفض قوي'),
    )

    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='interviews',
        verbose_name='طلب التوظيف',
    )
    interview_type = models.CharField(
        max_length=20,
        choices=INTERVIEW_TYPE_CHOICES,
        verbose_name='نوع المقابلة',
        db_index=True,
    )
    interviewer = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interviews_conducted',
        verbose_name='المُقابل',
    )
    scheduled_date = models.DateTimeField(
        verbose_name='موعد المقابلة',
        db_index=True,
    )
    duration_minutes = models.IntegerField(
        default=60,
        verbose_name='المدة (دقيقة)',
        validators=[MinValueValidator(15)],
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='المكان',
        help_text='رقم القاعة أو رابط الاجتماع',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name='الحالة',
        db_index=True,
    )
    technical_score = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='درجة التقييم الفني',
        help_text='من 0 إلى 100',
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    behavioral_score = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='درجة التقييم السلوكي',
        help_text='من 0 إلى 100',
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    communication_score = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='درجة التواصل',
        help_text='من 0 إلى 100',
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    overall_score = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='الدرجة الإجمالية',
        help_text='من 0 إلى 100',
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    strengths = models.TextField(
        blank=True,
        default='',
        verbose_name='نقاط القوة',
    )
    weaknesses = models.TextField(
        blank=True,
        default='',
        verbose_name='نقاط الضعف',
    )
    recommendation = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_CHOICES,
        blank=True,
        default='',
        verbose_name='التوصية',
        db_index=True,
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        verbose_name = 'مقابلة'
        verbose_name_plural = 'المقابلات'
        ordering = ['scheduled_date']

    def __str__(self):
        return f'مقابلة {self.get_interview_type_display()} - {self.application.full_name}'

    def save(self, *args, **kwargs):
        """Auto-calculate overall score from individual scores."""
        scores = [
            self.technical_score,
            self.behavioral_score,
            self.communication_score,
        ]
        valid_scores = [s for s in scores if s is not None]
        if valid_scores:
            self.overall_score = round(sum(valid_scores) / len(valid_scores))
        super().save(*args, **kwargs)

    @property
    def candidate_name(self):
        """Return the candidate's full name from the application."""
        return self.application.full_name

    @property
    def position_applied(self):
        """Return the position title from the related posting or requisition."""
        if self.application.posting:
            return self.application.posting.title
        if self.application.requisition:
            return self.application.requisition.position
        return ''


# =============================================
# Job Offer (عرض وظيفي)
# =============================================

class JobOffer(models.Model):
    """Formal job offer extended to a candidate."""

    EMPLOYMENT_TYPE_CHOICES = JobRequisition.EMPLOYMENT_TYPE_CHOICES

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('sent', 'مُرسل'),
        ('accepted', 'مقبول'),
        ('rejected', 'مرفوض'),
        ('revoked', 'ملغى'),
        ('expired', 'منتهي الصلاحية'),
    )

    offer_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم العرض الوظيفي',
        db_index=True,
        editable=False,
    )
    application = models.OneToOneField(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='job_offer',
        verbose_name='طلب التوظيف',
    )
    requisition = models.ForeignKey(
        JobRequisition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_offers',
        verbose_name='طلب التوظيف',
    )
    position = models.CharField(
        max_length=255,
        verbose_name='المسمى الوظيفي',
    )
    department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_offers',
        verbose_name='القسم',
    )
    proposed_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='الراتب المقترح',
        help_text='بالريال السعودي',
    )
    housing_allowance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='بدل السكن',
    )
    transport_allowance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='بدل النقل',
    )
    other_allowances = models.TextField(
        blank=True,
        default='',
        verbose_name='بدلات أخرى',
        help_text='وصف أي بدلات إضافية',
    )
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        verbose_name='نوع التوظيف',
        db_index=True,
    )
    start_date = models.DateField(
        verbose_name='تاريخ الالتحاق',
        db_index=True,
    )
    contract_duration = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='مدة العقد',
        help_text='مثال: سنة واحدة، غير محدد',
    )
    probation_months = models.IntegerField(
        default=3,
        verbose_name='مدة فترة التجربة (شهر)',
        validators=[MinValueValidator(0)],
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإرسال',
    )
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الرد',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offers_created',
        verbose_name='أنشئ بواسطة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        verbose_name = 'عرض وظيفي'
        verbose_name_plural = 'العروض الوظيفية'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.offer_number} - {self.position} - {self.application.full_name}'

    def save(self, *args, **kwargs):
        if not self.offer_number:
            self.offer_number = create_offer_number()
        super().save(*args, **kwargs)

    @property
    def candidate_name(self):
        """Return the candidate's full name from the application."""
        return self.application.full_name

    @property
    def total_compensation(self):
        """Calculate total monthly compensation including allowances."""
        return self.proposed_salary + self.housing_allowance + self.transport_allowance

    @property
    def total_compensation_display(self):
        """Formatted total compensation string."""
        return f'{self.total_compensation:,.0f} ر.س / شهر'
