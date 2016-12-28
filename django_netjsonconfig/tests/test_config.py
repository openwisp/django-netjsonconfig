from copy import deepcopy

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.transaction import atomic
from django.test import TestCase

from netjsonconfig import OpenWrt

from . import CreateTemplateMixin, CreateVpnMixin
from .. import settings as app_settings
from ..models import Config, Template


class TestConfig(CreateTemplateMixin, CreateVpnMixin, TestCase):
    """
    tests for Config model
    """
    fixtures = ['test_templates']
    maxDiff = None
    TEST_KEY = 'w1gwJxKaHcamUw62TQIPgYchwLKn3AA0'
    TEST_MAC_ADDRESS = '00:11:22:33:44:55'

    def test_str(self):
        d = Config(name='test')
        self.assertEqual(str(d), 'test')

    def test_config_not_none(self):
        c = Config(name='test',
                   mac_address=self.TEST_MAC_ADDRESS,
                   backend='netjsonconfig.OpenWrt',
                   config=None)
        c.full_clean()
        self.assertEqual(c.config, {})

    def test_backend_class(self):
        d = Config(name='test',
                   mac_address=self.TEST_MAC_ADDRESS,
                   backend='netjsonconfig.OpenWrt')
        self.assertIs(d.backend_class, OpenWrt)

    def test_backend_instance(self):
        config = {'general': {'hostname': 'config'}}
        d = Config(name='test',
                   mac_address=self.TEST_MAC_ADDRESS,
                   backend='netjsonconfig.OpenWrt',
                   config=config)
        self.assertIsInstance(d.backend_instance, OpenWrt)

    def test_validation(self):
        config = {'interfaces': {'invalid': True}}
        d = Config(name='test',
                   mac_address=self.TEST_MAC_ADDRESS,
                   backend='netjsonconfig.OpenWrt',
                   config=config,
                   key=self.TEST_KEY)
        # ensure django ValidationError is raised
        with self.assertRaises(ValidationError):
            d.full_clean()

    def test_json(self):
        dhcp = Template.objects.get(name='dhcp')
        radio = Template.objects.get(name='radio0')
        d = Config(name='test',
                   mac_address=self.TEST_MAC_ADDRESS,
                   backend='netjsonconfig.OpenWrt',
                   config={'general': {'hostname': 'json-test'}},
                   key=self.TEST_KEY)
        d.full_clean()
        d.save()
        d.templates.add(dhcp)
        d.templates.add(radio)
        full_config = {
            'general': {
                'hostname': 'json-test'
            },
            "interfaces": [
                {
                    "name": "eth0",
                    "type": "ethernet",
                    "addresses": [
                        {
                            "proto": "dhcp",
                            "family": "ipv4"
                        }
                    ]
                }
            ],
            "radios": [
                {
                    "name": "radio0",
                    "phy": "phy0",
                    "driver": "mac80211",
                    "protocol": "802.11n",
                    "channel": 11,
                    "channel_width": 20,
                    "tx_power": 8,
                    "country": "IT"
                }
            ]
        }
        del d.backend_instance
        self.assertDictEqual(d.json(dict=True), full_config)
        json_string = d.json()
        self.assertIn('json-test', json_string)
        self.assertIn('eth0', json_string)
        self.assertIn('radio0', json_string)

    def test_m2m_validation(self):
        # if config and template have a conflicting non-unique item
        # that violates the schema, the system should not allow
        # the assignment and raise an exception
        config = {
            "files": [
                {
                    "path": "/test",
                    "mode": "0644",
                    "contents": "test"
                }
            ]
        }
        config_copy = deepcopy(config)
        t = Template(name='files',
                     backend='netjsonconfig.OpenWrt',
                     config=config)
        t.full_clean()
        t.save()
        d = Config(name='test',
                   key=self.TEST_KEY,
                   mac_address=self.TEST_MAC_ADDRESS,
                   backend='netjsonconfig.OpenWrt',
                   config=config_copy)
        d.full_clean()
        d.save()
        with atomic():
            try:
                d.templates.add(t)
            except ValidationError:
                pass
            else:
                self.fail('ValidationError not raised')
        t.config['files'][0]['path'] = '/test2'
        t.full_clean()
        t.save()
        d.templates.add(t)

    def test_key_validation(self):
        d = Config(name='test',
                   mac_address=self.TEST_MAC_ADDRESS,
                   backend='netjsonconfig.OpenWrt',
                   config={'general': {'hostname': 'json-test'}})
        d.key = 'key/key'
        with self.assertRaises(ValidationError):
            d.full_clean()
        d.key = 'key.key'
        with self.assertRaises(ValidationError):
            d.full_clean()
        d.key = 'key key'
        with self.assertRaises(ValidationError):
            d.full_clean()
        d.key = self.TEST_KEY
        d.full_clean()

    def test_checksum(self):
        d = Config(name='test',
                   mac_address=self.TEST_MAC_ADDRESS,
                   backend='netjsonconfig.OpenWrt',
                   config={'general': {'hostname': 'json-test'}},
                   key=self.TEST_KEY)
        d.full_clean()
        d.save()
        self.assertEqual(len(d.checksum), 32)

    def test_backend_import_error(self):
        """
        see issue #5
        https://github.com/openwisp/django-netjsonconfig/issues/5
        """
        d = Config()
        with self.assertRaises(ValidationError):
            d.full_clean()
        d.backend = 'wrong'
        with self.assertRaises(ValidationError):
            d.full_clean()

    def test_default_status(self):
        c = Config(name='test')
        self.assertEqual(c.status, 'modified')

    def test_status_modified_after_change(self):
        c = Config(name='test-status',
                   status='running',
                   backend='netjsonconfig.OpenWrt',
                   mac_address=self.TEST_MAC_ADDRESS,
                   config={'general': {}})
        c.full_clean()
        c.save()
        self.assertEqual(c.status, 'running')
        c.refresh_from_db()
        c.name = 'test-status-modified'
        c.full_clean()
        c.save()
        self.assertEqual(c.status, 'modified')

    def test_status_modified_after_templates_changed(self):
        c = Config(name='test-status',
                   status='running',
                   backend='netjsonconfig.OpenWrt',
                   mac_address=self.TEST_MAC_ADDRESS,
                   config={'general': {}})
        c.full_clean()
        c.save()
        self.assertEqual(c.status, 'running')
        t = Template.objects.first()
        c.templates.add(t)
        c.refresh_from_db()
        self.assertEqual(c.status, 'modified')
        c.status = 'running'
        c.save()
        c.refresh_from_db()
        self.assertEqual(c.status, 'running')
        c.templates.remove(t)
        c.refresh_from_db()
        self.assertEqual(c.status, 'modified')

    def test_auto_hostname(self):
        c = Config(name='automate-me',
                   backend='netjsonconfig.OpenWrt',
                   mac_address=self.TEST_MAC_ADDRESS,
                   config={'general': {}})
        c.full_clean()
        c.save()
        expected = {
            'general': {'hostname': 'automate-me'}
        }
        self.assertDictEqual(c.backend_instance.config, expected)
        c.refresh_from_db()
        self.assertDictEqual(c.config, {'general': {}})

    def test_config_context(self):
        config = {
            'general': {
                'id': '{{ id }}',
                'key': '{{ key }}',
                'name': '{{ name }}',
                'mac_address': '{{ mac_address }}'
            }
        }
        c = Config(name='context-test',
                   backend='netjsonconfig.OpenWrt',
                   mac_address=self.TEST_MAC_ADDRESS,
                   config=config)
        output = c.backend_instance.render()
        self.assertIn(str(c.id), output)
        self.assertIn(c.key, output)
        self.assertIn(c.name, output)
        self.assertIn(c.mac_address, output)

    def test_context_setting(self):
        config = {
            'general': {
                'vpnserver1': '{{ vpnserver1 }}'
            }
        }
        c = Config(name='context-setting-test',
                   backend='netjsonconfig.OpenWrt',
                   mac_address=self.TEST_MAC_ADDRESS,
                   config=config)
        output = c.backend_instance.render()
        vpnserver1 = settings.NETJSONCONFIG_CONTEXT['vpnserver1']
        self.assertIn(vpnserver1, output)

    def test_mac_address_as_hostname(self):
        c = Config(name='00:11:22:33:44:55',
                   backend='netjsonconfig.OpenWrt',
                   mac_address=self.TEST_MAC_ADDRESS)
        c.full_clean()
        c.save()
        self.assertIn('00-11-22-33-44-55', c.backend_instance.render())

    def test_create_vpnclient(self):
        vpn = self._create_vpn()
        t = self._create_template(name='test-network',
                                  type='vpn',
                                  vpn=vpn)
        c = Config(name='test-create-cert',
                   backend='netjsonconfig.OpenWrt',
                   config={'general': {}},
                   mac_address=self.TEST_MAC_ADDRESS)
        c.full_clean()
        c.save()
        c.templates.add(t)
        c.save()
        vpnclient = c.vpnclient_set.first()
        self.assertIsNotNone(vpnclient)
        self.assertEqual(c.vpnclient_set.count(), 1)
        self.assertEqual(vpnclient.config, c)
        self.assertEqual(vpnclient.vpn, vpn)

    def test_delete_vpnclient(self):
        self.test_create_vpnclient()
        c = Config.objects.get(name='test-create-cert')
        t = Template.objects.get(name='test-network')
        c.templates.remove(t)
        c.save()
        vpnclient = c.vpnclient_set.first()
        self.assertIsNone(vpnclient)
        self.assertEqual(c.vpnclient_set.count(), 0)

    def test_clear_vpnclient(self):
        self.test_create_vpnclient()
        c = Config.objects.get(name='test-create-cert')
        c.templates.clear()
        c.save()
        vpnclient = c.vpnclient_set.first()
        self.assertIsNone(vpnclient)
        self.assertEqual(c.vpnclient_set.count(), 0)

    def test_mac_address_validator(self):
        d = Config(name='test',
                   mac_address='WRONG',
                   backend='netjsonconfig.OpenWrt',
                   config={'general': {'hostname': 'json-test'}},
                   key=self.TEST_KEY)
        try:
            d.full_clean()
        except ValidationError as e:
            self.assertIn('mac_address', e.message_dict)
        else:
            self.fail('ValidationError not raised')

    def test_create_cert(self):
        vpn = self._create_vpn()
        t = self._create_template(name='test-create-cert',
                                  type='vpn',
                                  vpn=vpn,
                                  auto_cert=True)
        c = Config(name='test-create-cert',
                   backend='netjsonconfig.OpenWrt',
                   mac_address=self.TEST_MAC_ADDRESS,
                   config={'general': {}})
        c.full_clean()
        c.save()
        c.templates.add(t)
        c.save()
        vpnclient = c.vpnclient_set.first()
        self.assertIsNotNone(vpnclient)
        self.assertTrue(vpnclient.auto_cert)
        self.assertIsNotNone(vpnclient.cert)
        self.assertEqual(c.vpnclient_set.count(), 1)

    def test_automatically_created_cert_common_name_format(self):
        self.test_create_cert()
        c = Config.objects.get(name='test-create-cert')
        vpnclient = c.vpnclient_set.first()
        expected_cn = app_settings.COMMON_NAME_FORMAT.format(**c.__dict__)
        self.assertEqual(vpnclient.cert.common_name, expected_cn)

    def test_automatically_created_cert_deleted_post_clear(self):
        self.test_create_cert()
        c = Config.objects.get(name='test-create-cert')
        vpnclient = c.vpnclient_set.first()
        cert = vpnclient.cert
        cert_model = cert.__class__
        c.templates.clear()
        self.assertEqual(c.vpnclient_set.count(), 0)
        self.assertEqual(cert_model.objects.filter(pk=cert.pk).count(), 0)

    def test_automatically_created_cert_deleted_post_remove(self):
        self.test_create_cert()
        c = Config.objects.get(name='test-create-cert')
        t = Template.objects.get(name='test-create-cert')
        vpnclient = c.vpnclient_set.first()
        cert = vpnclient.cert
        cert_model = cert.__class__
        c.templates.remove(t)
        self.assertEqual(c.vpnclient_set.count(), 0)
        self.assertEqual(cert_model.objects.filter(pk=cert.pk).count(), 0)

    def test_create_cert_false(self):
        vpn = self._create_vpn()
        t = self._create_template(type='vpn', auto_cert=False, vpn=vpn)
        c = Config(name='test-create-cert-false',
                   backend='netjsonconfig.OpenWrt',
                   mac_address=self.TEST_MAC_ADDRESS,
                   config={'general': {}})
        c.full_clean()
        c.save()
        c.templates.add(t)
        c.save()
        vpnclient = c.vpnclient_set.first()
        self.assertIsNotNone(vpnclient)
        self.assertFalse(vpnclient.auto_cert)
        self.assertIsNone(vpnclient.cert)
        self.assertEqual(c.vpnclient_set.count(), 1)

    def _get_vpn_context(self):
        self.test_create_cert()
        c = Config.objects.get(name='test-create-cert')
        context = c.get_context()
        vpnclient = c.vpnclient_set.first()
        return context, vpnclient

    def test_vpn_context_ca_path(self):
        context, vpnclient = self._get_vpn_context()
        ca = vpnclient.cert.ca
        key = 'ca_path_{0}'.format(vpnclient.vpn.pk.hex)
        filename = 'ca-{0}-{1}.pem'.format(ca.pk, ca.common_name)
        value = '{0}/{1}'.format(app_settings.CERT_PATH, filename)
        self.assertIn(key, context)
        self.assertIn(value, context[key])

    def test_vpn_context_ca_contents(self):
        context, vpnclient = self._get_vpn_context()
        key = 'ca_contents_{0}'.format(vpnclient.vpn.pk.hex)
        value = vpnclient.cert.ca.certificate
        self.assertIn(key, context)
        self.assertIn(value, context[key])

    def test_vpn_context_cert_path(self):
        context, vpnclient = self._get_vpn_context()
        vpn_pk = vpnclient.vpn.pk.hex
        key = 'cert_path_{0}'.format(vpn_pk)
        filename = 'client-{0}.pem'.format(vpn_pk)
        value = '{0}/{1}'.format(app_settings.CERT_PATH, filename)
        self.assertIn(key, context)
        self.assertIn(value, context[key])

    def test_vpn_context_cert_contents(self):
        context, vpnclient = self._get_vpn_context()
        vpn_pk = vpnclient.vpn.pk.hex
        key = 'cert_contents_{0}'.format(vpn_pk)
        value = vpnclient.cert.certificate
        self.assertIn(key, context)
        self.assertIn(value, context[key])

    def test_vpn_context_key_path(self):
        context, vpnclient = self._get_vpn_context()
        vpn_pk = vpnclient.vpn.pk.hex
        key = 'key_path_{0}'.format(vpn_pk)
        filename = 'key-{0}.pem'.format(vpn_pk)
        value = '{0}/{1}'.format(app_settings.CERT_PATH, filename)
        self.assertIn(key, context)
        self.assertIn(value, context[key])

    def test_vpn_context_key_contents(self):
        context, vpnclient = self._get_vpn_context()
        vpn_pk = vpnclient.vpn.pk.hex
        key = 'key_contents_{0}'.format(vpn_pk)
        value = vpnclient.cert.private_key
        self.assertIn(key, context)
        self.assertIn(value, context[key])

    def test_vpn_context_no_cert(self):
        vpn = self._create_vpn()
        t = self._create_template(type='vpn', auto_cert=False, vpn=vpn)
        c = Config(name='test-create-cert-false',
                   backend='netjsonconfig.OpenWrt',
                   mac_address=self.TEST_MAC_ADDRESS,
                   config={'general': {}})
        c.full_clean()
        c.save()
        c.templates.add(t)
        c.save()
        context = c.get_context()
        vpn_id = vpn.pk.hex
        cert_path_key = 'cert_path_{0}'.format(vpn_id)
        cert_contents_key = 'cert_contents_{0}'.format(vpn_id)
        key_path_key = 'key_path_{0}'.format(vpn_id)
        key_contents_key = 'key_contents_{0}'.format(vpn_id)
        ca_path_key = 'ca_path_{0}'.format(vpn_id)
        ca_contents_key = 'ca_contents_{0}'.format(vpn_id)
        self.assertNotIn(cert_path_key, context)
        self.assertNotIn(cert_contents_key, context)
        self.assertNotIn(key_path_key, context)
        self.assertNotIn(key_contents_key, context)
        self.assertIn(ca_path_key, context)
        self.assertIn(ca_contents_key, context)
