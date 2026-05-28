"""
اختبارات التكامل لنقاط نهاية المستودعات والمدفوعات.
Integration Tests for Warehouse and Payments APIs.
"""

import pytest
from rest_framework import status


# =============================================
# اختبارات نقاط نهاية المستودعات (Warehouse)
# =============================================


@pytest.mark.skip(reason="warehouse module removed")
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


@pytest.mark.skip(reason="warehouse module removed")
class TestWarehouseStockEndpoints:
    """اختبارات نقاط نهاية أرصدة المخزون."""

    def test_list_stocks(self, authenticated_client):
        """اختبار قائمة أرصدة المخزون."""
        response = authenticated_client.get('/api/warehouse/stocks/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.skip(reason="warehouse module removed")
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


@pytest.mark.skip(reason="warehouse module removed")
class TestStockAdjustmentEndpoints:
    """اختبارات نقاط نهاية تسويات المخزون."""

    def test_list_adjustments(self, authenticated_client):
        """اختبار قائمة تسويات المخزون."""
        response = authenticated_client.get('/api/warehouse/adjustments/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.skip(reason="warehouse module removed")
class TestStockCountEndpoints:
    """اختبارات نقاط نهاية جرد المخزون."""

    def test_list_counts(self, authenticated_client):
        """اختبار قائمة جرد المخزون."""
        response = authenticated_client.get('/api/warehouse/counts/')
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
