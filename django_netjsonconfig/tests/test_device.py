from django.test import TestCase

from netjsonconfig import OpenWrt

from ..models import Device, Template


class TestDevice(TestCase):
    """
    tests for Device model
    """
    fixtures = ['test_templates']
    maxDiff = None

    def test_str(self):
        d = Device(name='test')
        self.assertEqual(str(d), 'test')

    def test_backend_class(self):
        d = Device(name='test', backend='netjsonconfig.OpenWrt')
        self.assertIs(d.backend_class, OpenWrt)

    def test_backend_instance(self):
        config = {'general':{'hostname':'device'}}
        d = Device(name='test', backend='netjsonconfig.OpenWrt', config=config)
        self.assertDictEqual(d.backend_instance.config, config)

    def test_json(self):
        dhcp = Template.objects.get(name='dhcp')
        radio = Template.objects.get(name='radio0')
        d = Device(name='test',
                   backend='netjsonconfig.OpenWrt',
                   config={'general':{'hostname':'json-test'}})
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
        self.assertDictEqual(d.json(dict=True), full_config)
        json_string = d.json()
        self.assertIn('json-test', json_string)
        self.assertIn('eth0', json_string)
        self.assertIn('radio0', json_string)
