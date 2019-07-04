import mock
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase
from django_x509.models import Ca

from netjsonconfig import OpenWrt

from . import CreateConfigMixin, CreateTemplateMixin, TestVpnX509Mixin
from ..models import Config, Device, Template, Vpn


class TestTemplate(CreateConfigMixin, CreateTemplateMixin,
                   TestVpnX509Mixin, TestCase):
    """
    tests for Template model
    """
    ca_model = Ca
    config_model = Config
    device_model = Device
    template_model = Template
    vpn_model = Vpn

    def test_str(self):
        t = Template(name='test', backend='netjsonconfig.OpenWrt')
        self.assertEqual(str(t), 'test')

    def test_backend_class(self):
        t = Template(name='test', backend='netjsonconfig.OpenWrt')
        self.assertIs(t.backend_class, OpenWrt)

    def test_backend_instance(self):
        config = {'general': {'hostname': 'template'}}
        t = Template(name='test', backend='netjsonconfig.OpenWrt', config=config)
        self.assertIsInstance(t.backend_instance, OpenWrt)

    def test_validation(self):
        config = {'interfaces': {'invalid': True}}
        t = Template(name='test', backend='netjsonconfig.OpenWrt', config=config)
        # ensure django ValidationError is raised
        with self.assertRaises(ValidationError):
            t.full_clean()

    def test_config_status_modified_after_change(self):
        t = self._create_template()
        c = self._create_config(device=self._create_device(name='test-status'))
        c.templates.add(t)
        c.status = 'applied'
        c.save()
        c.refresh_from_db()
        self.assertEqual(c.status, 'applied')
        t.config['interfaces'][0]['name'] = 'eth1'
        t.full_clean()
        t.save()
        c.refresh_from_db()
        self.assertEqual(c.status, 'modified')

    def test_no_auto_hostname(self):
        t = self._create_template()
        self.assertNotIn('general', t.backend_instance.config)
        t.refresh_from_db()
        self.assertNotIn('general', t.config)

    def test_default_template(self):
        # no default templates defined yet
        c = self._create_config()
        self.assertEqual(c.templates.count(), 0)
        c.device.delete()
        # create default templates for different backends
        t1 = self._create_template(name='default-openwrt',
                                   backend='netjsonconfig.OpenWrt',
                                   default=True)
        t2 = self._create_template(name='default-openwisp',
                                   backend='netjsonconfig.OpenWisp',
                                   default=True)
        c1 = self._create_config(device=self._create_device(name='test-openwrt'),
                                 backend='netjsonconfig.OpenWrt')
        d2 = self._create_device(name='test-openwisp',
                                 mac_address=self.TEST_MAC_ADDRESS.replace('55', '56'))
        c2 = self._create_config(device=d2,
                                 backend='netjsonconfig.OpenWisp')
        # ensure OpenWRT device has only the default OpenWRT backend
        self.assertEqual(c1.templates.count(), 1)
        self.assertEqual(c1.templates.first().id, t1.id)
        # ensure OpenWISP device has only the default OpenWISP backend
        self.assertEqual(c2.templates.count(), 1)
        self.assertEqual(c2.templates.first().id, t2.id)

    def test_vpn_missing(self):
        try:
            self._create_template(type='vpn')
        except ValidationError as err:
            self.assertTrue('vpn' in err.message_dict)
        else:
            self.fail('ValidationError not raised')

    def test_generic_has_no_vpn(self):
        t = self._create_template(vpn=self._create_vpn())
        self.assertIsNone(t.vpn)
        self.assertFalse(t.auto_cert)

    def test_generic_has_create_cert_false(self):
        t = self._create_template()
        self.assertFalse(t.auto_cert)

    def test_auto_client_template(self):
        vpn = self._create_vpn()
        t = self._create_template(name='autoclient',
                                  type='vpn',
                                  auto_cert=True,
                                  vpn=vpn,
                                  config={})
        control = t.vpn.auto_client()
        self.assertDictEqual(t.config, control)

    def test_auto_client_template_auto_cert_False(self):
        vpn = self._create_vpn()
        t = self._create_template(name='autoclient',
                                  type='vpn',
                                  auto_cert=False,
                                  vpn=vpn,
                                  config={})
        vpn = t.config['openvpn'][0]
        self.assertEqual(vpn['cert'], 'cert.pem')
        self.assertEqual(vpn['key'], 'key.pem')
        self.assertEqual(len(t.config['files']), 1)
        self.assertIn('ca_path', t.config['files'][0]['path'])

    def test_template_context_var(self):
        t = self._create_template(config={'files': [
            {
                'path': '/etc/vpnserver1',
                'mode': '0644',
                'contents': '{{ name }}\n{{ vpnserver1 }}\n'
            }
        ]})
        c = self._create_config()
        c.templates.add(t)
        # clear cache
        del c.backend_instance
        output = c.backend_instance.render()
        vpnserver1 = settings.NETJSONCONFIG_CONTEXT['vpnserver1']
        self.assertIn(vpnserver1, output)

    def test_sharable_template_description(self):
        options1 = {
            "name": "test1",
            "sharing": "public",
            "backend": "netjsonconfig.OpenWrt",
            "notes": "some admininstrative notes",
        }
        options2 = {
            "name": "test2",
            "sharing": "secret_key",
            "backend": "netjsonconfig.OpenWrt",
            "notes": "some admininstrative notes",
        }
        with self.assertRaises(ValidationError):
            t = self.template_model(**options1)
            t.full_clean()
        with self.assertRaises(ValidationError):
            t2 = self.template_model(**options2)
            t2.full_clean()

    def test_variable_substition(self):
        config = {
            "dns_servers": ["{{dns}}"]
        }
        default_values = {
            "dns": "4.4.4.4"
        }
        options = {
            "name": "test1",
            "sharing": "public",
            "backend": "netjsonconfig.OpenWrt",
            "notes": "some admininstrative notes",
            "description": "Some desciption notes",
            "config": config,
            "default_values": default_values
        }
        temp = self.template_model(**options)
        temp.full_clean()
        temp.save()

    def test_sharable_template_default_values_required(self):
        options1 = {
            "name": "test1",
            "sharing": "public",
            "backend": "netjsonconfig.OpenWrt",
            "notes": "some admininstrative notes",
            "description": "Some desciption notes"
        }
        options2 = {
            "name": "test2",
            "sharing": "secret_key",
            "backend": "netjsonconfig.OpenWrt",
            "notes": "some admininstrative notes",
            "description": "Some desciption notes"
        }
        t = self.template_model(**options1)
        t.full_clean()
        t2 = self.template_model(**options2)
        t2.full_clean()

    def test_none_secret_key(self):
        options1 = {
            "name": "test-public",
            "sharing": "public",
            "backend": "netjsonconfig.OpenWrt",
            "description": "some description"
        }
        options2 = {
            "name": "test-secret",
            "sharing": "secret_key",
            "backend": "netjsonconfig.OpenWrt",
            "description": "some description"
        }
        t = self.template_model(**options1)
        t1 = self.template_model(**options2)
        t.full_clean()
        t1.full_clean()
        t1.save()
        t.save()
        self.assertEqual(t.key, None)
        self.assertNotEqual(t1.key, None)

    def test_template_vpn_import(self):
        data = {
            "id": "915db519-9bd1-4172-a866-c94f93eddd73",
            "vpn": {
                "id": "f770fbb8-46ff-4fb6-a9e4-a955e1fe659b",
                "ca": {
                    "id": 1,
                    "name": "cred1",
                    "notes": "asdasd",
                },
                "cert": {
                    "id": 1,
                    "name": "cert",
                    "ca": 1
                },
                "config": {
                    "openvpn": [
                        {
                            "name": "vpn1",
                            "mode": "server",
                            "proto": "udp",
                            "port": 1194,
                            "dev_type": "tun",
                            "dev": "vvvv",
                            "comp_lzo": "adaptive",
                            "auth": "SHA1",
                            "cipher": "BF-CBC",
                            "ca": "ca.pem",
                            "cert": "cert.pem",
                            "key": "key.pem",
                            "status_version": 1,
                            "reneg_sec": 3600,
                            "tls_timeout": 2,
                            "verb": 1,
                            "topology": "subnet"
                        }
                    ]
                },
                "name": "vpn1",
                "host": "localhost",
                "backend": "django_netjsonconfig.vpn_backends.OpenVpn",
            },
            "tags": [
                "WDS",
                "4G",
                "VPN",
                "mesh"
            ],
            "config": {
                "interfaces": [
                    {
                        "type": "ethernet",
                        "name": "eth7",
                        "mac": "{{ mac }}",
                        "addresses": [
                                {
                                    "proto": "static",
                                    "family": "ipv4",
                                    "address": "{{ ip }}",
                                    "mask": 24,
                                    "gateway": ""
                                }
                        ]
                    }
                ]
            },
            "default_values": {
                "mac": "00-87-AB-DE-43-23",
                "ip": "1.1.1.1"
            },
            "name": "public2",
            "backend": "netjsonconfig.OpenWrt",
            "type": "vpn",
            "sharing": "public",
            "key": None,
            "auto_cert": False,
            "description": "some description",
        }
        options = {
            "sharing": "import",
            "url": "http://localhost:8000/test/url/",
            "backend": "netjsonconfig.OpenWrt",
            "name": "import-template"
        }
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = data
        with mock.patch('requests.get') as mocked:
            mocked.return_value = response
            t = self.template_model(**options)
            t.full_clean()
            t.save()
            mocked.assert_called_once()
        queryset = self.template_model.objects.get(name='import-template')
        self.assertEqual(queryset.name, 'import-template')
        self.assertEqual(queryset.vpn.name, 'vpn1')

    def test_template_generic_import(self):
        data = {
            "id": "915db519-9bd1-4172-a866-c94f93eddd73",
            "tags": [
                "WDS",
                "4G",
                "VPN",
                "mesh"
            ],
            "config": {
                "interfaces": [
                    {
                        "type": "ethernet",
                        "name": "eth7",
                        "mac": "{{ mac }}",
                        "addresses": [
                                {
                                    "proto": "static",
                                    "family": "ipv4",
                                    "address": "{{ ip }}",
                                    "mask": 24,
                                    "gateway": ""
                                }
                        ]
                    }
                ]
            },
            "default_values": {
                "mac": "00-87-AB-DE-43-23",
                "ip": "1.1.1.1"
            },
            "name": "public",
            "backend": "netjsonconfig.OpenWrt",
            "type": "generic",
            "sharing": "public",
            "key": None,
            "auto_cert": False,
            "description": "some description",
        }
        options = {
            "sharing": "import",
            "url": "http://localhost:8000/test/url/",
            "backend": "netjsonconfig.OpenWrt",
            "name": "import-generic-template"
        }
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = data
        with mock.patch('requests.get') as mocked:
            mocked.return_value = response
            t = self.template_model(**options)
            t.full_clean()
            t.save()
            mocked.assert_called_once()
        queryset = self.template_model.objects.get(name='import-generic-template')
        self.assertEqual(queryset.name, 'import-generic-template')

    def test_template_import_url_not_found(self):
        options = {
            "sharing": "import",
            "url": "http://localhost:8000/test/url/",
            "name": "invalid-url",
            "backend": "netjsonconfig.OpenWrt"
        }
        response = mock.Mock()
        response.status_code = 404
        with mock.patch('requests.get') as mocked:
            mocked.return_value = response
            with self.assertRaises(ValidationError):
                t = self.template_model(**options)
                t.full_clean()
            mocked.assert_called_once()

    def test_template_import_connection_error(self):
        options = {
            "sharing": "import",
            "url": "http://localhost:8000/test/url/",
            "name": "invalid-url",
            "backend": "netjsonconfig.OpenWrt"
        }
        with self.assertRaises(ValidationError):
            t = self.template_model(**options)
            t.full_clean()
            t.save()

    def test_import_template_invalid_data(self):
        options = {
            "sharing": "import",
            "url": "http://localhost:8000/test/url/",
            "name": "invalid-content",
            "backend": "netjsonconfig.OpenWrt",
        }
        response = mock.Mock()
        response.status_code = 200
        response.json.side_effect = ValueError
        with mock.patch('requests.get') as mocked:
            mocked.return_value = response
            with self.assertRaises(ValidationError):
                t = self.template_model(**options)
                t.full_clean()
                t.save()
            mocked.assert_called_once()
