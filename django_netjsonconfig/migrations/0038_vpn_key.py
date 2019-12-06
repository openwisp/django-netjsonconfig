import re

import django.core.validators
import django_netjsonconfig.utils
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_netjsonconfig', '0037_config_context'),
    ]

    operations = [
        migrations.AddField(
            model_name='vpn',
            name='key',
            field=models.CharField(db_index=True, default=django_netjsonconfig.utils.get_random_key, max_length=64, validators=[django.core.validators.RegexValidator(re.compile('^[^\\s/\\.]+$'), code='invalid', message='Key must not contain spaces, dots or slashes.')]),
        ),
    ]
