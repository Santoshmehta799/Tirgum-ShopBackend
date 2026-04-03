

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0018_alter_order_company_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='company_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),

    ]