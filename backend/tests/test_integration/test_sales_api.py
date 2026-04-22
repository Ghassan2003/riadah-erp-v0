"""
اختبارات التكامل لنقاط نهاية المبيعات.
Integration Tests for Sales API Endpoints.
"""

import pytest
from rest_framework import status


class TestCustomerEndpoints:
    """اختبارات نقاط نهاية العملاء."""

    def test_list_customers(self, authenticated_client, customer):
        """اختبار قائمة العملاء."""
        response = authenticated_client.get('/api/sales/customers/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_customer(self, sales_client):
        """اختبار إنشاء عميل."""
        response = sales_client.post('/api/sales/customers/', {
            'name': 'عميل جديد',
            'email': 'new@customer.com',
            'phone': '0559876543',
            'address': 'جدة، المملكة العربية السعودية',
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_get_customer_detail(self, authenticated_client, customer):
        """اختبار جلب تفاصيل عميل."""
        response = authenticated_client.get(f'/api/sales/customers/{customer.id}/')
        assert response.status_code == status.HTTP_200_OK

    def test_update_customer(self, sales_client, customer):
        """اختبار تحديث بيانات عميل."""
        response = sales_client.patch(f'/api/sales/customers/{customer.id}/', {
            'name': 'عميل محدث',
            'phone': '0551111222',
        })
        assert response.status_code == status.HTTP_200_OK

    def test_soft_delete_customer(self, authenticated_client, customer):
        """اختبار حذف عميل (مدير فقط)."""
        response = authenticated_client.delete(f'/api/sales/customers/{customer.id}/soft-delete/')
        assert response.status_code == status.HTTP_200_OK
        customer.refresh_from_db()
        assert customer.is_active is False


class TestSalesOrderEndpoints:
    """اختبارات نقاط نهاية أوامر البيع."""

    def test_list_orders(self, authenticated_client):
        """اختبار قائمة أوامر البيع."""
        response = authenticated_client.get('/api/sales/orders/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_order(self, sales_client, customer, product):
        """اختبار إنشاء أمر بيع."""
        response = sales_client.post('/api/sales/orders/create/', {
            'customer': customer.id,
            'items': [
                {
                    'product': product.id,
                    'quantity': 5,
                }
            ],
            'notes': 'اختبار إنشاء أمر',
        }, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_order_detail(self, authenticated_client, admin_user, customer):
        """اختبار جلب تفاصيل أمر بيع."""
        from sales.models import SalesOrder
        order = SalesOrder.objects.create(customer=customer, created_by=admin_user)
        response = authenticated_client.get(f'/api/sales/orders/{order.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['order_number'] == order.order_number

    def test_sales_stats(self, authenticated_client):
        """اختبار إحصائيات المبيعات."""
        response = authenticated_client.get('/api/sales/stats/')
        assert response.status_code == status.HTTP_200_OK


class TestSalesWorkflow:
    """اختبارات سير عمل المبيعات المتكامل."""

    def test_order_status_change_draft_to_confirmed(self, authenticated_client, admin_user, customer, product):
        """اختبار تغيير حالة أمر البيع من مسودة إلى مؤكد."""
        from sales.models import SalesOrder, SalesOrderItem
        order = SalesOrder.objects.create(customer=customer, created_by=admin_user)
        SalesOrderItem.objects.create(
            order=order, product=product, quantity=5, unit_price=50.00,
        )
        response = authenticated_client.post(
            f'/api/sales/orders/{order.id}/change-status/',
            {'status': 'confirmed'}
        )
        assert response.status_code == status.HTTP_200_OK
        order.refresh_from_db()
        assert order.status == 'confirmed'

    def test_confirm_order_deducts_inventory(self, authenticated_client, admin_user, customer, product):
        """اختبار أن تأكيد الأمر يخصم من المخزون."""
        from sales.models import SalesOrder, SalesOrderItem
        initial_qty = product.quantity
        order = SalesOrder.objects.create(customer=customer, created_by=admin_user)
        SalesOrderItem.objects.create(
            order=order, product=product, quantity=10, unit_price=50.00,
        )
        response = authenticated_client.post(
            f'/api/sales/orders/{order.id}/change-status/',
            {'status': 'confirmed'}
        )
        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.quantity == initial_qty - 10

    def test_cancel_confirmed_order_restores_stock(self, authenticated_client, admin_user, customer, product):
        """اختبار أن إلغاء أمر مؤكد يعيد المخزون."""
        from sales.models import SalesOrder, SalesOrderItem
        initial_qty = product.quantity

        order = SalesOrder.objects.create(customer=customer, created_by=admin_user)
        SalesOrderItem.objects.create(
            order=order, product=product, quantity=5, unit_price=50.00,
        )
        # Confirm
        authenticated_client.post(
            f'/api/sales/orders/{order.id}/change-status/',
            {'status': 'confirmed'}
        )
        product.refresh_from_db()
        qty_after_confirm = product.quantity

        # Cancel
        response = authenticated_client.post(
            f'/api/sales/orders/{order.id}/change-status/',
            {'status': 'cancelled'}
        )
        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.quantity == qty_after_confirm + 5

    def test_full_order_lifecycle(self, authenticated_client, customer, product, admin_user):
        """اختبار دورة حياة كاملة لأمر البيع."""
        from sales.models import SalesOrder, SalesOrderItem
        initial_qty = product.quantity

        # 1. إنشاء أمر مباشرة
        order = SalesOrder.objects.create(customer=customer, created_by=admin_user)
        SalesOrderItem.objects.create(
            order=order, product=product, quantity=10, unit_price=50.00,
        )

        # 2. تأكيد
        response = authenticated_client.post(
            f'/api/sales/orders/{order.id}/change-status/',
            {'status': 'confirmed'}
        )
        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.quantity == initial_qty - 10

        # 3. شحن
        response = authenticated_client.post(
            f'/api/sales/orders/{order.id}/change-status/',
            {'status': 'shipped'}
        )
        assert response.status_code == status.HTTP_200_OK

        # 4. تسليم
        response = authenticated_client.post(
            f'/api/sales/orders/{order.id}/change-status/',
            {'status': 'delivered'}
        )
        assert response.status_code == status.HTTP_200_OK
