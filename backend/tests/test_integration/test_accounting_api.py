"""
اختبارات التكامل لنقاط نهاية المحاسبة.
Integration Tests for Accounting API Endpoints.
"""

import pytest
from rest_framework import status


class TestAccountEndpoints:
    """اختبارات نقاط نهاية الحسابات."""

    def test_list_accounts(self, accountant_client, account_asset):
        """اختبار قائمة الحسابات."""
        response = accountant_client.get('/api/accounting/accounts/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_account(self, accountant_client):
        """اختبار إنشاء حساب."""
        response = accountant_client.post('/api/accounting/accounts/create/', {
            'code': '2000',
            'name': 'الموردين',
            'account_type': 'liability',
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_get_account_detail(self, accountant_client, account_asset):
        """اختبار جلب تفاصيل حساب."""
        response = accountant_client.get(f'/api/accounting/accounts/{account_asset.id}/')
        assert response.status_code == status.HTTP_200_OK

    def test_update_account(self, accountant_client, account_asset):
        """اختبار تحديث حساب."""
        response = accountant_client.put(
            f'/api/accounting/accounts/{account_asset.id}/update/',
            {'name': 'الأصول المتداولة', 'account_type': 'asset'}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_sales_cannot_create_account(self, sales_client):
        """اختبار منع موظف مبيعات من إنشاء حساب."""
        response = sales_client.post('/api/accounting/accounts/create/', {
            'code': '9999',
            'name': 'ممنوع',
            'account_type': 'asset',
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestJournalEntryEndpoints:
    """اختبارات نقاط نهاية قيود اليومية."""

    def test_create_journal_entry(self, accountant_client, account_asset, account_revenue):
        """اختبار إنشاء قيد يومية."""
        response = accountant_client.post('/api/accounting/entries/create/', {
            'description': 'قيد اختبار',
            'entry_type': 'manual',
            'transactions': [
                {
                    'account': account_asset.id,
                    'transaction_type': 'debit',
                    'amount': 5000,
                    'description': 'مدين',
                },
                {
                    'account': account_revenue.id,
                    'transaction_type': 'credit',
                    'amount': 5000,
                    'description': 'دائن',
                },
            ],
        }, format='json')
        if response.status_code != 201:
            print(f'ERROR: {response.data}')
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_journal_entries(self, accountant_client):
        """اختبار قائمة قيود اليومية."""
        response = accountant_client.get('/api/accounting/entries/')
        assert response.status_code == status.HTTP_200_OK

    def test_post_entry(self, accountant_client, account_asset, account_revenue):
        """اختبار ترحيل قيد."""
        from accounting.models import JournalEntry, Transaction
        entry = JournalEntry.objects.create(description='قيد للترحيل')
        Transaction.objects.create(
            journal_entry=entry, account=account_asset,
            transaction_type='debit', amount=3000,
        )
        Transaction.objects.create(
            journal_entry=entry, account=account_revenue,
            transaction_type='credit', amount=3000,
        )
        response = accountant_client.post(f'/api/accounting/entries/{entry.id}/post/')
        assert response.status_code == status.HTTP_200_OK
        entry.refresh_from_db()
        assert entry.is_posted is True

    def test_reverse_entry(self, accountant_client, account_asset, account_revenue):
        """اختبار إلغاء ترحيل قيد."""
        from accounting.models import JournalEntry, Transaction
        entry = JournalEntry.objects.create(description='قيد للإلغاء')
        Transaction.objects.create(
            journal_entry=entry, account=account_asset,
            transaction_type='debit', amount=2000,
        )
        Transaction.objects.create(
            journal_entry=entry, account=account_revenue,
            transaction_type='credit', amount=2000,
        )
        entry.post_entry()

        response = accountant_client.post(f'/api/accounting/entries/{entry.id}/reverse/')
        assert response.status_code == status.HTTP_200_OK
        entry.refresh_from_db()
        assert entry.is_posted is False

    def test_accounting_stats(self, accountant_client):
        """اختبار إحصائيات المحاسبة."""
        response = accountant_client.get('/api/accounting/stats/')
        assert response.status_code == status.HTTP_200_OK


class TestDoubleEntryAccounting:
    """اختبارات نظام القيد المزدوج المتكامل."""

    def test_full_double_entry_workflow(self, accountant_client):
        """اختبار سير عمل كامل للقيد المزدوج."""
        # 1. إنشاء حسابات
        cash_resp = accountant_client.post('/api/accounting/accounts/create/', {
            'code': '1010', 'name': 'الصندوق', 'account_type': 'asset',
        })
        sales_acc_resp = accountant_client.post('/api/accounting/accounts/create/', {
            'code': '4010', 'name': 'المبيعات', 'account_type': 'income',
        })
        cash_id = cash_resp.data['account']['id']
        sales_id = sales_acc_resp.data['account']['id']

        # 2. إنشاء قيد
        entry_resp = accountant_client.post('/api/accounting/entries/create/', {
            'description': 'بيع نقدي',
            'entry_type': 'sale',
            'transactions': [
                {'account': cash_id, 'transaction_type': 'debit', 'amount': 10000},
                {'account': sales_id, 'transaction_type': 'credit', 'amount': 10000},
            ],
        }, format='json')
        entry_id = entry_resp.data['entry']['id']

        # 3. ترحيل القيد
        post_resp = accountant_client.post(f'/api/accounting/entries/{entry_id}/post/')
        assert post_resp.status_code == status.HTTP_200_OK

        # 4. التحقق من أرصدة الحسابات
        cash_detail = accountant_client.get(f'/api/accounting/accounts/{cash_id}/')
        assert float(cash_detail.data['current_balance']) == 10000

        # 5. إلغاء الترحيل
        reverse_resp = accountant_client.post(f'/api/accounting/entries/{entry_id}/reverse/')
        assert reverse_resp.status_code == status.HTTP_200_OK

        cash_detail = accountant_client.get(f'/api/accounting/accounts/{cash_id}/')
        assert float(cash_detail.data['current_balance']) == 0
