# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forward(apps, schema_editor):
    """
    converts "enabled" attribute to "disabled" in OpenVPN configurations,
    according to the change introduced in netjsonconfig 0.5.3
    (see https://github.com/openwisp/netjsonconfig/commit/7a152a344333665bbc9217011418ae39e8a1af81)
    TODO: delete this migration in future releases
    """
    if not schema_editor.connection.alias == 'default':
        return
    Config = apps.get_model('django_netjsonconfig', 'Config')
    Template = apps.get_model('django_netjsonconfig', 'Template')
    for model in [Config, Template]:
        for obj in model.objects.filter(config__contains='"openvpn"'):
            for vpn in obj.config['openvpn']:
                if 'enabled' in vpn:
                    vpn['disabled'] = not vpn['enabled']
                    del vpn['enabled']
            obj.save()


class Migration(migrations.Migration):
    dependencies = [
        ('django_netjsonconfig', '0017_openvpn_data_migration'),
    ]

    operations = [
        migrations.RunPython(forward, reverse_code=migrations.RunPython.noop),
    ]
