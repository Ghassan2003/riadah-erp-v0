"""
Payments app configuration for ERP System.
Manages payment accounts, financial transactions, cheques, and reconciliations.
"""

from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'
    verbose_name = 'المدفوعات'
