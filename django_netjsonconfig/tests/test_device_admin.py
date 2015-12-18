import json

from django.test import TestCase
from django.core.urlresolvers import reverse

from ..models import Device, Template


class TestDeviceAdmin(TestCase):
    """
    tests for Device model
    """
    fixtures = ['test_templates', 'test_users']
    maxDiff = None
    TEST_KEY = '00:11:22:33:44:55'

    def setUp(self):
        self.client.login(username='admin', password='tester')

    def test_change_device_clean_templates(self):
        t = Template.objects.first()
        d = Device(name='test', backend=t.backend, config=t.config, key=self.TEST_KEY)
        d.full_clean()
        d.save()
        path = reverse('admin:django_netjsonconfig_device_change', args=[d.pk])
        # ensure it fails with error
        response = self.client.post(path, {'templates': str(t.pk), 'key': self.TEST_KEY})
        self.assertIn('errors field-templates', str(response.content))
        # remove conflicting template and ensure doesn't error
        response = self.client.post(path, {'templates': '', 'key': self.TEST_KEY})
        self.assertNotIn('errors field-templates', str(response.content))

    def test_add_device(self):
        """ test for issue #1 """
        t = Template.objects.first()
        path = reverse('admin:django_netjsonconfig_device_add')
        params = {
            'name': 'add_device_clean_templates',
            'key': self.TEST_KEY,
            'templates': str(t.pk),
            'backend': 'netjsonconfig.OpenWrt',
            'config': json.dumps({'general':{'hostname':'device'}})
        }
        response = self.client.post(path, params)
        self.assertEqual(response.status_code, 302)
        d = Device.objects.last()
        self.assertEqual(d.name, 'add_device_clean_templates')

    def test_download_config(self):
        d = Device(name='download',
                   backend='netjsonconfig.OpenWrt',
                   config={'general':{'hostname':'device'}},
                   key=self.TEST_KEY)
        d.full_clean()
        d.save()
        path = reverse('admin:django_netjsonconfig_device_download', args=[d.pk])
        response = self.client.get(path)
        self.assertEqual(response.get('content-type'), 'application/octet-stream')

    def test_visualize_config(self):
        d = Device(name='download',
                   backend='netjsonconfig.OpenWrt',
                   config={'general':{'hostname':'device'}},
                   key=self.TEST_KEY)
        d.full_clean()
        d.save()
        path = reverse('admin:django_netjsonconfig_device_visualize', args=[d.pk])
        response = self.client.get(path)
        self.assertContains(response, '<pre class="djnjc-preformatted">')
