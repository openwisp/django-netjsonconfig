# -*- coding: utf-8 -*-

from django.db import migrations, models


def forward(apps, schema_editor):
    """
    converts "resolv_retry" attribute to string format in OpenVPN configurations,
    according to the change introduced in netjsonconfig 0.5.4
    (see https://github.com/openwisp/netjsonconfig/commit/904659962832b1cf097e34c4251a56e158a247ae)
    TODO: delete this migration in future releases
    """
    if not schema_editor.connection.alias == 'default':
        return
    Config = apps.get_model('django_netjsonconfig', 'Config')
    Template = apps.get_model('django_netjsonconfig', 'Template')
    Vpn = apps.get_model('django_netjsonconfig', 'Vpn')
    for model in [Config, Template, Vpn]:
        # find objects which have OpenVPN configurations containing the "resolv_retry" attribute
        queryset = model.objects.filter(config__contains='"openvpn"')\
                                .filter(config__contains='"resolv_retry"')
        for obj in queryset:
            for vpn in obj.config['openvpn']:
                if 'resolv_retry' in vpn:
                    vpn['resolv_retry'] = 'infinite' if vpn['resolv_retry'] else '0'
            obj.save()


class Migration(migrations.Migration):
    dependencies = [
        ('django_netjsonconfig', '0019_cleanup_model_options'),
    ]

    operations = [
        migrations.RunPython(forward, reverse_code=migrations.RunPython.noop),
    ]
