import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django_x509.models import Ca

from . import CreateConfigMixin, CreateTemplateMixin, TestVpnX509Mixin
from ..models import Config, Device, Template, Vpn


class TestAdmin(TestVpnX509Mixin, CreateConfigMixin, CreateTemplateMixin, TestCase):
    """
    tests for Config model
    """
    fixtures = ['test_templates']
    maxDiff = None
    ca_model = Ca
    config_model = Config
    device_model = Device
    vpn_model = Vpn
    template_model = Template

    def setUp(self):
        User.objects.create_superuser(username='admin',
                                      password='tester',
                                      email='admin@admin.com')
        self.client.login(username='admin', password='tester')

    def _get_device_params(self):
        return {
            'name': '',
            'hardware_id': '1234',
            'mac_address': self.TEST_MAC_ADDRESS,
            'key': self.TEST_KEY,
            'model': '',
            'os': '',
            'notes': '',
            'config-0-id': '',
            'config-0-device': '',
            'config-0-templates': '',
            'config-0-backend': 'netjsonconfig.OpenWrt',
            'config-0-config': json.dumps({}),
            'config-TOTAL_FORMS': 1,
            'config-INITIAL_FORMS': 0,
            'config-MIN_NUM_FORMS': 0,
            'config-MAX_NUM_FORMS': 1,
        }

    def test_change_device_clean_templates(self):
        t = Template.objects.first()
        d = self._create_device()
        c = self._create_config(device=d, backend=t.backend, config=t.config)
        path = reverse('admin:django_netjsonconfig_device_change', args=[d.pk])
        params = self._get_device_params()
        params.update({
            'name': 'test-change-device',
            'config-0-id': str(c.pk),
            'config-0-device': str(d.pk),
            'config-0-templates': str(t.pk),
            'config-INITIAL_FORMS': 1
        })
        # ensure it fails with error
        response = self.client.post(path, params)
        self.assertContains(response, 'errors field-templates')
        # remove conflicting template and ensure doesn't error
        params['config-0-templates'] = ''
        response = self.client.post(path, params)
        self.assertNotContains(response, 'errors field-templates', status_code=302)

    def test_add_device(self):
        t = Template.objects.first()
        path = reverse('admin:django_netjsonconfig_device_add')
        params = self._get_device_params()
        params.update({
            'name': 'test-add-config',
            'config-0-templates': str(t.pk)
        })
        response = self.client.post(path, params)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Device.objects.filter(name=params['name']).count(), 1)

    def test_download_device_config(self):
        d = self._create_device(name='download')
        self._create_config(device=d)
        path = reverse('admin:django_netjsonconfig_device_download', args=[d.pk])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('content-type'), 'application/octet-stream')

    def test_download_device_config_404(self):
        d = self._create_device(name='download')
        path = reverse('admin:django_netjsonconfig_device_download', args=[d.pk])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def test_preview_device_config(self):
        templates = Template.objects.all()
        path = reverse('admin:django_netjsonconfig_device_preview')
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
            'name': 'test-device',
            'mac_address': self.TEST_MAC_ADDRESS,
            'backend': 'netjsonconfig.OpenWrt',
            'config': config,
            'context': '',
            'csrfmiddlewaretoken': 'test',
            'templates': ','.join([str(t.pk) for t in templates])
        }
        response = self.client.post(path, data)
        self.assertContains(response, '<pre class="djnjc-preformatted')
        self.assertContains(response, 'lo0')
        self.assertContains(response, 'eth0')
        self.assertContains(response, 'dhcp')
        self.assertContains(response, 'radio0')

    def test_variable_usage(self):
        config = {
            'interfaces': [
                {
                    'name': 'lo0',
                    'type': 'loopback',
                    'mac_address': '{{ mac }}',
                    'addresses': [
                        {
                            'family': 'ipv4',
                            'proto': 'static',
                            'address': '{{ ip }}',
                            'mask': 8
                        }
                    ]
                }
            ]
        }
        default_values = {
            'ip': '192.168.56.2',
            'mac': '08:00:27:06:72:88'
        }
        t = self._create_template(config=config, default_values=default_values)
        path = reverse('admin:django_netjsonconfig_device_add')
        params = self._get_device_params()
        params.update({
            'name': 'test-device',
            'config-0-templates': str(t.pk)
        })
        response = self.client.post(path, params)
        self.assertNotContains(response, 'errors field-templates', status_code=302)
        self.assertEqual(Device.objects.filter(name='test-device').count(), 1)

    def test_preview_device_config_empty_id(self):
        path = reverse('admin:django_netjsonconfig_device_preview')
        config = json.dumps({'general': {'descripion': 'id: {{ id }}'}})
        data = {
            'id': '',
            'name': 'test-empty-id',
            'mac_address': self.TEST_MAC_ADDRESS,
            'backend': 'netjsonconfig.OpenWrt',
            'config': config,
            'csrfmiddlewaretoken': 'test',
        }
        response = self.client.post(path, data)
        # expect 200
        self.assertContains(response, 'id:')

    def test_preview_device_attributeerror(self):
        path = reverse('admin:django_netjsonconfig_device_preview')
        data = {
            'name': 'test-device',
            'mac_address': self.TEST_MAC_ADDRESS,
            'backend': 'netjsonconfig.OpenWrt',
            'config': '{}',
            'csrfmiddlewaretoken': 'test'
        }
        response = self.client.post(path, data)
        self.assertContains(response, '<pre class="djnjc-preformatted')

    def test_preview_device_valueerror(self):
        path = reverse('admin:django_netjsonconfig_device_preview')
        data = {
            'name': 'test-device',
            'mac_address': self.TEST_MAC_ADDRESS,
            'backend': 'netjsonconfig.OpenWrt',
            'config': '{}',
            'templates': 'wrong,totally',
            'csrfmiddlewaretoken': 'test',
        }
        response = self.client.post(path, data)
        self.assertEqual(response.status_code, 400)

    def test_preview_device_validationerror(self):
        path = reverse('admin:django_netjsonconfig_device_preview')
        data = {
            'name': 'test-device',
            'mac_address': self.TEST_MAC_ADDRESS,
            'backend': 'netjsonconfig.OpenWrt',
            'config': '{"interfaces": {"wrong":"wrong"}}',
            'csrfmiddlewaretoken': 'test'
        }
        response = self.client.post(path, data)
        self.assertEqual(response.status_code, 400)

    def test_preview_device_jsonerror(self):
        path = reverse('admin:django_netjsonconfig_device_preview')
        data = {
            'name': 'test-device',
            'mac_address': self.TEST_MAC_ADDRESS,
            'backend': 'netjsonconfig.OpenWrt',
            'config': 'WRONG',
            'csrfmiddlewaretoken': 'test'
        }
        response = self.client.post(path, data)
        self.assertEqual(response.status_code, 400)

    def test_preview_device_showerror(self):
        t1 = Template.objects.get(name='dhcp')
        t2 = Template(name='t',
                      config=t1.config,
                      backend='netjsonconfig.OpenWrt')
        t2.full_clean()
        t2.save()
        templates = [t1, t2]
        path = reverse('admin:django_netjsonconfig_device_preview')
        data = {
            'name': 'test-device',
            'mac_address': self.TEST_MAC_ADDRESS,
            'backend': 'netjsonconfig.OpenWrt',
            'config': '{}',
            'templates': ','.join([str(t.pk) for t in templates]),
            'csrfmiddlewaretoken': 'test',
        }
        response = self.client.post(path, data)
        # expect duplicate error
        self.assertContains(response, '<pre class="djnjc-preformatted error')

    def test_preview_device_405(self):
        path = reverse('admin:django_netjsonconfig_device_preview')
        response = self.client.get(path, {})
        self.assertEqual(response.status_code, 405)

    def test_download_template_config(self):
        t = Template.objects.first()
        path = reverse('admin:django_netjsonconfig_template_download', args=[t.pk])
        response = self.client.get(path)
        self.assertEqual(response.get('content-type'), 'application/octet-stream')

    def test_preview_template(self):
        template = Template.objects.get(name='radio0')
        path = reverse('admin:django_netjsonconfig_template_preview')
        data = {
            'name': template.name,
            'backend': template.backend,
            'config': json.dumps(template.config),
            'csrfmiddlewaretoken': 'test'
        }
        response = self.client.post(path, data)
        self.assertContains(response, '<pre class="djnjc-preformatted')
        self.assertContains(response, 'radio0')
        self.assertContains(response, 'phy')
        self.assertNotContains(response, 'system')
        self.assertNotContains(response, 'hostname')

    def test_uuid_field_in_change(self):
        t = Template.objects.first()
        c = self._create_config(device=self._create_device(),
                                backend=t.backend,
                                config=t.config)
        path = reverse('admin:django_netjsonconfig_device_change', args=[c.device.pk])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'field-id')

    def test_empty_backend_import_error(self):
        t = Template.objects.first()
        path = reverse('admin:django_netjsonconfig_device_add')
        params = self._get_device_params()
        params.update({
            'name': 'empty-backend',
            'key': self.TEST_KEY,
            'config-0-templates': str(t.pk),
            'config-0-backend': '',
            'config-0-config': json.dumps({'general': {'hostname': 'config'}})
        })
        response = self.client.post(path, params)
        self.assertContains(response, 'errors field-backend')

    def test_default_device_backend(self):
        path = reverse('admin:django_netjsonconfig_device_add')
        response = self.client.get(path)
        self.assertContains(response, '<option value="netjsonconfig.OpenWrt" selected')

    def test_existing_device_backend(self):
        d = self._create_device()
        self._create_config(device=d, backend='netjsonconfig.OpenWisp')
        path = reverse('admin:django_netjsonconfig_device_change', args=[d.pk])
        response = self.client.get(path)
        self.assertContains(response, '<option value="netjsonconfig.OpenWisp" selected')

    def test_device_search(self):
        d = self._create_device(name='admin-search-test')
        path = reverse('admin:django_netjsonconfig_device_changelist')
        response = self.client.get(path, {'q': str(d.pk.hex)})
        self.assertContains(response, 'admin-search-test')
        response = self.client.get(path, {'q': 'ZERO-RESULTS-PLEASE'})
        self.assertNotContains(response, 'admin-search-test')

    def test_default_template_backend(self):
        path = reverse('admin:django_netjsonconfig_template_add')
        response = self.client.get(path)
        self.assertContains(response, '<option value="netjsonconfig.OpenWrt" selected')

    def test_existing_template_backend(self):
        t = Template.objects.first()
        t.backend = 'netjsonconfig.OpenWisp'
        t.save()
        path = reverse('admin:django_netjsonconfig_template_change', args=[t.pk])
        response = self.client.get(path)
        self.assertContains(response, '<option value="netjsonconfig.OpenWisp" selected')

    def test_preview_variables(self):
        path = reverse('admin:django_netjsonconfig_device_preview')
        c = self._create_config(device=self._create_device(name='variables'),
                                config={'general': {'cid': '{{ id }}',
                                                    'ckey': '{{ key }}',
                                                    'cname': '{{ name }}'}})
        templates = Template.objects.all()
        c.templates.add(*templates)
        d = c.device
        data = {
            'name': d.name,
            'id': d.id,
            'mac_address': d.mac_address,
            'key': d.key,
            'backend': c.backend,
            'config': json.dumps(c.config),
            'csrfmiddlewaretoken': 'test',
            'templates': ','.join([str(t.pk) for t in templates])
        }
        response = self.client.post(path, data)
        self.assertContains(response, "cid &#39;{0}&#39;".format(str(d.id)))
        self.assertContains(response, "ckey &#39;{0}&#39;".format(d.key))
        self.assertContains(response, "cname &#39;{0}&#39;".format(d.name))

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

    def test_add_vpn(self):
        path = reverse('admin:django_netjsonconfig_vpn_add')
        response = self.client.get(path)
        self.assertContains(response, 'value="django_netjsonconfig.vpn_backends.OpenVpn" selected')

    def test_ip_not_in_add_device(self):
        path = reverse('admin:django_netjsonconfig_device_add')
        response = self.client.get(path)
        self.assertNotContains(response, 'last_ip')

    def test_ip_in_change_device(self):
        d = self._create_device()
        t = Template.objects.first()
        self._create_config(device=d, backend=t.backend, config=t.config)
        path = reverse('admin:django_netjsonconfig_device_change', args=[d.pk])
        response = self.client.get(path)
        self.assertContains(response, 'last_ip')

    def test_hardware_id_in_change_device(self):
        d = self._create_device()
        t = Template.objects.first()
        self._create_config(device=d, backend=t.backend, config=t.config)
        path = reverse('admin:django_netjsonconfig_device_change', args=[d.pk])
        response = self.client.get(path)
        self.assertContains(response, 'hardware_id')

    def test_error_if_download_config(self):
        d = self._create_device()
        res = self.client.get(reverse('admin:django_netjsonconfig_device_change', args=[d.pk]))
        self.assertNotContains(res, 'Download configuration')

    def test_preview_device_with_context(self):
        path = reverse('admin:django_netjsonconfig_device_preview')
        config = json.dumps({
            'openwisp': [
                {
                    "config_name": "controller",
                    "config_value": "http",
                    "url": "http://controller.examplewifiservice.com",
                    "interval": "{{ interval }}",
                    "verify_ssl": "1",
                    "uuid": "UUID",
                    "key": self.TEST_KEY
                }
            ]
        })
        data = {
            'id': 'd60ecd62-5d00-4e7b-bd16-6fc64a95e60c',
            'name': 'test-asd',
            'mac_address': self.TEST_MAC_ADDRESS,
            'backend': 'netjsonconfig.OpenWrt',
            'config': config,
            'csrfmiddlewaretoken': 'test',
            'context': '{"interval": "60"}'
        }
        response = self.client.post(path, data)
        self.assertContains(response, "option interval &#39;60&#39;")
