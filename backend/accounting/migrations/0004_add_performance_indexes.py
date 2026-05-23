from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounting', '0003_alter_journalentry_entry_date'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['journal_entry', 'transaction_type'], name='acct_txn_entry_type_idx'),
        ),
    ]
