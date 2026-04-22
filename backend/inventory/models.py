"""
Product model for inventory management.
Supports soft delete (is_active flag) and SKU tracking.
"""

from django.db import models
from .managers import ProductManager, AllProductManager


class Product(models.Model):
    """Product model with inventory tracking capabilities."""

    name = models.CharField(
        max_length=255,
        verbose_name='اسم المنتج',
        db_index=True,
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='الوصف',
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='رمز المنتج (SKU)',
        db_index=True,
        help_text='رمز فريد لتحديد المنتج',
    )
    quantity = models.PositiveIntegerField(
        default=0,
        verbose_name='الكمية المتوفرة',
        help_text='الكمية الحالية في المخزون',
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='سعر الوحدة',
        help_text='سعر البيع لكل وحدة',
    )
    reorder_level = models.PositiveIntegerField(
        default=10,
        verbose_name='حد إعادة الطلب',
        help_text='الحد الأدنى للكمية قبل طلب المزيد',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
        db_index=True,
        help_text='الحذف الناعم - يعطل المنتج بدلاً من حذفه',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    # Custom managers
    objects = ProductManager()        # Default: active products only
    all_objects = AllProductManager() # All products including deleted

    class Meta:
        verbose_name = 'منتج'
        verbose_name_plural = 'المنتجات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['is_active']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f'{self.name} ({self.sku})'

    @property
    def is_low_stock(self):
        """Check if product quantity is below reorder level."""
        return self.quantity <= self.reorder_level

    @property
    def total_value(self):
        """Calculate total inventory value for this product."""
        return self.quantity * self.unit_price

    def soft_delete(self):
        """Mark product as inactive instead of deleting."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])

    def restore(self):
        """Restore a soft-deleted product."""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])
