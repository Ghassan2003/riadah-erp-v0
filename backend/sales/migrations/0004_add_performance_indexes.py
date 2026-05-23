from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('sales', '0003_alter_salesorder_order_date'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='salesorder',
            index=models.Index(fields=['status', 'order_date'], name='sales_order_status_date_idx'),
        ),
    ]
