"""
اختبارات الوحدات البرمجية لنماذج المحاسبة.
Unit Tests for Accounting Models - Chart of Accounts, Journal Entries, Transactions.
"""

import pytest


class TestAccountModel:
    """اختبارات نموذج الحساب."""

    def test_create_account(self, account_asset):
        """اختبار إنشاء حساب."""
        assert account_asset.code == '1000'
        assert account_asset.name == 'الأصول'
        assert account_asset.account_type == 'asset'
        assert account_asset.current_balance == 0

    def test_account_str(self, account_asset):
        """اختبار التمثيل النصي."""
        assert '1000' in str(account_asset)
        assert 'الأصول' in str(account_asset)

    def test_unique_code(self, account_asset):
        """اختبار تفرد رمز الحساب."""
        from accounting.models import Account
        with pytest.raises(Exception):
            Account.objects.create(
                code='1000',
                name='حساب مكرر',
                account_type='asset',
            )

    def test_recalculate_balance_asset(self, db):
        """اختبار إعادة حساب رصيد حساب أصول."""
        from accounting.models import Account, JournalEntry, Transaction
        acc = Account.objects.create(code='1010', name='الصندوق', account_type='asset')
        acc2 = Account.objects.create(code='2000', name='الموردين', account_type='liability')
        entry = JournalEntry.objects.create(description='إيداع')
        Transaction.objects.create(
            journal_entry=entry, account=acc,
            transaction_type='debit', amount=1000,
        )
        Transaction.objects.create(
            journal_entry=entry, account=acc2,
            transaction_type='credit', amount=1000,
        )
        entry.post_entry()
        acc.recalculate_balance()
        assert acc.current_balance == 1000  # asset: debit - credit

    def test_recalculate_balance_income(self, db):
        """اختبار إعادة حساب رصيد حساب إيرادات."""
        from accounting.models import Account, JournalEntry, Transaction
        acc = Account.objects.create(code='4000', name='المبيعات', account_type='income')
        acc2 = Account.objects.create(code='1000', name='الصندوق', account_type='asset')
        entry = JournalEntry.objects.create(description='بيع')
        Transaction.objects.create(
            journal_entry=entry, account=acc,
            transaction_type='credit', amount=5000,
        )
        Transaction.objects.create(
            journal_entry=entry, account=acc2,
            transaction_type='debit', amount=5000,
        )
        entry.post_entry()
        acc.recalculate_balance()
        assert acc.current_balance == 5000  # income: credit - debit

    def test_get_children_balances(self, db):
        """اختبار حساب أرصدة الحسابات الفرعية."""
        from accounting.models import Account
        parent = Account.objects.create(code='1000', name='الأصول', account_type='asset')
        child1 = Account.objects.create(code='1010', name='الصندوق', account_type='asset', parent=parent)
        child1.current_balance = 5000
        child1.save()
        child2 = Account.objects.create(code='1020', name='البنك', account_type='asset', parent=parent)
        child2.current_balance = 10000
        child2.save()
        assert parent.get_children_balances() == 15000


class TestJournalEntryModel:
    """اختبارات نموذج قيد اليومية."""

    def test_create_journal_entry(self, db):
        """اختبار إنشاء قيد يومية."""
        from accounting.models import JournalEntry
        entry = JournalEntry.objects.create(
            description='قيد اختبار',
            entry_type='manual',
        )
        assert entry.entry_number.startswith('JE-')
        assert entry.status if hasattr(entry, 'status') else True
        assert entry.is_posted is False

    def test_entry_number_format(self, db):
        """اختبار تنسيق رقم القيد."""
        from accounting.models import JournalEntry
        entry = JournalEntry.objects.create(description='اختبار تنسيق')
        parts = entry.entry_number.split('-')
        assert parts[0] == 'JE'
        assert len(parts[1]) == 8
        assert len(parts[2]) == 4

    def test_validate_balance_equal(self, account_asset, account_revenue):
        """اختبار التحقق من توازن القيد."""
        from accounting.models import JournalEntry, Transaction
        entry = JournalEntry.objects.create(description='قيد متوازن')
        Transaction.objects.create(
            journal_entry=entry, account=account_asset,
            transaction_type='debit', amount=1000,
        )
        Transaction.objects.create(
            journal_entry=entry, account=account_revenue,
            transaction_type='credit', amount=1000,
        )
        # Should not raise
        entry.validate_balance()

    def test_validate_balance_unequal(self, account_asset, account_revenue):
        """اختبار كشف عدم توازن القيد."""
        from accounting.models import JournalEntry, Transaction
        entry = JournalEntry.objects.create(description='قيد غير متوازن')
        Transaction.objects.create(
            journal_entry=entry, account=account_asset,
            transaction_type='debit', amount=1000,
        )
        Transaction.objects.create(
            journal_entry=entry, account=account_revenue,
            transaction_type='credit', amount=500,
        )
        with pytest.raises(ValueError):
            entry.validate_balance()

    def test_validate_empty_transactions(self, db):
        """اختبار كشف قيد بدون حركات."""
        from accounting.models import JournalEntry
        entry = JournalEntry.objects.create(description='قيد فارغ')
        with pytest.raises(ValueError):
            entry.validate_balance()

    def test_post_entry(self, account_asset, account_revenue):
        """اختبار ترحيل القيد."""
        from accounting.models import JournalEntry, Transaction
        entry = JournalEntry.objects.create(description='قيد ترحيل')
        Transaction.objects.create(
            journal_entry=entry, account=account_asset,
            transaction_type='debit', amount=5000,
        )
        Transaction.objects.create(
            journal_entry=entry, account=account_revenue,
            transaction_type='credit', amount=5000,
        )
        entry.post_entry()
        assert entry.is_posted is True
        account_asset.refresh_from_db()
        account_revenue.refresh_from_db()
        assert account_asset.current_balance == 5000  # asset: debit+
        assert account_revenue.current_balance == 5000  # income: credit+

    def test_post_already_posted(self, account_asset, account_revenue):
        """اختبار محاولة ترحيل قيد مرحّل مسبقاً."""
        from accounting.models import JournalEntry, Transaction
        entry = JournalEntry.objects.create(description='قيد')
        Transaction.objects.create(
            journal_entry=entry, account=account_asset,
            transaction_type='debit', amount=1000,
        )
        Transaction.objects.create(
            journal_entry=entry, account=account_revenue,
            transaction_type='credit', amount=1000,
        )
        entry.post_entry()
        with pytest.raises(ValueError):
            entry.post_entry()

    def test_reverse_entry(self, account_asset, account_revenue):
        """اختبار إلغاء ترحيل القيد."""
        from accounting.models import JournalEntry, Transaction
        entry = JournalEntry.objects.create(description='قيد إلغاء')
        Transaction.objects.create(
            journal_entry=entry, account=account_asset,
            transaction_type='debit', amount=3000,
        )
        Transaction.objects.create(
            journal_entry=entry, account=account_revenue,
            transaction_type='credit', amount=3000,
        )
        entry.post_entry()
        account_asset.refresh_from_db()
        balance_after_post = account_asset.current_balance

        entry.reverse_entry()
        account_asset.refresh_from_db()
        assert entry.is_posted is False
        assert account_asset.current_balance == balance_after_post - 3000

    def test_reverse_unposted_entry(self, account_asset, account_revenue):
        """اختبار إلغاء قيد غير مرحّل."""
        from accounting.models import JournalEntry
        entry = JournalEntry.objects.create(description='قيد')
        with pytest.raises(ValueError):
            entry.reverse_entry()


class TestTransactionModel:
    """اختبارات نموذج الحركة المالية."""

    def test_create_transaction(self, account_asset):
        """اختبار إنشاء حركة مالية."""
        from accounting.models import JournalEntry, Transaction
        entry = JournalEntry.objects.create(description='اختبار')
        txn = Transaction.objects.create(
            journal_entry=entry,
            account=account_asset,
            transaction_type='debit',
            amount=1500,
            description='مدين',
        )
        assert txn.transaction_type == 'debit'
        assert float(txn.amount) == 1500.00

    def test_transaction_str(self, account_asset):
        """اختبار التمثيل النصي للحركة."""
        from accounting.models import JournalEntry, Transaction
        entry = JournalEntry.objects.create(description='اختبار نصي')
        txn = Transaction.objects.create(
            journal_entry=entry,
            account=account_asset,
            transaction_type='credit',
            amount=2000,
        )
        assert entry.entry_number in str(txn)
        assert '1000' in str(txn)
