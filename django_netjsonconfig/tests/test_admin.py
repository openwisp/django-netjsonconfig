import json

from django.test import TestCase
from django.core.urlresolvers import reverse

from ..models import Config, Template


class TestAdmin(TestCase):
    """
    tests for Config model
    """
    fixtures = ['test_templates', 'test_users']
    maxDiff = None
    TEST_KEY = '00:11:22:33:44:55'

    def setUp(self):
        self.client.login(username='admin', password='tester')

    def test_change_config_clean_templates(self):
        t = Template.objects.first()
        d = Config(name='test', backend=t.backend, config=t.config, key=self.TEST_KEY)
        d.full_clean()
        d.save()
        path = reverse('admin:django_netjsonconfig_config_change', args=[d.pk])
        # ensure it fails with error
        response = self.client.post(path, {'templates': str(t.pk), 'key': self.TEST_KEY})
        self.assertIn('errors field-templates', str(response.content))
        # remove conflicting template and ensure doesn't error
        response = self.client.post(path, {'templates': '', 'key': self.TEST_KEY})
        self.assertNotIn('errors field-templates', str(response.content))

    def test_add_config(self):
        """ test for issue #1 """
        t = Template.objects.first()
        path = reverse('admin:django_netjsonconfig_config_add')
        params = {
            'name': 'add_config_clean_templates',
            'key': self.TEST_KEY,
            'templates': str(t.pk),
            'backend': 'netjsonconfig.OpenWrt',
            'config': json.dumps({'general': {'hostname': 'config'}})
        }
        response = self.client.post(path, params)
        self.assertEqual(response.status_code, 302)
        d = Config.objects.last()
        self.assertEqual(d.name, 'add_config_clean_templates')

    def test_download_config(self):
        d = Config(name='download',
                   backend='netjsonconfig.OpenWrt',
                   config={'general': {'hostname': 'config'}},
                   key=self.TEST_KEY)
        d.full_clean()
        d.save()
        path = reverse('admin:django_netjsonconfig_config_download', args=[d.pk])
        response = self.client.get(path)
        self.assertEqual(response.get('content-type'), 'application/octet-stream')

    def test_preview_config(self):
        templates = Template.objects.all()
        path = reverse('admin:django_netjsonconfig_config_preview')
        config = json.dumps({
            'interfaces': [
                {
                    'name': 'lo0',
                    'type': 'loopback',
                    'addresses': [
                        {
                            'family': 'ipv4',
                            'proto': 'static',
                            'address': '127.0.0.1',
                            'netmask': '8'
                        }
                    ]
                }
            ]
        })
        data = {
            'name': 'test-config',
            'backend': 'netjsonconfig.OpenWrt',
            'config': config,
            'csrfmiddlewaretoken': 'test',
            'templates': ','.join([str(t.pk) for t in templates])
        }
        response = self.client.post(path, data)
        self.assertContains(response, '<pre class="djnjc-preformatted')
        self.assertContains(response, 'lo0')
        self.assertContains(response, 'eth0')
        self.assertContains(response, 'dhcp')
        self.assertContains(response, 'radio0')

    def test_preview_config_attributeerror(self):
        t = Template.objects.first()
        path = reverse('admin:django_netjsonconfig_config_preview')
        data = {
            'name': 'test-config',
            'backend': 'netjsonconfig.OpenWrt',
            'config': '{}',
            'csrfmiddlewaretoken': 'test'
        }
        response = self.client.post(path, data)
        self.assertContains(response, '<pre class="djnjc-preformatted')

    def test_preview_config_valueerror(self):
        t = Template.objects.first()
        path = reverse('admin:django_netjsonconfig_config_preview')
        data = {
            'name': 'test-config',
            'backend': 'netjsonconfig.OpenWrt',
            'config': '{}',
            'csrfmiddlewaretoken': 'test',
            'templates': 'wrong,totally'
        }
        response = self.client.post(path, data)
        self.assertEqual(response.status_code, 400)

    def test_preview_config_validationerror(self):
        path = reverse('admin:django_netjsonconfig_config_preview')
        data = {
            'name': 'test-config',
            'backend': 'netjsonconfig.OpenWrt',
            'config': '{"interfaces": {"wrong":"wrong"}}',
            'csrfmiddlewaretoken': 'test'
        }
        response = self.client.post(path, data)
        self.assertEqual(response.status_code, 400)

    def test_preview_config_jsonerror(self):
        path = reverse('admin:django_netjsonconfig_config_preview')
        data = {
            'name': 'test-config',
            'backend': 'netjsonconfig.OpenWrt',
            'config': 'WRONG',
            'csrfmiddlewaretoken': 'test'
        }
        response = self.client.post(path, data)
        self.assertEqual(response.status_code, 400)

    def test_preview_config_showerror(self):
        t1 = Template.objects.first()
        t2 = Template(name='t',
                      config=t1.config,
                      backend='netjsonconfig.OpenWrt')
        t2.full_clean()
        t2.save()
        templates = [t1, t2]
        path = reverse('admin:django_netjsonconfig_config_preview')
        data = {
            'name': 'test-config',
            'backend': 'netjsonconfig.OpenWrt',
            'config': '{}',
            'csrfmiddlewaretoken': 'test',
            'templates': ','.join([str(t.pk) for t in templates])
        }
        response = self.client.post(path, data)
        self.assertContains(response, '<pre class="djnjc-preformatted error')

    def test_preview_config_405(self):
        path = reverse('admin:django_netjsonconfig_config_preview')
        response = self.client.get(path, {})
        self.assertEqual(response.status_code, 405)

    def test_download_template_config(self):
        t = Template.objects.first()
        path = reverse('admin:django_netjsonconfig_template_download', args=[t.pk])
        response = self.client.get(path)
        self.assertEqual(response.get('content-type'), 'application/octet-stream')

    def test_preview_template(self):
        template = Template.objects.first()
        path = reverse('admin:django_netjsonconfig_template_preview')
        data = {
            'name': template.name,
            'backend': template.backend,
            'config': json.dumps(template.config),
            'csrfmiddlewaretoken': 'test'
        }
        response = self.client.post(path, data)
        self.assertContains(response, '<pre class="djnjc-preformatted')
        self.assertNotContains(response, 'system')
        self.assertNotContains(response, 'hostname')

    def test_uuid_field_not_in_add(self):
        path = reverse('admin:django_netjsonconfig_config_add')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'field-id')

    def test_uuid_field_in_change(self):
        t = Template.objects.first()
        c = Config(name='test', backend=t.backend, config=t.config, key=self.TEST_KEY)
        c.full_clean()
        c.save()
        path = reverse('admin:django_netjsonconfig_config_change', args=[c.pk])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'field-id')
