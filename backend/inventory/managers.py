"""
Custom manager for Product model.
Provides filtered querysets for active/inactive products.
"""

from django.db import models


class ProductManager(models.Manager):
    """Default manager - returns only active products."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class AllProductManager(models.Manager):
    """Manager that returns all products including soft-deleted ones."""

    def get_queryset(self):
        return super().get_queryset()
