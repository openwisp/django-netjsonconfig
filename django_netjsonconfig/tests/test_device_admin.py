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
        path = reverse('admin:django_netjsonconfig_device_change', args=[d.pk])
        # ensure it fails with error
        response = self.client.post(path, {'templates': str(t.pk)})
        self.assertIn('errors field-templates', str(response.content))
        # remove conflicting template and ensure doesn't error
        response = self.client.post(path, {'templates': ''})
        self.assertNotIn('errors field-templates', str(response.content))

    def test_download_config(self):
        d = Device(name='download',
                   backend='netjsonconfig.OpenWrt',
                   config={'general':{'hostname':'device'}})
        d.full_clean()
        d.save()
        path = reverse('admin:django_netjsonconfig_device_download', args=[d.pk])
        response = self.client.get(path)
        self.assertEqual(response.get('content-type'), 'application/octet-stream')

    def test_visualize_config(self):
        d = Device(name='download',
                   backend='netjsonconfig.OpenWrt',
                   config={'general':{'hostname':'device'}})
        d.full_clean()
        d.save()
        path = reverse('admin:django_netjsonconfig_device_visualize', args=[d.pk])
        response = self.client.get(path)
        self.assertContains(response, '<pre class="djnjc-preformatted">')
