"""
اختبارات التكامل لنقاط نهاية المستودعات والأصول والعقود والمدفوعات.
Integration Tests for Warehouse, Assets, Contracts, and Payments APIs.
"""

import pytest
from rest_framework import status


# =============================================
# اختبارات نقاط نهاية المستودعات (Warehouse)
# =============================================


class TestWarehouseEndpoints:
    """اختبارات نقاط نهاية المستودعات."""

    def test_warehouse_stats(self, authenticated_client):
        """اختبار إحصائيات المستودعات."""
        response = authenticated_client.get('/api/warehouse/stats/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_warehouses(self, authenticated_client):
        """اختبار قائمة المستودعات."""
        response = authenticated_client.get('/api/warehouse/warehouses/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_warehouse(self, authenticated_client):
        """اختبار إنشاء مستودع جديد."""
        response = authenticated_client.post('/api/warehouse/warehouses/', {
            'name': 'مستودع اختبار',
            'address': 'الرياض، حي الصناعة',
            'city': 'الرياض',
            'capacity': '5000.00',
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_warehouse_non_admin_denied(self, sales_client):
        """اختبار منع غير المدير من إنشاء مستودع."""
        response = sales_client.post('/api/warehouse/warehouses/', {
            'name': 'مستودع ممنوع',
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestWarehouseStockEndpoints:
    """اختبارات نقاط نهاية أرصدة المخزون."""

    def test_list_stocks(self, authenticated_client):
        """اختبار قائمة أرصدة المخزون."""
        response = authenticated_client.get('/api/warehouse/stocks/')
        assert response.status_code == status.HTTP_200_OK


class TestStockTransferEndpoints:
    """اختبارات نقاط نهاية تحويلات المخزون."""

    def test_list_transfers(self, authenticated_client):
        """اختبار قائمة تحويلات المخزون."""
        response = authenticated_client.get('/api/warehouse/transfers/')
        assert response.status_code == status.HTTP_200_OK

    def test_transfer_non_admin_denied(self, sales_client):
        """اختبار منع غير المدير من إنشاء تحويل مخزون."""
        response = sales_client.post('/api/warehouse/transfers/create/', {
            'from_warehouse': 1,
            'to_warehouse': 2,
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestStockAdjustmentEndpoints:
    """اختبارات نقاط نهاية تسويات المخزون."""

    def test_list_adjustments(self, authenticated_client):
        """اختبار قائمة تسويات المخزون."""
        response = authenticated_client.get('/api/warehouse/adjustments/')
        assert response.status_code == status.HTTP_200_OK


class TestStockCountEndpoints:
    """اختبارات نقاط نهاية جرد المخزون."""

    def test_list_counts(self, authenticated_client):
        """اختبار قائمة جرد المخزون."""
        response = authenticated_client.get('/api/warehouse/counts/')
        assert response.status_code == status.HTTP_200_OK


# =============================================
# اختبارات نقاط نهاية الأصول الثابتة (Assets)
# =============================================


class TestAssetEndpoints:
    """اختبارات نقاط نهاية الأصول."""

    def test_asset_stats(self, authenticated_client):
        """اختبار إحصائيات الأصول."""
        response = authenticated_client.get('/api/assets/stats/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_categories(self, authenticated_client):
        """اختبار قائمة تصنيفات الأصول."""
        response = authenticated_client.get('/api/assets/categories/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_assets(self, authenticated_client):
        """اختبار قائمة الأصول الثابتة."""
        response = authenticated_client.get('/api/assets/assets/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_asset_category(self, authenticated_client):
        """اختبار إنشاء تصنيف أصل جديد."""
        response = authenticated_client.post('/api/assets/categories/', {
            'name': 'تصنيف اختبار',
            'name_en': 'Test Category',
            'useful_life_years': 5,
            'depreciation_method': 'straight_line',
            'salvage_value_rate': '10.00',
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_fixed_asset(self, authenticated_client):
        """اختبار إنشاء أصل ثابت جديد."""
        response = authenticated_client.post('/api/assets/assets/', {
            'name': 'جهاز اختبار',
            'purchase_date': '2024-06-15',
            'purchase_price': '5000.00',
            'useful_life_months': 60,
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_asset_non_admin_denied(self, sales_client):
        """اختبار منع غير المدير من إنشاء أصل."""
        response = sales_client.post('/api/assets/assets/', {
            'name': 'أصل ممنوع',
            'purchase_date': '2024-01-01',
            'purchase_price': '1000.00',
            'useful_life_months': 12,
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAssetTransferEndpoints:
    """اختبارات نقاط نهاية نقل الأصول."""

    def test_list_asset_transfers(self, authenticated_client):
        """اختبار قائمة نقل الأصول."""
        response = authenticated_client.get('/api/assets/transfers/')
        assert response.status_code == status.HTTP_200_OK


class TestAssetMaintenanceEndpoints:
    """اختبارات نقاط نهاية صيانة الأصول."""

    def test_list_maintenances(self, authenticated_client):
        """اختبار قائمة صيانات الأصول."""
        response = authenticated_client.get('/api/assets/maintenances/')
        assert response.status_code == status.HTTP_200_OK


class TestAssetDisposalEndpoints:
    """اختبارات نقاط نهاية تخريد الأصول."""

    def test_list_disposals(self, authenticated_client):
        """اختبار قائمة تخريدات الأصول."""
        response = authenticated_client.get('/api/assets/disposals/')
        assert response.status_code == status.HTTP_200_OK


# =============================================
# اختبارات نقاط نهاية العقود (Contracts)
# =============================================


class TestContractEndpoints:
    """اختبارات نقاط نهاية العقود."""

    def test_contract_stats(self, authenticated_client):
        """اختبار إحصائيات العقود."""
        response = authenticated_client.get('/api/contracts/stats/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_contracts(self, authenticated_client):
        """اختبار قائمة العقود."""
        response = authenticated_client.get('/api/contracts/contracts/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_contract(self, authenticated_client):
        """اختبار إنشاء عقد جديد."""
        response = authenticated_client.post('/api/contracts/contracts/', {
            'title': 'عقد اختبار',
            'contract_type': 'service',
            'start_date': '2024-06-01',
            'end_date': '2025-05-31',
            'value': '50000.00',
            'currency': 'SAR',
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_contract_non_admin_denied(self, sales_client):
        """اختبار منع غير المدير من إنشاء عقد."""
        response = sales_client.post('/api/contracts/contracts/', {
            'title': 'عقد ممنوع',
            'contract_type': 'service',
            'start_date': '2024-01-01',
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestContractMilestoneEndpoints:
    """اختبارات نقاط نهاية مراحل العقود."""

    def test_list_milestones(self, authenticated_client):
        """اختبار قائمة مراحل العقود."""
        response = authenticated_client.get('/api/contracts/milestones/')
        assert response.status_code == status.HTTP_200_OK


class TestContractPaymentEndpoints:
    """اختبارات نقاط نهاية دفعات العقود."""

    def test_list_contract_payments(self, authenticated_client):
        """اختبار قائمة دفعات العقود."""
        response = authenticated_client.get('/api/contracts/payments/')
        assert response.status_code == status.HTTP_200_OK


# =============================================
# اختبارات نقاط نهاية المدفوعات (Payments)
# =============================================


class TestPaymentAccountEndpoints:
    """اختبارات نقاط نهاية الحسابات المالية."""

    def test_payment_stats(self, authenticated_client):
        """اختبار إحصائيات المدفوعات."""
        response = authenticated_client.get('/api/payments/stats/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_accounts(self, authenticated_client):
        """اختبار قائمة الحسابات المالية."""
        response = authenticated_client.get('/api/payments/accounts/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_payment_account(self, authenticated_client):
        """اختبار إنشاء حساب مالي جديد."""
        response = authenticated_client.post('/api/payments/accounts/create/', {
            'account_name': 'حساب اختبار',
            'account_type': 'bank_account',
            'bank_name': 'البنك الأهلي',
            'account_number': '1234567890',
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_payment_account_non_admin_denied(self, sales_client):
        """اختبار منع غير المدير من إنشاء حساب مالي."""
        response = sales_client.post('/api/payments/accounts/create/', {
            'account_name': 'حساب ممنوع',
            'account_type': 'cash_box',
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestFinancialTransactionEndpoints:
    """اختبارات نقاط نهاية العمليات المالية."""

    def test_list_transactions(self, authenticated_client):
        """اختبار قائمة العمليات المالية."""
        response = authenticated_client.get('/api/payments/transactions/')
        assert response.status_code == status.HTTP_200_OK

    def test_transaction_non_admin_denied(self, sales_client):
        """اختبار منع غير المدير من إنشاء عملية مالية."""
        response = sales_client.post('/api/payments/transactions/create/', {
            'transaction_type': 'receipt',
            'amount': '1000.00',
            'transaction_date': '2024-06-15',
            'payment_method': 'cash',
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestChequeEndpoints:
    """اختبارات نقاط نهاية الشيكات."""

    def test_list_cheques(self, authenticated_client):
        """اختبار قائمة الشيكات."""
        response = authenticated_client.get('/api/payments/cheques/')
        assert response.status_code == status.HTTP_200_OK


class TestReconciliationEndpoints:
    """اختبارات نقاط نهاية التسويات."""

    def test_list_reconciliations(self, authenticated_client):
        """اختبار قائمة التسويات."""
        response = authenticated_client.get('/api/payments/reconciliations/')
        assert response.status_code == status.HTTP_200_OK
