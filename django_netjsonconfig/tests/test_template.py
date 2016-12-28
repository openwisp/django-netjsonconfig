from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase

from netjsonconfig import OpenWrt

from . import CreateTemplateMixin, CreateVpnMixin
from ..models import Config, Template


class TestTemplate(CreateTemplateMixin, CreateVpnMixin, TestCase):
    """
    tests for Template model
    """
    TEST_MAC_ADDRESS = '00:11:22:33:44:55'

    def test_str(self):
        t = Template(name='test', backend='netjsonconfig.OpenWrt')
        self.assertEqual(str(t), '[Generic-OpenWRT] test')

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
        c = Config(name='test-status',
                   backend='netjsonconfig.OpenWrt',
                   mac_address=self.TEST_MAC_ADDRESS,
                   config={'general': {}})
        c.full_clean()
        c.save()
        c.templates.add(t)
        c.status = 'running'
        c.save()
        c.refresh_from_db()
        self.assertEqual(c.status, 'running')
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
        t = self._create_template(default=True)
        c = Config(name='test-default',
                   backend='netjsonconfig.OpenWrt',
                   mac_address=self.TEST_MAC_ADDRESS)
        c.full_clean()
        c.save()
        self.assertEqual(c.templates.count(), 1)
        self.assertEqual(c.templates.first().id, t.id)

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
        c = Config(name='test-var',
                   backend='netjsonconfig.OpenWrt',
                   mac_address=self.TEST_MAC_ADDRESS)
        c.full_clean()
        c.save()
        c.templates.add(t)
        # clear cache
        del c.backend_instance
        output = c.backend_instance.render()
        vpnserver1 = settings.NETJSONCONFIG_CONTEXT['vpnserver1']
        self.assertIn(vpnserver1, output)
