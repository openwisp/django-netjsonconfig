from django.test import TestCase
from django.core.urlresolvers import reverse

from ..models import Device, Template


class TestDeviceAdmin(TestCase):
    """
    tests for Device model
    """
    fixtures = ['test_templates', 'test_users']
    maxDiff = None

    def setUp(self):
        self.client.login(username='admin', password='tester')

    def test_clean_templates(self):
        t = Template.objects.first()
        d = Device(name='test', backend=t.backend, config=t.config)
        d.full_clean()
        d.save()
        path = reverse('admin:netjsonconfig_device_change', args=[d.pk])
        response = self.client.post(path, {'templates': str(t.pk)})
        self.assertIn('errors field-templates', str(response.content))
