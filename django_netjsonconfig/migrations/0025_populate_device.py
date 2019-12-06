# -*- coding: utf-8 -*-

from django.db import migrations, models


def forward(apps, schema_editor):
    """
    Creates a Device record for each existing Config
    TODO: delete this migration in future releases
    """
    if not schema_editor.connection.alias == 'default':
        return
    Device = apps.get_model('django_netjsonconfig', 'Device')
    Config = apps.get_model('django_netjsonconfig', 'Config')

    for config in Config.objects.all():
        device = Device(id=config.id,
                        name=config.name,
                        mac_address=config.mac_address,
                        key=config.key,
                        created=config.created,
                        modified=config.modified)
        device.full_clean()
        device.save()
        config.device = device
        config.save()


class Migration(migrations.Migration):
    dependencies = [
        ('django_netjsonconfig', '0024_add_device_model'),
    ]

    operations = [
        migrations.RunPython(forward, reverse_code=migrations.RunPython.noop),
    ]
