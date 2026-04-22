"""
Fixed Assets Models for ERP System.
Asset categories, fixed assets, transfers, maintenance, and disposals.
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal


class AssetCategory(models.Model):
    """Category for classifying fixed assets with depreciation settings."""

    name = models.CharField(
        max_length=200,
        verbose_name='اسم التصنيف',
        db_index=True,
    )
    name_en = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='اسم التصنيف (إنجليزي)',
    )
    useful_life_years = models.IntegerField(
        default=5,
        verbose_name='سنوات العمر الافتراضي',
    )
    depreciation_method = models.CharField(
        max_length=20,
        choices=(
            ('straight_line', 'القسط الثابت'),
            ('declining_balance', 'القسط المتناقص'),
        ),
        default='straight_line',
        verbose_name='طريقة الإهلاك',
    )
    salvage_value_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='نسبة القيمة التخريدية',
        help_text='النسبة المئوية من سعر الشراء كقيمة تخريدية',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
        db_index=True,
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
        verbose_name = 'تصنيف أصل'
        verbose_name_plural = 'تصنيفات الأصول'
        ordering = ['name']

    def __str__(self):
        return self.name


class FixedAsset(models.Model):
    """Fixed asset with depreciation tracking."""

    STATUS_CHOICES = (
        ('active', 'نشط'),
        ('in_maintenance', 'في الصيانة'),
        ('disposed', 'مخرد'),
        ('sold', 'مباع'),
        ('lost', 'مفقود'),
    )

    asset_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم الأصل',
        db_index=True,
        editable=False,
    )
    name = models.CharField(
        max_length=200,
        verbose_name='اسم الأصل',
    )
    name_en = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='اسم الأصل (إنجليزي)',
    )
    category = models.ForeignKey(
        AssetCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assets',
        verbose_name='التصنيف',
    )
    serial_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='الرقم التسلسلي',
    )
    barcode = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='الباركود',
    )
    purchase_date = models.DateField(
        verbose_name='تاريخ الشراء',
    )
    purchase_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name='سعر الشراء',
    )
    salvage_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='القيمة التخريدية',
    )
    useful_life_months = models.IntegerField(
        verbose_name='العمر الافتراضي (بالشهور)',
    )
    accumulated_depreciation = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='مجمع الإهلاك',
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='الموقع',
    )
    department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='department_assets',
        verbose_name='القسم',
    )
    assigned_to = models.ForeignKey(
        'hr.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_assets',
        verbose_name='مسند إلى',
    )
    supplier = models.ForeignKey(
        'purchases.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supplied_assets',
        verbose_name='المورد',
    )
    warranty_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ انتهاء الضمان',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='الحالة',
        db_index=True,
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
        verbose_name='أنشئ بواسطة',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
        db_index=True,
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
        verbose_name = 'أصل ثابت'
        verbose_name_plural = 'الأصول الثابتة'

    def __str__(self):
        return f'{self.asset_number} - {self.name}'

    def generate_asset_number(self):
        """Generate a unique asset number: AST-YYYYMMDD-XXXX."""
        today = timezone.now().strftime('%Y%m%d')
        last_ast = FixedAsset.objects.filter(
            asset_number__startswith=f'AST-{today}'
        ).order_by('-asset_number').first()

        if last_ast:
            try:
                seq = int(last_ast.asset_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f'AST-{today}-{seq:04d}'

    def save(self, *args, **kwargs):
        if not self.asset_number:
            self.asset_number = self.generate_asset_number()
        super().save(*args, **kwargs)

    @property
    def current_value(self):
        """Current book value: purchase price minus accumulated depreciation."""
        result = self.purchase_price - self.accumulated_depreciation
        return max(result, self.salvage_value)

    @property
    def monthly_depreciation(self):
        """Calculate monthly depreciation amount."""
        return self.calculate_depreciation()

    def calculate_depreciation(self):
        """
        Calculate monthly depreciation based on the category's method.
        Returns monthly depreciation amount.
        """
        if self.useful_life_months <= 0:
            return Decimal('0.00')

        depreciable_amount = self.purchase_price - self.salvage_value

        if self.category and self.category.depreciation_method == 'declining_balance':
            # Declining balance: (current_value - salvage) / remaining_months
            current_val = self.current_value
            remaining = max(self.useful_life_months, 1)
            amount = (current_val - self.salvage_value) / remaining
            return round(amount, 2)
        else:
            # Straight line: (purchase_price - salvage) / useful_life_months
            amount = depreciable_amount / self.useful_life_months
            return round(amount, 2)


class AssetTransfer(models.Model):
    """Transfer record for moving assets between departments/employees/locations."""

    asset = models.ForeignKey(
        FixedAsset,
        on_delete=models.CASCADE,
        related_name='transfers',
        verbose_name='الأصل',
    )
    from_department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_transfers_out',
        verbose_name='من قسم',
    )
    to_department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_transfers_in',
        verbose_name='إلى قسم',
    )
    from_employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_transfers_out',
        verbose_name='من موظف',
    )
    to_employee = models.ForeignKey(
        'hr.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asset_transfers_in',
        verbose_name='إلى موظف',
    )
    from_location = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='من موقع',
    )
    to_location = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='إلى موقع',
    )
    transfer_date = models.DateField(
        verbose_name='تاريخ النقل',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='وافق بواسطة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'نقل أصل'
        verbose_name_plural = 'نقل الأصول'
        ordering = ['-created_at']

    def __str__(self):
        return f'نقل {self.asset.name} - {self.transfer_date}'


class AssetMaintenance(models.Model):
    """Maintenance record for fixed assets."""

    TYPE_CHOICES = (
        ('preventive', 'وقائية'),
        ('corrective', 'تصحيحية'),
        ('emergency', 'طارئة'),
    )

    STATUS_CHOICES = (
        ('scheduled', 'مجدول'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    )

    asset = models.ForeignKey(
        FixedAsset,
        on_delete=models.CASCADE,
        related_name='maintenances',
        verbose_name='الأصل',
    )
    maintenance_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='نوع الصيانة',
    )
    description = models.TextField(
        verbose_name='الوصف',
    )
    cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='التكلفة',
    )
    maintenance_date = models.DateField(
        verbose_name='تاريخ الصيانة',
    )
    next_maintenance_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='تاريخ الصيانة القادمة',
    )
    vendor = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='مزود الخدمة',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name='الحالة',
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'صيانة أصل'
        verbose_name_plural = 'صيانات الأصول'
        ordering = ['-created_at']

    def __str__(self):
        return f'صيانة {self.asset.name} - {self.get_maintenance_type_display()}'


class AssetDisposal(models.Model):
    """Disposal record for fixed assets (sold, scraped, donated, lost)."""

    DISPOSAL_TYPE_CHOICES = (
        ('sold', 'مباع'),
        ('scraped', 'مخرد'),
        ('donated', 'متبرع به'),
        ('lost', 'مفقود'),
    )

    asset = models.ForeignKey(
        FixedAsset,
        on_delete=models.CASCADE,
        related_name='disposals',
        verbose_name='الأصل',
    )
    disposal_type = models.CharField(
        max_length=20,
        choices=DISPOSAL_TYPE_CHOICES,
        verbose_name='نوع التخريد',
    )
    disposal_date = models.DateField(
        verbose_name='تاريخ التخريد',
    )
    disposal_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='قيمة التخريد',
    )
    buyer_name = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name='اسم المشتري',
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name='ملاحظات',
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='وافق بواسطة',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    class Meta:
        verbose_name = 'تخريد أصل'
        verbose_name_plural = 'تخريد الأصول'
        ordering = ['-created_at']

    def __str__(self):
        return f'تخريد {self.asset.name} - {self.get_disposal_type_display()}'

    @property
    def loss_gain(self):
        """Loss or gain from disposal: disposal_value - current_value."""
        return self.disposal_value - self.asset.current_value
