from django.db import migrations


def forward(apps, schema_editor):
    """
    Updates default value of context field
    """
    if not schema_editor.connection.alias == 'default':
        return
    Config = apps.get_model('django_netjsonconfig', 'Config')

    for config in Config.objects.filter(context__isnull=True):
        config.context = {}
        config.save()


class Migration(migrations.Migration):

    dependencies = [
        ('django_netjsonconfig', '0040_update_context'),
    ]

    operations = [
        migrations.RunPython(forward, reverse_code=migrations.RunPython.noop),
    ]
