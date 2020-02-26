from hashlib import md5
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase

from .. import settings as app_settings
from ..models import Config, Device
from ..validators import device_name_validator, mac_address_validator
from . import CreateConfigMixin


class TestDevice(CreateConfigMixin, TestCase):
    """
    tests for Device model
    """
    config_model = Config
    device_model = Device

    def test_str(self):
        d = Device(name='test')
        self.assertEqual(str(d), 'test')

    def test_mac_address_validator(self):
        d = Device(name='test',
                   key=self.TEST_KEY)
        bad_mac_addresses_list = [
            '{0}:BB:CC'.format(self.TEST_MAC_ADDRESS),
            'AA:BB:CC:11:22033',
            'AA BB CC 11 22 33'
        ]
        for mac_address in bad_mac_addresses_list:
            d.mac_address = mac_address
            try:
                d.full_clean()
            except ValidationError as e:
                self.assertIn('mac_address', e.message_dict)
                self.assertEqual(mac_address_validator.message,
                                 e.message_dict['mac_address'][0])
            else:
                self.fail('ValidationError not raised for "{0}"'.format(mac_address))

    def test_config_status_modified(self):
        c = self._create_config(device=self._create_device(),
                                status='applied')
        self.assertEqual(c.status, 'applied')
        c.device.name = 'test-status-modified'
        c.device.full_clean()
        c.device.save()
        c.refresh_from_db()
        self.assertEqual(c.status, 'modified')

    def test_key_validator(self):
        d = Device(name='test',
                   mac_address=self.TEST_MAC_ADDRESS,
                   hardware_id='1234')
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

    def test_backend(self):
        d = self._create_device()
        self.assertIsNone(d.backend)
        c = self._create_config(device=d)
        self.assertIsNotNone(d.backend)
        self.assertEqual(d.backend, c.get_backend_display())

    def test_status(self):
        d = self._create_device()
        self.assertEqual(d.status, None)
        c = self._create_config(device=d)
        self.assertIsNotNone(d.status)
        self.assertEqual(d.status, c.get_status_display())

    def test_config_model(self):
        d = Device()
        self.assertIs(d.get_config_model(), Config)

    def test_config_model_static(self):
        self.assertIs(Device.get_config_model(), Config)

    def test_get_default_templates(self):
        d = self._create_device()
        self.assertEqual(d.get_default_templates().count(),
                         Config().get_default_templates().count())
        self._create_config(device=d)
        self.assertEqual(d.get_default_templates().count(),
                         Config().get_default_templates().count())

    def test_bad_hostnames(self):
        bad_host_name_list = [
            'test device',
            'openwisp..mydomain.com',
            'openwisp,mydomain.test',
            '{0}:BB:CC'.format(self.TEST_MAC_ADDRESS),
            'AA:BB:CC:11:22033'
        ]
        for host in bad_host_name_list:
            try:
                self._create_device(name=host)
            except ValidationError as e:
                self.assertIn('name', e.message_dict)
                self.assertEqual(device_name_validator.message,
                                 e.message_dict['name'][0])
            else:
                self.fail('ValidationError not raised for "{0}"'.format(host))

    def test_add_device_with_context(self):
        d = self._create_device()
        d.save()
        c = self._create_config(device=d, config={
            "openwisp": [
                {
                    "config_name": "controller",
                    "config_value": "http",
                    "url": "http://controller.examplewifiservice.com",
                    "interval": "{{ interval }}",
                    "verify_ssl": "1",
                    "uuid": "UUID",
                    "key": self.TEST_KEY
                }
            ]
        }, context={
            'interval': '60'
        })
        self.assertEqual(c.json(dict=True)['openwisp'][0]['interval'],
                         '60')

    def test_get_context_with_config(self):
        d = self._create_device()
        c = self._create_config(device=d)
        self.assertEqual(d.get_context(), c.get_context())

    def test_get_context_without_config(self):
        d = self._create_device()
        self.assertEqual(d.get_context(), Config(device=d).get_context())

    @mock.patch('django_netjsonconfig.settings.CONSISTENT_REGISTRATION', False)
    def test_generate_random_key(self):
        d = self.device_model(name='test_generate_key',
                              mac_address='00:11:22:33:44:55')
        self.assertIsNone(d.key)
        # generating key twice shall not yield same result
        self.assertNotEqual(d.generate_key(app_settings.SHARED_SECRET),
                            d.generate_key(app_settings.SHARED_SECRET))

    @mock.patch('django_netjsonconfig.settings.CONSISTENT_REGISTRATION', True)
    @mock.patch('django_netjsonconfig.settings.HARDWARE_ID_ENABLED', False)
    def test_generate_consistent_key_mac_address(self):
        d = self.device_model(name='test_generate_key',
                              mac_address='00:11:22:33:44:55')
        self.assertIsNone(d.key)
        string = '{}+{}'.format(d.mac_address, app_settings.SHARED_SECRET).encode('utf-8')
        expected = md5(string).hexdigest()
        key = d.generate_key(app_settings.SHARED_SECRET)
        self.assertEqual(key, expected)
        self.assertEqual(key, d.generate_key(app_settings.SHARED_SECRET))

    @mock.patch('django_netjsonconfig.settings.CONSISTENT_REGISTRATION', True)
    @mock.patch('django_netjsonconfig.settings.HARDWARE_ID_ENABLED', True)
    def test_generate_consistent_key_mac_hardware_id(self):
        d = self.device_model(name='test_generate_key',
                              mac_address='00:11:22:33:44:55',
                              hardware_id='1234')
        self.assertIsNone(d.key)
        string = '{}+{}'.format(d.hardware_id, app_settings.SHARED_SECRET).encode('utf-8')
        expected = md5(string).hexdigest()
        key = d.generate_key(app_settings.SHARED_SECRET)
        self.assertEqual(key, expected)
        self.assertEqual(key, d.generate_key(app_settings.SHARED_SECRET))
