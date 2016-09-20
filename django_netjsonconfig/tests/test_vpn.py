from django.core.exceptions import ValidationError
from django.test import TestCase

from django_x509.models import Ca, Cert

from . import CreateTemplateMixin, CreateVpnMixin
from ..models import Config, Vpn, VpnClient
from ..vpn_backends import OpenVpn


class TestVpn(CreateVpnMixin, CreateTemplateMixin, TestCase):
    """
    tests for Vpn model
    """
    maxDiff = None

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
                backend='django_netjsonconfig.vpn_backends.OpenVpn',
                config=None,
                dh=self._dh)
        try:
            v.full_clean()
        except ValidationError:
            pass
        self.assertEqual(v.config, {})

    def test_backend_class(self):
        v = Vpn(name='test',
                host='vpn1.test.com',
                ca=self._create_ca(),
                backend='django_netjsonconfig.vpn_backends.OpenVpn')
        self.assertIs(v.backend_class, OpenVpn)

    def test_backend_instance(self):
        v = Vpn(name='test',
                host='vpn1.test.com',
                ca=self._create_ca(),
                backend='django_netjsonconfig.vpn_backends.OpenVpn',
                config={})
        self.assertIsInstance(v.backend_instance, OpenVpn)

    def test_validation(self):
        config = {'openvpn': {'invalid': True}}
        v = Vpn(name='test',
                host='vpn1.test.com',
                ca=self._create_ca(),
                backend='django_netjsonconfig.vpn_backends.OpenVpn',
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
                   mac_address='00:11:22:33:44:55',
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

    def test_vpn_client_auto_cert_deletes_cert(self):
        vpn = self._create_vpn()
        t = self._create_template(name='vpn-test',
                                  type='vpn',
                                  vpn=vpn,
                                  auto_cert=True)
        c = Config(name='test-create-cert',
                   mac_address='00:11:22:33:44:55',
                   backend='netjsonconfig.OpenWrt',
                   config={'general': {}})
        c.full_clean()
        c.save()
        c.templates.add(t)
        vpnclient = c.vpnclient_set.first()
        cert_pk = vpnclient.cert.pk
        self.assertEqual(Cert.objects.filter(pk=cert_pk).count(), 1)
        c.delete()
        self.assertEqual(VpnClient.objects.filter(pk=vpnclient.pk).count(), 0)
        self.assertEqual(Cert.objects.filter(pk=cert_pk).count(), 0)

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
                  backend='django_netjsonconfig.vpn_backends.OpenVpn')
        try:
            vpn.full_clean()
        except ValidationError as e:
            self.assertIn('cert', e.message_dict)
        else:
            self.fail('Mismatch between ca and cert but '
                      'ValidationError not raised')

    def test_auto_client(self):
        vpn = self._create_vpn()
        auto = vpn.auto_client()
        context_keys = vpn._get_auto_context_keys()
        for key in context_keys.keys():
            context_keys[key] = '{{%s}}' % context_keys[key]
        control = vpn.backend_class.auto_client(host=vpn.host,
                                                server=self._vpn_config['openvpn'][0],
                                                **context_keys)
        control['files'] = [
            {
                'path': context_keys['ca_path'],
                'mode': '0644',
                'contents': context_keys['ca_contents']
            },
            {
                'path': context_keys['cert_path'],
                'mode': '0644',
                'contents': context_keys['cert_contents']
            },
            {
                'path': context_keys['key_path'],
                'mode': '0644',
                'contents': context_keys['key_contents']
            }
        ]
        self.assertDictEqual(auto, control)

    def test_auto_client_auto_cert_False(self):
        vpn = self._create_vpn()
        auto = vpn.auto_client(auto_cert=False)
        context_keys = vpn._get_auto_context_keys()
        for key in context_keys.keys():
            context_keys[key] = '{{%s}}' % context_keys[key]
        for key in ['cert_path', 'cert_contents', 'key_path', 'key_contents']:
            del context_keys[key]
        control = vpn.backend_class.auto_client(host=vpn.host,
                                                server=self._vpn_config['openvpn'][0],
                                                **context_keys)
        control['files'] = [
            {
                'path': context_keys['ca_path'],
                'mode': '0644',
                'contents': context_keys['ca_contents']
            }
        ]
        self.assertDictEqual(auto, control)

    def test_get_auto_context_keys(self):
        vpn = self._create_vpn()
        keys = vpn._get_auto_context_keys()
        pk = vpn.pk.hex
        control = {
            'ca_path': 'ca_path_{0}'.format(pk),
            'ca_contents': 'ca_contents_{0}'.format(pk),
            'cert_path': 'cert_path_{0}'.format(pk),
            'cert_contents': 'cert_contents_{0}'.format(pk),
            'key_path': 'key_path_{0}'.format(pk),
            'key_contents': 'key_contents_{0}'.format(pk),
        }
        self.assertEqual(keys, control)

    def test_get_context(self):
        v = self._create_vpn()
        expected = {
            'ca': v.ca.certificate,
            'cert': v.cert.certificate,
            'key': v.cert.private_key,
            'dh': v.dh
        }
        self.assertEqual(v.get_context(), expected)

    def test_dh(self):
        v = self._create_vpn()
        v.dh = None
        v.save()
        self.assertIsNotNone(v.dh)
        self.assertNotEqual(v.dh.decode('utf8'), '')
        self.assertIn('-----BEGIN DH PARAMETERS-----', v.dh.decode('utf8'))
        self.assertIn('-----END DH PARAMETERS-----', v.dh.decode('utf8'))

    def test_context_empty(self):
        v = Vpn()
        self.assertEqual(v.get_context(), {})
