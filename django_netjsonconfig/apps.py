from django.apps import AppConfig


class NetJsonConfigApp(AppConfig):
    name = 'django_netjsonconfig'
    label = 'netjsonconfig'

    def ready(self):
        """
        * m2m validation before templates are added to a device
        """
        from django.db.models.signals import m2m_changed
        from .models import Device

        m2m_changed.connect(Device.clean_templates,
                            sender=Device.templates.through)
