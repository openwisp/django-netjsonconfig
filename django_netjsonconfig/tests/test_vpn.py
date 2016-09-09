from django.core.exceptions import ValidationError
from django.test import TestCase
from django_x509.models import Ca, Cert
from netjsonconfig import OpenVpn

from . import CreateTemplateMixin, CreateVpnMixin
from ..models import Config, Vpn, VpnClient


class TestVpn(CreateVpnMixin, CreateTemplateMixin, TestCase):
    """
    tests for Vpn model
    """
    def _create_ca(self):
        ca = Ca(name='test-ca',
                key_length='2048',
                digest='sha256',
                country_code='IT',
                state='RM',
                city='Rome',
                organization='OpenWISP',
                email='test@test.com',
                common_name='openwisp.org')
        ca.full_clean()
        ca.save()
        return ca

    def test_config_not_none(self):
        v = Vpn(name='test',
                host='vpn1.test.com',
                ca=self._create_ca(),
                backend='netjsonconfig.OpenVpn',
                config=None)
        try:
            v.full_clean()
        except ValidationError:
            pass
        self.assertEqual(v.config, {})

    def test_backend_class(self):
        v = Vpn(name='test',
                host='vpn1.test.com',
                ca=self._create_ca(),
                backend='netjsonconfig.OpenVpn')
        self.assertIs(v.backend_class, OpenVpn)

    def test_backend_instance(self):
        v = Vpn(name='test',
                host='vpn1.test.com',
                ca=self._create_ca(),
                backend='netjsonconfig.OpenVpn',
                config={})
        self.assertIsInstance(v.backend_instance, OpenVpn)

    def test_validation(self):
        config = {'openvpn': {'invalid': True}}
        v = Vpn(name='test',
                host='vpn1.test.com',
                ca=self._create_ca(),
                backend='netjsonconfig.OpenVpn',
                config=config)
        # ensure django ValidationError is raised
        with self.assertRaises(ValidationError):
            v.full_clean()

    def test_json(self):
        v = self._create_vpn()
        self.assertDictEqual(v.json(dict=True), self._vpn_config)

    def test_automatic_cert_creation(self):
        vpn = self._create_vpn()
        self.assertIsNotNone(vpn.cert)
        server_extensions = [
            {
                "name": "nsCertType",
                "value": "server",
                "critical": False
            }
        ]
        self.assertEqual(vpn.cert.extensions, server_extensions)

    def test_vpn_client_unique_together(self):
        vpn = self._create_vpn()
        t = self._create_template(name='vpn-test', type='vpn', vpn=vpn)
        c = Config(name='test-create-cert',
                   backend='netjsonconfig.OpenWrt',
                   config={'general': {}})
        c.full_clean()
        c.save()
        c.templates.add(t)
        # one VpnClient instance has been automatically created
        # now try to create a duplicate
        client = VpnClient(vpn=vpn, config=c, auto_cert=True)
        try:
            client.full_clean()
        except ValidationError as e:
            self.assertIn('Vpn client with this Config and Vpn already exists.',
                          e.message_dict['__all__'])
        else:
            self.fail('unique_together clause not triggered')

    def test_vpn_cert_and_ca_mismatch(self):
        ca = self._create_ca()
        different_ca = self._create_ca()
        cert = Cert(name='test-cert-vpn',
                    ca=ca,
                    key_length='2048',
                    digest='sha256',
                    country_code='IT',
                    state='RM',
                    city='Rome',
                    organization='OpenWISP',
                    email='test@test.com',
                    common_name='openwisp.org')
        cert.full_clean()
        cert.save()
        vpn = Vpn(name='test',
                  host='vpn1.test.com',
                  ca=different_ca,
                  cert=cert,
                  backend='netjsonconfig.OpenVpn')
        try:
            vpn.full_clean()
        except ValidationError as e:
            self.assertIn('cert', e.message_dict)
        else:
            self.fail('Mismatch between ca and cert but '
                      'ValidationError not raised')
