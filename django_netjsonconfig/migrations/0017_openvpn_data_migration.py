# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forward(apps, schema_editor):
    """
    corrects wrong openvpn "mode"
    TODO: delete this migration in future releases
    """
    if not schema_editor.connection.alias == 'default':
        return
    Config = apps.get_model('django_netjsonconfig', 'Config')
    Template = apps.get_model('django_netjsonconfig', 'Template')
    for model in [Config, Template]:
        for obj in model.objects.filter(config__contains='"openvpn"'):
            for v in obj.config['openvpn']:
                if 'mode' in v and v['mode'] == 'client':
                    v['mode'] = 'p2p'
            obj.save()


class Migration(migrations.Migration):
    dependencies = [
        ('django_netjsonconfig', '0016_vpn_dh'),
    ]

    operations = [
        migrations.RunPython(forward, reverse_code=migrations.RunPython.noop),
    ]
