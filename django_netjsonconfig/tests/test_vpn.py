# from django.contrib.auth import get_user_model
# from django.core.urlresolvers import reverse
from django.test import TestCase

from django_x509.models import Ca

from ..models import Vpn


class TestVpn(TestCase):
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

    def test_automatic_cert_creation(self):
        vpn = Vpn(name='test',
                  ca=self._create_ca(),
                  backend='netjsonconfig.OpenVpn')
        vpn.full_clean()
        vpn.save()
        self.assertIsNotNone(vpn.cert)
        server_extensions = [
            {
                "name": "nsCertType",
                "value": "server",
                "critical": False
            }
        ]
        self.assertEqual(vpn.cert.extensions, server_extensions)
