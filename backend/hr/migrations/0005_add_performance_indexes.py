from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('hr', '0004_alter_attendance_unique_together_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='employee',
            index=models.Index(fields=['department', 'status'], name='hr_emp_dept_status_idx'),
        ),
        migrations.AddIndex(
            model_name='attendance',
            index=models.Index(fields=['employee', 'date'], name='hr_attendance_emp_date_idx'),
        ),
    ]
