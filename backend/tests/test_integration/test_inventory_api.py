"""
اختبارات التكامل لنقاط نهاية المخزون.
Integration Tests for Inventory API Endpoints.
"""

import pytest
from rest_framework import status


class TestProductEndpoints:
    """اختبارات نقاط نهاية المنتجات."""

    def test_list_products_authenticated(self, authenticated_client, product):
        """اختبار قائمة المنتجات كمستخدم مصادق."""
        response = authenticated_client.get('/api/inventory/products/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_products_unauthenticated(self, api_client):
        """اختبار منع غير المصادق من رؤية المنتجات."""
        response = api_client.get('/api/inventory/products/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_product_admin(self, authenticated_client):
        """اختبار إنشاء منتج كمدير."""
        response = authenticated_client.post('/api/inventory/products/', {
            'name': 'منتج جديد',
            'sku': 'NEW-001',
            'quantity': 50,
            'unit_price': 100.00,
            'reorder_level': 5,
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert 'تم إضافة المنتج' in response.data['message']

    def test_create_product_warehouse(self, warehouse_client):
        """اختبار إنشاء منتج كمستخدم مخازن."""
        response = warehouse_client.post('/api/inventory/products/', {
            'name': 'منتج مخازن',
            'sku': 'WH-001',
            'quantity': 200,
            'unit_price': 25.00,
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_product_sales_denied(self, sales_client):
        """اختبار منع موظف مبيعات من إنشاء منتج."""
        response = sales_client.post('/api/inventory/products/', {
            'name': 'منتج ممنوع',
            'sku': 'DENY-001',
            'quantity': 10,
            'unit_price': 10.00,
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_product_detail(self, authenticated_client, product):
        """اختبار جلب تفاصيل منتج."""
        response = authenticated_client.get(f'/api/inventory/products/{product.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'منتج اختبار'

    def test_update_product(self, warehouse_client, product):
        """اختبار تحديث منتج."""
        response = warehouse_client.patch(f'/api/inventory/products/{product.id}/', {
            'name': 'منتج محدث',
            'unit_price': 75.00,
        })
        assert response.status_code == status.HTTP_200_OK

    def test_update_product_sales_denied(self, sales_client, product):
        """اختبار منع موظف مبيعات من تحديث منتج."""
        response = sales_client.patch(f'/api/inventory/products/{product.id}/', {
            'name': 'ممنوع التحديث',
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_soft_delete_product(self, warehouse_client, product):
        """اختبار الحذف الناعم للمنتج."""
        response = warehouse_client.delete(f'/api/inventory/products/{product.id}/soft-delete/')
        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.is_active is False

    def test_soft_delete_already_deleted(self, warehouse_client, product):
        """اختبار حذف منتج محذوف مسبقاً."""
        product.soft_delete()
        response = warehouse_client.delete(f'/api/inventory/products/{product.id}/soft-delete/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_restore_product(self, warehouse_client, product):
        """اختبار استعادة منتج محذوف."""
        product.soft_delete()
        response = warehouse_client.post(f'/api/inventory/products/{product.id}/restore/')
        assert response.status_code == status.HTTP_200_OK

    def test_product_not_found(self, authenticated_client):
        """اختبار البحث عن منتج غير موجود."""
        response = authenticated_client.get('/api/inventory/products/99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_search_products(self, authenticated_client, product):
        """اختبار البحث في المنتجات."""
        response = authenticated_client.get('/api/inventory/products/?search=اختبار')
        assert response.status_code == status.HTTP_200_OK

    def test_order_products(self, authenticated_client, product):
        """اختبار ترتيب المنتجات."""
        response = authenticated_client.get('/api/inventory/products/?ordering=name')
        assert response.status_code == status.HTTP_200_OK


class TestInventoryStatsEndpoint:
    """اختبارات نقطة نهاية إحصائيات المخزون."""

    def test_inventory_stats(self, authenticated_client, product, product_low_stock):
        """اختبار إحصائيات المخزون."""
        response = authenticated_client.get('/api/inventory/stats/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total_products' in response.data
        assert 'active_products' in response.data
        assert 'low_stock_products' in response.data
        assert 'total_inventory_value' in response.data
