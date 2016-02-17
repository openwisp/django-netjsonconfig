from copy import deepcopy

from django.core.exceptions import ValidationError
from django.db.transaction import atomic
from django.test import TestCase

from netjsonconfig import OpenWrt

from ..models import Config, Template


class TestConfig(TestCase):
    """
    tests for Config model
    """
    fixtures = ['test_templates']
    maxDiff = None
    TEST_KEY = '00:11:22:33:44:55'

    def test_str(self):
        d = Config(name='test')
        self.assertEqual(str(d), 'test')

    def test_config_not_none(self):
        c = Config(name='test', backend='netjsonconfig.OpenWrt', config=None)
        c.full_clean()
        self.assertEqual(c.config, {})

    def test_backend_class(self):
        d = Config(name='test', backend='netjsonconfig.OpenWrt')
        self.assertIs(d.backend_class, OpenWrt)

    def test_backend_instance(self):
        config = {'general': {'hostname': 'config'}}
        d = Config(name='test', backend='netjsonconfig.OpenWrt', config=config)
        self.assertIsInstance(d.backend_instance, OpenWrt)

    def test_validation(self):
        config = {'interfaces': {'invalid': True}}
        d = Config(name='test',
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
                   backend='netjsonconfig.OpenWrt',
                   config={'general': {'hostname': 'json-test'}},
                   key=self.TEST_KEY)
        d.full_clean()
        d.save()
        d.templates.add(dhcp)
        d.templates.add(radio)
        full_config = {
            'type': 'DeviceConfiguration',
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
                   config={'general': {}},
                   key=self.TEST_KEY)
        c.full_clean()
        c.save()
        expected = {
            'type': 'DeviceConfiguration',
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
                'name': '{{ name }}'
            }
        }
        c = Config(name='context-test',
                   backend='netjsonconfig.OpenWrt',
                   config=config,
                   key=self.TEST_KEY)
        output = c.backend_instance.render()
        self.assertIn(str(c.id), output)
        self.assertIn(c.key, output)
        self.assertIn(c.name, output)

    def test_security_error(self):
        c = Config(name='security-error',
                   backend='netjsonconfig.OpenWrt',
                   config={'general': {'desc': '{{ 1000**10000 }}'}},
                   key=self.TEST_KEY)
        with self.assertRaises(ValidationError):
            c.full_clean()
