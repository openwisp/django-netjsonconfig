import json

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from . import CreateVpnMixin
from ..models import Config, Template


class TestAdmin(CreateVpnMixin, TestCase):
    """
    tests for Config model
    """
    fixtures = ['test_templates']
    maxDiff = None
    TEST_KEY = 'w1gwJxKaHcamUw62TQIPgYchwLKn3AA0'
    TEST_MAC_ADDRESS = '00:11:22:33:44:55'

    def setUp(self):
        User.objects.create_superuser(username='admin',
                                      password='tester',
                                      email='admin@admin.com')
        self.client.login(username='admin', password='tester')

    def test_change_config_clean_templates(self):
        t = Template.objects.first()
        d = Config(name='test',
                   backend=t.backend,
                   mac_address=self.TEST_MAC_ADDRESS,
                   config=t.config,
                   key=self.TEST_KEY)
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
        t = Template.objects.first()
        path = reverse('admin:django_netjsonconfig_config_add')
        params = {
            'name': 'add-config-test',
            'mac_address': self.TEST_MAC_ADDRESS,
            'key': self.TEST_KEY,
            'templates': str(t.pk),
            'backend': 'netjsonconfig.OpenWrt',
            'config': json.dumps({})
        }
        response = self.client.post(path, params)
        self.assertEqual(response.status_code, 302)
        d = Config.objects.last()
        self.assertEqual(d.name, 'add-config-test')

    def test_download_config(self):
        d = Config(name='download',
                   backend='netjsonconfig.OpenWrt',
                   mac_address=self.TEST_MAC_ADDRESS,
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
                            'mask': 8
                        }
                    ]
                }
            ]
        })
        data = {
            'name': 'test-config',
            'mac_address': self.TEST_MAC_ADDRESS,
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
        path = reverse('admin:django_netjsonconfig_config_preview')
        data = {
            'name': 'test-config',
            'mac_address': self.TEST_MAC_ADDRESS,
            'backend': 'netjsonconfig.OpenWrt',
            'config': '{}',
            'csrfmiddlewaretoken': 'test'
        }
        response = self.client.post(path, data)
        self.assertContains(response, '<pre class="djnjc-preformatted')

    def test_preview_config_valueerror(self):
        path = reverse('admin:django_netjsonconfig_config_preview')
        data = {
            'name': 'test-config',
            'mac_address': self.TEST_MAC_ADDRESS,
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
            'mac_address': self.TEST_MAC_ADDRESS,
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
            'mac_address': self.TEST_MAC_ADDRESS,
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
            'mac_address': self.TEST_MAC_ADDRESS,
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
        c = Config(name='test',
                   backend=t.backend,
                   mac_address=self.TEST_MAC_ADDRESS,
                   config=t.config,
                   key=self.TEST_KEY)
        c.full_clean()
        c.save()
        path = reverse('admin:django_netjsonconfig_config_change', args=[c.pk])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'field-id')

    def test_empty_backend_import_error(self):
        t = Template.objects.first()
        path = reverse('admin:django_netjsonconfig_config_add')
        params = {
            'name': 'empty-backend',
            'key': self.TEST_KEY,
            'templates': str(t.pk),
            'backend': '',
            'config': json.dumps({'general': {'hostname': 'config'}})
        }
        response = self.client.post(path, params)
        self.assertIn('errors field-backend', str(response.content))

    def test_default_config_backend(self):
        path = reverse('admin:django_netjsonconfig_config_add')
        response = self.client.get(path)
        self.assertContains(response, '<option value="netjsonconfig.OpenWrt" selected')

    def test_default_template_backend(self):
        path = reverse('admin:django_netjsonconfig_template_add')
        response = self.client.get(path)
        self.assertContains(response, '<option value="netjsonconfig.OpenWrt" selected')

    def test_preview_variables(self):
        path = reverse('admin:django_netjsonconfig_config_preview')
        c = Config(name='variables',
                   backend='netjsonconfig.OpenWrt',
                   mac_address=self.TEST_MAC_ADDRESS,
                   config={'general': {'cid': '{{ id }}',
                                       'ckey': '{{ key }}',
                                       'cname': '{{ name }}'}})
        c.full_clean()
        c.save()
        templates = Template.objects.all()
        c.templates.add(*templates)
        data = {
            'name': c.name,
            'id': c.id,
            'mac_address': self.TEST_MAC_ADDRESS,
            'key': c.key,
            'backend': c.backend,
            'config': json.dumps(c.config),
            'csrfmiddlewaretoken': 'test',
            'templates': ','.join([str(t.pk) for t in templates])
        }
        response = self.client.post(path, data)
        self.assertContains(response, "cid &#39;{0}&#39;".format(str(c.id)))
        self.assertContains(response, "ckey &#39;{0}&#39;".format(c.key))
        self.assertContains(response, "cname &#39;{0}&#39;".format(c.name))

    def test_download_vpn_config(self):
        v = self._create_vpn()
        path = reverse('admin:django_netjsonconfig_vpn_download', args=[v.pk])
        response = self.client.get(path)
        self.assertEqual(response.get('content-type'), 'application/octet-stream')

    def test_preview_vpn(self):
        v = self._create_vpn()
        path = reverse('admin:django_netjsonconfig_vpn_preview')
        data = {
            'name': v.name,
            'backend': v.backend,
            'host': v.host,
            'ca': v.ca_id,
            'cert': v.cert_id,
            'config': json.dumps(v.config),
            'csrfmiddlewaretoken': 'test'
        }
        response = self.client.post(path, data)
        self.assertContains(response, '<pre class="djnjc-preformatted')
        self.assertContains(response, '# openvpn config:')
