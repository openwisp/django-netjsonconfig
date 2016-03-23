# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from netjsonconfig.backends.openwrt.schema import DEFAULT_FILE_MODE


def forwards(apps, schema_editor):
    """
    adds "mode" property to "files" section in configurations, if missing
    """
    if not schema_editor.connection.alias == 'default':
        return
    Config = apps.get_model('django_netjsonconfig', 'Config')
    Template = apps.get_model('django_netjsonconfig', 'Template')
    for model in [Config, Template]:
        for obj in model.objects.filter(config__contains='"files"'):
            for f in obj.config['files']:
                if 'mode' not in f:
                    f['mode'] = DEFAULT_FILE_MODE
            obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('django_netjsonconfig', '0006_utc_data_migration'),
    ]

    operations = [
        migrations.RunPython(forwards),
    ]
