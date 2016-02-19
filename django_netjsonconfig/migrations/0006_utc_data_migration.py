# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forwards(apps, schema_editor):
    """
    converts "Coordinated Universal Time" to "UTC"
    """
    if not schema_editor.connection.alias == 'default':
        return
    Config = apps.get_model('django_netjsonconfig', 'Config')
    Template = apps.get_model('django_netjsonconfig', 'Template')
    old_value = 'Coordinated Universal Time'
    new_value = 'UTC'
    for model in [Config, Template]:
        for obj in model.objects.filter(config__contains=old_value):
            obj.config['general']['timezone'] = new_value
            obj.full_clean()
            obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('django_netjsonconfig', '0005_template_default'),
    ]

    operations = [
        migrations.RunPython(forwards),
    ]
