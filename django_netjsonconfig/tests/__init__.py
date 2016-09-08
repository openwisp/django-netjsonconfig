from django_x509.models import Ca
from ..models import Template, Vpn


class CreateTemplateMixin(object):
    def _create_template(self, **kwargs):
        model_kwargs = {
            "name": "dhcp",
            "backend": "netjsonconfig.OpenWrt",
            "config": {
                "interfaces": [
                    {
                        "name": "eth0",
                        "type": "ethernet"
                    }
                ]
            }
        }
        model_kwargs.update(kwargs)
        t = Template(**model_kwargs)
        t.full_clean()
        t.save()
        return t


class CreateVpnMixin(object):
    def _create_vpn(self):
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
        vpn = Vpn(name='test',
                  host='vpn1.test.com',
                  ca=ca,
                  backend='netjsonconfig.OpenVpn')
        vpn.full_clean()
        vpn.save()
        return vpn
