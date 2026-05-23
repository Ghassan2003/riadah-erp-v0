"""
Employee Qualifications, Skills & Certifications Models.
Manages Education, Experience, Skills, Languages, and Professional Certifications.
"""

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


# =============================================
# Education (المؤهلات التعليمية)
# =============================================

class Education(models.Model):
    """Educational qualifications of an employee."""

    DEGREE_CHOICES = (
        ('high_school', 'ثانوية'),
        ('diploma', 'دبلوم'),
        ('bachelor', 'بكالوريوس'),
        ('master', 'ماجستير'),
        ('doctorate', 'دكتوراه'),
        ('other', 'أخرى'),
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='education_records',
        verbose_name='الموظف',
    )
    institution = models.CharField(
        max_length=255,
        verbose_name='المؤسسة التعليمية',
        help_text='اسم الجامعة أو المدرسة',
    )
    degree = models.CharField(
        max_length=20,
        choices=DEGREE_CHOICES,
        verbose_name='الدرجة العلمية',
        db_index=True,
    )
    major = models.CharField(
        max_length=255,
        verbose_name='التخصص',
    )
    gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='المعدل التراكمي',
        help_text='من 0.00 إلى 5.00',
        validators=[MinValueValidator(0.00), MaxValueValidator(5.00)],
    )
    graduation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ التخرج',
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='الدولة',
    )
    certificate_file = models.FileField(
        upload_to='certificates/education/',
        blank=True,
        verbose_name='ملف الشهادة',
    )
    verified = models.BooleanField(
        default=False,
        verbose_name='تم التحقق',
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

    class Meta:
        verbose_name = 'مؤهل تعليمي'
        verbose_name_plural = 'المؤهلات التعليمية'
        ordering = ['-graduation_date', '-created_at']

    def __str__(self):
        return f'{self.employee.full_name} - {self.get_degree_display()} في {self.major}'


# =============================================
# Experience (الخبرات العملية)
# =============================================

class Experience(models.Model):
    """Work experience history of an employee."""

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='experience_records',
        verbose_name='الموظف',
    )
    company_name = models.CharField(
        max_length=255,
        verbose_name='اسم الشركة',
    )
    position = models.CharField(
        max_length=255,
        verbose_name='المسمى الوظيفي',
    )
    department = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='القسم',
    )
    start_date = models.DateField(
        verbose_name='تاريخ البداية',
        db_index=True,
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ النهاية',
        help_text='اتركه فارغاً إذا كانت الوظيفة الحالية',
    )
    is_current = models.BooleanField(
        default=False,
        verbose_name='وظيفة حالية',
        db_index=True,
    )
    responsibilities = models.TextField(
        blank=True,
        default='',
        verbose_name='المهام والمسؤوليات',
    )
    achievements = models.TextField(
        blank=True,
        default='',
        verbose_name='الإنجازات',
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='الدولة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'خبرة عملية'
        verbose_name_plural = 'الخبرات العملية'
        ordering = ['-start_date', '-created_at']

    def __str__(self):
        company_display = f'{self.company_name} - '
        position_display = f'{self.position}'
        return f'{self.employee.full_name} - {company_display}{position_display}'

    def save(self, *args, **kwargs):
        """Auto-set is_current when end_date is None."""
        if self.end_date is None:
            self.is_current = True
        else:
            self.is_current = False
        super().save(*args, **kwargs)

    @property
    def duration_months(self):
        """Calculate total duration in months."""
        from datetime import date
        end = self.end_date or date.today()
        delta = (end.year - self.start_date.year) * 12 + (end.month - self.start_date.month)
        return max(delta, 0)


# =============================================
# Skill (المهارات)
# =============================================

class Skill(models.Model):
    """Employee skills with proficiency levels."""

    SKILL_TYPE_CHOICES = (
        ('technical', 'مهارة تقنية'),
        ('soft', 'مهارة شخصية'),
        ('language', 'لغة'),
        ('other', 'أخرى'),
    )

    PROFICIENCY_LEVEL_CHOICES = (
        ('beginner', 'مبتدئ'),
        ('intermediate', 'متوسط'),
        ('advanced', 'متقدم'),
        ('expert', 'خبير'),
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='skills',
        verbose_name='الموظف',
    )
    skill_name = models.CharField(
        max_length=255,
        verbose_name='اسم المهارة',
    )
    skill_type = models.CharField(
        max_length=20,
        choices=SKILL_TYPE_CHOICES,
        default='technical',
        verbose_name='نوع المهارة',
        db_index=True,
    )
    proficiency_level = models.CharField(
        max_length=20,
        choices=PROFICIENCY_LEVEL_CHOICES,
        default='intermediate',
        verbose_name='مستوى الإتقان',
        db_index=True,
    )
    years_of_experience = models.IntegerField(
        default=0,
        verbose_name='سنوات الخبرة',
        validators=[MinValueValidator(0)],
    )
    certificate_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='اسم الشهادة',
    )
    certificate_file = models.FileField(
        upload_to='certificates/skills/',
        blank=True,
        verbose_name='ملف الشهادة',
    )
    verified = models.BooleanField(
        default=False,
        verbose_name='تم التحقق',
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'مهارة'
        verbose_name_plural = 'المهارات'
        ordering = ['skill_type', 'skill_name']

    def __str__(self):
        return f'{self.employee.full_name} - {self.skill_name} ({self.get_proficiency_level_display()})'


# =============================================
# Language (اللغات)
# =============================================

class Language(models.Model):
    """Languages spoken by an employee with proficiency details."""

    PROFICIENCY_CHOICES = (
        ('native', 'لغة أم'),
        ('fluent', 'بطلاقة'),
        ('advanced', 'متقدم'),
        ('intermediate', 'متوسط'),
        ('beginner', 'مبتدئ'),
    )

    LANGUAGE_SKILL_CHOICES = (
        ('excellent', 'ممتاز'),
        ('good', 'جيد'),
        ('fair', 'مقبول'),
        ('basic', 'أساسي'),
    )

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='languages',
        verbose_name='الموظف',
    )
    language = models.CharField(
        max_length=100,
        verbose_name='اللغة',
        help_text='مثال: العربية، الإنجليزية، الفرنسية',
    )
    proficiency = models.CharField(
        max_length=20,
        choices=PROFICIENCY_CHOICES,
        verbose_name='مستوى الإتقان العام',
        db_index=True,
    )
    reading = models.CharField(
        max_length=20,
        choices=LANGUAGE_SKILL_CHOICES,
        verbose_name='القراءة',
    )
    writing = models.CharField(
        max_length=20,
        choices=LANGUAGE_SKILL_CHOICES,
        verbose_name='الكتابة',
    )
    speaking = models.CharField(
        max_length=20,
        choices=LANGUAGE_SKILL_CHOICES,
        verbose_name='المحادثة',
    )
    certificate_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='اسم الشهادة',
    )
    certificate_file = models.FileField(
        upload_to='certificates/languages/',
        blank=True,
        verbose_name='ملف الشهادة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'لغة'
        verbose_name_plural = 'اللغات'
        ordering = ['-proficiency', 'language']
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'language'],
                name='unique_language_employee',
            ),
        ]

    def __str__(self):
        return f'{self.employee.full_name} - {self.language} ({self.get_proficiency_display()})'


# =============================================
# Certification (الشهادات المهنية)
# =============================================

class Certification(models.Model):
    """Professional certifications held by an employee."""

    employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.CASCADE,
        related_name='certifications',
        verbose_name='الموظف',
    )
    name = models.CharField(
        max_length=255,
        verbose_name='اسم الشهادة',
    )
    issuing_organization = models.CharField(
        max_length=255,
        verbose_name='الجهة المانحة',
    )
    certificate_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='رقم الشهادة',
    )
    issue_date = models.DateField(
        verbose_name='تاريخ الإصدار',
        db_index=True,
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الانتهاء',
        help_text='اتركه فارغاً إذا كانت الشهادة لا تنتهي',
    )
    is_expired = models.BooleanField(
        default=False,
        verbose_name='منتهية الصلاحية',
        db_index=True,
    )
    credential_url = models.URLField(
        blank=True,
        default='',
        verbose_name='رابط الاعتماد',
    )
    certificate_file = models.FileField(
        upload_to='certifications/',
        blank=True,
        verbose_name='ملف الشهادة',
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

    class Meta:
        verbose_name = 'شهادة مهنية'
        verbose_name_plural = 'الشهادات المهنية'
        ordering = ['-issue_date', '-created_at']

    def __str__(self):
        return f'{self.employee.full_name} - {self.name}'

    def save(self, *args, **kwargs):
        """Auto-check if certification is expired."""
        if self.expiry_date:
            from datetime import date
            self.is_expired = self.expiry_date < date.today()
        else:
            self.is_expired = False
        super().save(*args, **kwargs)
