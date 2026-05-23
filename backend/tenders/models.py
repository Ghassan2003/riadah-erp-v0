"""
Tender Management Models for ERP System.
Manages Tenders, TenderDocuments, TenderBids, TenderEvaluations, and TenderAwards.
"""

from decimal import Decimal

from django.db import models
from django.utils import timezone


class Tender(models.Model):
    """Tender (مناقصة) model for managing procurement tenders."""

    TENDER_TYPE_CHOICES = (
        ('open', 'مفتوحة'),
        ('restricted', 'مقيدة'),
        ('invitation', 'بدعوة'),
    )

    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('published', 'منشورة'),
        ('evaluation', 'قيد التقييم'),
        ('awarded', 'مترسية'),
        ('cancelled', 'ملغاة'),
    )

    title = models.CharField(
        max_length=255,
        verbose_name='العنوان',
    )
    tender_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم المناقصة',
        db_index=True,
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    tender_type = models.CharField(
        max_length=20,
        choices=TENDER_TYPE_CHOICES,
        default='open',
        verbose_name='نوع المناقصة',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='الحالة',
        db_index=True,
    )
    publish_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ النشر',
    )
    closing_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الإغلاق',
    )
    opening_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ فتح العروض',
    )
    estimated_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='القيمة التقديرية',
    )
    department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenders',
        verbose_name='القسم',
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenders',
        verbose_name='المشروع',
    )
    terms_conditions = models.TextField(
        blank=True,
        default='',
        verbose_name='الشروط والأحكام',
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenders_created',
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
        ordering = ['-created_at']
        verbose_name = 'مناقصة'
        verbose_name_plural = 'المناقصات'

    def __str__(self):
        return f'{self.tender_number} - {self.title}'


class TenderDocument(models.Model):
    """Tender Document (مستند المناقصة) for uploading tender-related files."""

    tender = models.ForeignKey(
        Tender,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='المناقصة',
    )
    title = models.CharField(
        max_length=255,
        verbose_name='عنوان المستند',
    )
    file = models.FileField(
        upload_to='tenders/',
        verbose_name='الملف',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الرفع',
    )

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'مستند مناقصة'
        verbose_name_plural = 'مستندات المناقصات'

    def __str__(self):
        return f'{self.title} - {self.tender.tender_number}'


class TenderBid(models.Model):
    """Tender Bid (عرض المناقصة) submitted by suppliers."""

    STATUS_CHOICES = (
        ('submitted', 'مقدم'),
        ('qualified', 'مؤهل'),
        ('disqualified', 'غير مؤهل'),
        ('selected', 'مختار'),
        ('rejected', 'مرفوض'),
    )

    tender = models.ForeignKey(
        Tender,
        on_delete=models.CASCADE,
        related_name='bids',
        verbose_name='المناقصة',
    )
    supplier = models.ForeignKey(
        'purchases.Supplier',
        on_delete=models.CASCADE,
        related_name='tender_bids',
        verbose_name='المورد',
    )
    bid_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم العرض',
        db_index=True,
    )
    submission_date = models.DateField(
        verbose_name='تاريخ التقديم',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='submitted',
        verbose_name='الحالة',
        db_index=True,
    )
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='إجمالي المبلغ',
    )
    validity_days = models.IntegerField(
        default=90,
        verbose_name='أيام الصلاحية',
    )
    technical_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='الدرجة الفنية',
    )
    financial_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='الدرجة المالية',
    )
    total_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='الدرجة الإجمالية',
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
        ordering = ['-created_at']
        verbose_name = 'عرض مناقصة'
        verbose_name_plural = 'عروض المناقصات'

    def __str__(self):
        return f'{self.bid_number} - {self.supplier.name}'


class TenderEvaluation(models.Model):
    """Tender Evaluation (تقييم المناقصة) criteria and scores for bids."""

    bid = models.ForeignKey(
        TenderBid,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name='العرض',
    )
    criterion = models.CharField(
        max_length=255,
        verbose_name='معيار التقييم',
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الوزن',
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الدرجة',
    )
    weighted_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الدرجة الموزونة',
    )
    evaluator = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tender_evaluations',
        verbose_name='المقيّم',
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
        ordering = ['criterion']
        verbose_name = 'تقييم مناقصة'
        verbose_name_plural = 'تقييمات المناقصات'

    def __str__(self):
        return f'{self.criterion} - {self.bid.bid_number}'


class TenderAward(models.Model):
    """Tender Award (ترسية المناقصة) for assigning contracts to winning bids."""

    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('approved', 'موافق عليها'),
        ('rejected', 'مرفوضة'),
    )

    tender = models.ForeignKey(
        Tender,
        on_delete=models.CASCADE,
        related_name='awards',
        verbose_name='المناقصة',
    )
    bid = models.ForeignKey(
        TenderBid,
        on_delete=models.CASCADE,
        related_name='award',
        verbose_name='العرض الفائز',
    )
    award_date = models.DateField(
        verbose_name='تاريخ الترسية',
    )
    contract_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='قيمة العقد',
    )
    contract_duration_days = models.IntegerField(
        default=0,
        verbose_name='مدة العقد (بالأيام)',
    )
    terms = models.TextField(
        blank=True,
        default='',
        verbose_name='شروط العقد',
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tender_awards_approved',
        verbose_name='وافق بواسطة',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='الحالة',
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'ترسية مناقصة'
        verbose_name_plural = 'ترسيات المناقصات'

    def __str__(self):
        return f'{self.tender.tender_number} - {self.bid.supplier.name}'
