"""
Admin configuration for custom User model.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom admin interface for the User model."""

    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'role', 'is_active', 'created_at',
    )
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-created_at',)

    fieldsets = UserAdmin.fieldsets + (
        ('معلومات إضافية', {
            'fields': ('role', 'phone')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('معلومات إضافية', {
            'fields': ('role', 'phone')
        }),
    )
