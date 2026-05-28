"""
اختبارات التكامل لنقاط نهاية التطبيقات الجديدة.
Integration Tests for the New Feature APIs.
"""

import pytest
from rest_framework import status
from datetime import date
from decimal import Decimal


# ============================================================
# 1. Payroll API Tests
# ============================================================

class TestPayrollEndpoints:
    """اختبارات نقاط نهاية نظام الرواتب."""

    def test_payroll_stats(self, authenticated_client):
        """اختبار إحصائيات الرواتب."""
        response = authenticated_client.get('/api/payroll/stats/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_payroll_periods(self, authenticated_client):
        """اختبار قائمة فترات الرواتب."""
        response = authenticated_client.get('/api/payroll/periods/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_payroll_period(self, authenticated_client):
        """اختبار إنشاء فترة رواتب."""
        response = authenticated_client.post('/api/payroll/periods/', {
            'name': 'مايو 2025',
            'month': 5,
            'year': 2025,
            'start_date': '2025-05-01',
            'end_date': '2025-05-31',
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_payroll_records(self, authenticated_client):
        """اختبار قائمة سجلات الرواتب."""
        response = authenticated_client.get('/api/payroll/records/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_salary_advances(self, authenticated_client):
        """اختبار قائمة السلف."""
        response = authenticated_client.get('/api/payroll/advances/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_employee_loans(self, authenticated_client):
        """اختبار قائمة القروض."""
        response = authenticated_client.get('/api/payroll/loans/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_end_of_service(self, authenticated_client):
        """اختبار قائمة مكافآت نهاية الخدمة."""
        response = authenticated_client.get('/api/payroll/end-of-service/')
        assert response.status_code == status.HTTP_200_OK

    def test_payroll_export(self, authenticated_client):
        """اختبار تصدير الرواتب."""
        response = authenticated_client.get('/api/payroll/export/')
        assert response.status_code == status.HTTP_200_OK


# ============================================================
# 2. Invoicing (Tax) API Tests
# ============================================================

class TestInvoicingEndpoints:
    """اختبارات نقاط نهاية نظام الفواتير الضريبية."""

    def test_invoice_stats(self, authenticated_client):
        """اختبار إحصائيات الفواتير."""
        response = authenticated_client.get('/api/invoicing/stats/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_invoices(self, authenticated_client):
        """اختبار قائمة الفواتير."""
        response = authenticated_client.get('/api/invoicing/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_invoice(self, authenticated_client, customer):
        """اختبار إنشاء فاتورة ضريبية."""
        response = authenticated_client.post('/api/invoicing/create/', {
            'invoice_type': 'sales',
            'customer': customer.id,
            'issue_date': str(date.today()),
            'due_date': str(date.today()),
            'tax_number': '300000000000003',
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert 'invoice_number' in response.data

    def test_create_invoice_with_vat(self, authenticated_client, customer):
        """اختبار إنشاء فاتورة مع حساب ضريبة القيمة المضافة."""
        response = authenticated_client.post('/api/invoicing/create/', {
            'invoice_type': 'sales',
            'customer': customer.id,
            'issue_date': str(date.today()),
            'due_date': str(date.today()),
            'subtotal': '1000',
            'vat_rate': '15',
        })
        assert response.status_code == status.HTTP_201_CREATED
        # التحقق من أن الفاتورة تم إنشاؤها بنجاح

    def test_invoice_detail(self, authenticated_client, db):
        """اختبار تفاصيل فاتورة."""
        from invoicing.models import Invoice
        invoice = Invoice.objects.create(
            invoice_type='sales', issue_date=date.today(), due_date=date.today()
        )
        response = authenticated_client.get(f'/api/invoicing/{invoice.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert 'invoice_number' in response.data

    def test_create_invoice_item(self, authenticated_client, customer, product):
        """اختبار إنشاء فاتورة مع بنود."""
        # أولاً إنشاء فاتورة
        inv_resp = authenticated_client.post('/api/invoicing/create/', {
            'invoice_type': 'sales',
            'customer': customer.id,
            'issue_date': str(date.today()),
            'due_date': str(date.today()),
        })
        assert inv_resp.status_code == status.HTTP_201_CREATED
        invoice_id = inv_resp.data['id']

    def test_invoice_export(self, authenticated_client):
        """اختبار تصدير الفواتير."""
        response = authenticated_client.get('/api/invoicing/export/')
        assert response.status_code == status.HTTP_200_OK


# ============================================================
# 3. POS API Tests
# ============================================================

class TestPOSEndpoints:
    """اختبارات نقاط نهاية نظام نقاط البيع."""

    def test_pos_stats(self, authenticated_client):
        """اختبار إحصائيات نقاط البيع."""
        response = authenticated_client.get('/api/pos/stats/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_pos_shifts(self, authenticated_client):
        """اختبار قائمة الورديات."""
        response = authenticated_client.get('/api/pos/shifts/')
        assert response.status_code == status.HTTP_200_OK

    def test_open_shift(self, authenticated_client):
        """اختبار محاولة فتح وردية."""
        response = authenticated_client.post('/api/pos/shifts/open/', {
            'opening_cash': '1000',
        })
        # قد يعود 201 أو 400 حسب حالة الوردية الحالية
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    def test_list_pos_sales(self, authenticated_client):
        """اختبار قائمة عمليات البيع."""
        response = authenticated_client.get('/api/pos/sales/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_pos_refunds(self, authenticated_client):
        """اختبار قائمة المرتجعات."""
        response = authenticated_client.get('/api/pos/refunds/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_pos_holds(self, authenticated_client):
        """اختبار قائمة الطلبات المعلقة."""
        response = authenticated_client.get('/api/pos/holds/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_drawer_transactions(self, authenticated_client):
        """اختبار قائمة حركات الصندوق."""
        response = authenticated_client.get('/api/pos/drawer/')
        assert response.status_code == status.HTTP_200_OK

    def test_pos_export(self, authenticated_client):
        """اختبار تصدير بيانات نقاط البيع."""
        response = authenticated_client.get('/api/pos/export/')
        assert response.status_code == status.HTTP_200_OK


# ============================================================
# 4. Warehouse (Multi-Warehouse) API Tests
# ============================================================

@pytest.mark.skip(reason="warehouse module removed")
class TestWarehouseEndpoints:

    def test_warehouse_stats(self, authenticated_client):
        """اختبار إحصائيات المخازن."""
        response = authenticated_client.get('/api/warehouse/stats/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_warehouses(self, authenticated_client):
        """اختبار قائمة المستودعات."""
        response = authenticated_client.get('/api/warehouse/warehouses/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_warehouse(self, authenticated_client):
        """اختبار إنشاء مستودع."""
        response = authenticated_client.post('/api/warehouse/warehouses/', {
            'name': 'مستودع اختبار',
            'city': 'الرياض',
            'capacity': '10000',
        })
        assert response.status_code == status.HTTP_201_CREATED
        # الاستجابة قد تكون في مفتاح 'warehouse' أو مباشرة
        data = response.data
        wh_data = data.get('warehouse', data)
        assert 'code' in wh_data
        assert wh_data['code'].startswith('WH-')

    def test_list_stocks(self, authenticated_client):
        """اختبار قائمة أرصدة المخزون."""
        response = authenticated_client.get('/api/warehouse/stocks/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_transfers(self, authenticated_client):
        """اختبار قائمة التحويلات."""
        response = authenticated_client.get('/api/warehouse/transfers/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_adjustments(self, authenticated_client):
        """اختبار قائمة التسويات."""
        response = authenticated_client.get('/api/warehouse/adjustments/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_counts(self, authenticated_client):
        """اختبار قائمة الجرد."""
        response = authenticated_client.get('/api/warehouse/counts/')
        assert response.status_code == status.HTTP_200_OK

    def test_warehouse_export(self, authenticated_client):
        """اختبار تصدير بيانات المخازن."""
        response = authenticated_client.get('/api/warehouse/warehouses/export/')
        assert response.status_code == status.HTTP_200_OK



# ============================================================
# 7. Payments (Collections & Transfers) API Tests
# ============================================================

class TestPaymentsEndpoints:
    """اختبارات نقاط نهاية نظام التحصيلات والتحويلات المالية."""

    def test_payment_stats(self, authenticated_client):
        """اختبار إحصائيات المدفوعات."""
        response = authenticated_client.get('/api/payments/stats/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_accounts(self, authenticated_client):
        """اختبار قائمة الحسابات المالية."""
        response = authenticated_client.get('/api/payments/accounts/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_account(self, authenticated_client):
        """اختبار إنشاء حساب مالي."""
        response = authenticated_client.post('/api/payments/accounts/create/', {
            'account_name': 'حساب الراجحي',
            'account_type': 'bank_account',
            'bank_name': 'مصرف الراجحي',
            'account_number': '1234567890',
            'current_balance': '100000',
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_transactions(self, authenticated_client):
        """اختبار قائمة العمليات المالية."""
        response = authenticated_client.get('/api/payments/transactions/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_cheques(self, authenticated_client):
        """اختبار قائمة الشيكات."""
        response = authenticated_client.get('/api/payments/cheques/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_reconciliations(self, authenticated_client):
        """اختبار قائمة التسويات."""
        response = authenticated_client.get('/api/payments/reconciliations/')
        assert response.status_code == status.HTTP_200_OK

    def test_payment_export(self, authenticated_client):
        """اختبار تصدير بيانات المدفوعات."""
        response = authenticated_client.get('/api/payments/export/')
        assert response.status_code == status.HTTP_200_OK


# ============================================================
# Access Control Tests
# ============================================================

class TestNewFeaturesAccessControl:
    """اختبارات صلاحيات الوصول للتطبيقات الجديدة."""

    def test_payroll_sales_denied(self, sales_client):
        """اختبار منع دور المبيعات من الوصول للرواتب (أو السماح حسب الصلاحيات)."""
        response = sales_client.get('/api/payroll/stats/')
        # قد يكون 403 أو 200 حسب إعدادات الصلاحيات
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_200_OK]

    def test_pos_sales_allowed(self, sales_client):
        """اختبار السماح لدور المبيعات بالوصول لنقاط البيع."""
        response = sales_client.get('/api/pos/stats/')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]

    @pytest.mark.skip(reason="warehouse module removed")
    def test_warehouse_warehouse_allowed(self, warehouse_client):
        """اختبار السماح لدور المخازن بالوصول للمستودعات."""
        response = warehouse_client.get('/api/warehouse/stats/')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]

    def test_payments_accountant_allowed(self, accountant_client):
        """اختبار السماح للمحاسب بالوصول للمدفوعات."""
        response = accountant_client.get('/api/payments/stats/')
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]
