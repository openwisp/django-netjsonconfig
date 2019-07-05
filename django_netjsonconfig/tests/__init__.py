"""
test utilities shared among test classes
these mixins are reused also in openwisp2
change with care.
"""
from uuid import uuid4

from django_x509.tests import TestX509Mixin


class CreateDeviceMixin(object):
    TEST_MAC_ADDRESS = '00:11:22:33:44:55'

    def _create_device(self, **kwargs):
        options = dict(name='test-device',
                       mac_address=self.TEST_MAC_ADDRESS,
                       hardware_id=str(uuid4().hex),
                       model='TP-Link TL-WDR4300 v1',
                       os='LEDE Reboot 17.01-SNAPSHOT r3313-c2999ef')
        options.update(kwargs)
        d = self.device_model(**options)
        d.full_clean()
        d.save()
        return d

    def _create_device_config(self, device_opts=None, config_opts=None):
        device_opts = device_opts or {}
        config_opts = config_opts or {}
        device_opts['name'] = 'test'
        d = self._create_device(**device_opts)
        config_opts['device'] = d
        self._create_config(**config_opts)
        return d


class CreateConfigMixin(CreateDeviceMixin):
    TEST_KEY = 'w1gwJxKaHcamUw62TQIPgYchwLKn3AA0'

    def _create_config(self, **kwargs):
        options = dict(backend='netjsonconfig.OpenWrt',
                       config={'general': {}})
        options.update(kwargs)
        if 'device' not in kwargs:
            options['device'] = self._create_device(name='test-device')
        c = self.config_model(**options)
        c.full_clean()
        c.save()
        return c


class CreateTemplateMixin(object):
    _import_template_data = {
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
        "name": "public",
        "backend": "netjsonconfig.OpenWrt",
        "type": "vpn",
        "sharing": "public",
        "key": None,
        "auto_cert": False,
        "description": "some description",
    }

    def _create_template(self, **kwargs):
        model_kwargs = {
            "name": "test-template",
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
        t = self.template_model(**model_kwargs)
        t.full_clean()
        t.save()
        return t


class CreateTemplateSubscriptionMixin(object):
    def _create_subscription(self, **kwargs):
        model_kwargs = {
            'template': self._create_template(),
            'subscriber': 'http://test.com',
            'subscribe': True
        }
        model_kwargs.update(kwargs)
        s = self.subscription_model(**model_kwargs)
        s.full_clean()
        s.save()
        return s


class CreateVpnMixin(object):
    _dh = """-----BEGIN DH PARAMETERS-----
MIGHAoGBAMkiqC2kAkjhysnuBORxJgDMdq3JrvaNh1kZW0IkFiyLRyhtYf92atP4
ycYELVoRZoRZ8zp2Y2L71vHRNx5okiXZ1xRWDfEVp7TFVc+oCTTRwJqyq21/DJpe
Qt01H2yL7CvdEUi/gCUJNS9Jm40248nwKgyrwyoS3SjY49CAcEYLAgEC
-----END DH PARAMETERS-----"""
    _vpn_config = {
        "openvpn": [
            {
                "ca": "ca.pem",
                "cert": "cert.pem",
                "dev": "tap0",
                "dev_type": "tap",
                "dh": "dh.pem",
                "key": "key.pem",
                "mode": "server",
                "name": "example-vpn",
                "proto": "udp",
                "tls_server": True
            }
        ]
    }

    def _create_vpn(self, ca_options={}, **kwargs):
        options = dict(name='test',
                       host='vpn1.test.com',
                       ca=None,
                       backend='django_netjsonconfig.vpn_backends.OpenVpn',
                       config=self._vpn_config,
                       dh=self._dh)
        options.update(**kwargs)
        if not options['ca']:
            options['ca'] = self._create_ca(**ca_options)
        vpn = self.vpn_model(**options)
        vpn.full_clean()
        vpn.save()
        return vpn


class TestVpnX509Mixin(CreateVpnMixin, TestX509Mixin):
    pass
