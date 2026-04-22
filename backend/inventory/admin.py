"""
Admin configuration for the Product model.
"""

from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Custom admin interface for the Product model."""

    list_display = (
        'name', 'sku', 'quantity', 'unit_price',
        'reorder_level', 'is_active', 'created_at',
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'sku', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('معلومات المنتج', {
            'fields': ('name', 'sku', 'description')
        }),
        ('معلومات المخزون', {
            'fields': ('quantity', 'unit_price', 'reorder_level')
        }),
        ('الحالة', {
            'fields': ('is_active',)
        }),
        ('التواريخ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    list_editable = ('quantity', 'unit_price', 'reorder_level', 'is_active')

    def get_queryset(self, request):
        """Show all products including soft-deleted ones in admin."""
        return Product.all_objects.all()

    actions = ['restore_products']

    @admin.action(description='استعادة المنتجات المحددة')
    def restore_products(self, request, queryset):
        """Restore soft-deleted products."""
        count = queryset.filter(is_active=False).update(is_active=True)
        self.message_user(request, f'تم استعادة {count} منتج(ات)')
