import re

import django.core.validators
from django.db import migrations, models
import openwisp_utils.base
import openwisp_utils.utils


class Migration(migrations.Migration):

    dependencies = [
        ('django_netjsonconfig', '0037_config_context'),
    ]

    operations = [
        migrations.AddField(
            model_name='vpn',
            name='key',
            field=openwisp_utils.base.KeyField(db_index=True, default=openwisp_utils.utils.get_random_key, help_text=None, max_length=64, validators=[django.core.validators.RegexValidator(re.compile('^[^\\s/\\.]+$'), code='invalid', message='This value must not contain spaces, dots or slashes.')]),
        ),
    ]
