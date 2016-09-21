# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import six
from django.db import migrations, models


def forward(apps, schema_editor):
    """
    converts openvpn configuration to newer format
    """
    if not schema_editor.connection.alias == 'default':
        return
    Config = apps.get_model('django_netjsonconfig', 'Config')
    Template = apps.get_model('django_netjsonconfig', 'Template')
    for model in [Config, Template]:
        for obj in model.objects.filter(config__contains='"openvpn"'):
            for v in obj.config['openvpn']:
                if 'config_name' in v:
                    del v['config_name']
                if 'config_value' in v:
                    v['name'] = v['config_value']
                    del v['config_value']
                v['enabled'] = True
                if 'remote' in v and isinstance(v['remote'], six.string_types):
                    parts = v['remote'].split()
                    v['remote'] = [{'host': parts[0], 'port': int(parts[1])}]
                if 'mode' not in v:
                    if 'client' in v or 'tls_client' in v:
                        v['mode'] = 'p2p'
                    else:
                        v['mode'] = 'server'
                if 'proto' not in v:
                    v['proto'] = 'udp'
                if 'dev' not in v:
                    v['dev'] = v['name']
                for key, value in v.items():
                    if value == '1':
                        v[key] = True
                    elif value == '0':
                        v[key] = True
                if isinstance(v.get('up_delay'), bool):
                    v['up_delay'] = int(v['up_delay'])
                if isinstance(v.get('down_delay'), bool):
                    v['down_delay'] = int(v['down_delay'])
                if v.get('resolv_retry') == 'infinite':
                    v['resolv_retry'] = True
                elif 'resolv_retry' in v:
                    v['resolv_retry'] = False
            obj.save()


def backward(apps, schema_editor):
    """
    rolls back to old format
    """
    if not schema_editor.connection.alias == 'default':
        return
    Config = apps.get_model('django_netjsonconfig', 'Config')
    Template = apps.get_model('django_netjsonconfig', 'Template')
    for model in [Config, Template]:
        for obj in model.objects.filter(config__contains='"openvpn"'):
            for v in obj.config['openvpn']:
                v['config_name'] = 'openvpn'
                if 'name' in v:
                    v['config_value'] = v['name']
                    del v['name']
                if 'remote' in v and isinstance(v['remote'], list):
                    v['remote'] = '{host} {port}'.format(**v['remote'][0])
            obj.save()


class Migration(migrations.Migration):
    dependencies = [
        ('django_x509', '0002_certificate'),
        ('django_netjsonconfig', '0008_vpn_integration'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
