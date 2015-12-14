from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.transaction import atomic

from netjsonconfig import OpenWrt

from ..models import Device, Template


class TestDevice(TestCase):
    """
    tests for Device model
    """
    fixtures = ['test_templates']
    maxDiff = None
    TEST_KEY = '00:11:22:33:44:55'

    def test_str(self):
        d = Device(name='test')
        self.assertEqual(str(d), 'test')

    def test_backend_class(self):
        d = Device(name='test', backend='netjsonconfig.OpenWrt')
        self.assertIs(d.backend_class, OpenWrt)

    def test_backend_instance(self):
        config = {'general':{'hostname':'device'}}
        d = Device(name='test', backend='netjsonconfig.OpenWrt', config=config)
        self.assertIsInstance(d.backend_instance, OpenWrt)

    def test_validation(self):
        config = {'interfaces': {'invalid': True}}
        d = Device(name='test',
                   backend='netjsonconfig.OpenWrt',
                   config=config,
                   key=self.TEST_KEY)
        # ensure django ValidationError is raised
        with self.assertRaises(ValidationError):
            d.full_clean()

    def test_json(self):
        dhcp = Template.objects.get(name='dhcp')
        radio = Template.objects.get(name='radio0')
        d = Device(name='test',
                   backend='netjsonconfig.OpenWrt',
                   config={'general':{'hostname':'json-test'}},
                   key=self.TEST_KEY)
        d.full_clean()
        d.save()
        d.templates.add(dhcp)
        d.templates.add(radio)
        full_config = {
            'type': 'DeviceConfiguration',
            'general': {
                'hostname':'json-test'
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
        # if device and template have a conflicting non-unique item
        # that violates the schema, the system should not allow
        # the assignment and raise an IntegrityError
        config = {
            "files": [
                {
                    "path": "/test",
                    "contents": "test"
                }
            ]
        }
        kwargs = dict(backend='netjsonconfig.OpenWrt',
                      config=config)
        t = Template(name='files', **kwargs)
        t.full_clean()
        t.save()
        d = Device(name='test', key=self.TEST_KEY, **kwargs)
        d.full_clean()
        d.save()
        with atomic():
            try:
                d.templates.add(t)
            except ValidationError as e:
                pass
            else:
                self.fail('ValidationError not raised')
        t.config['files'][0]['path'] = '/test2'
        d.templates.add(t)
