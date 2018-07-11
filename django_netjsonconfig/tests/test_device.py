from django.core.exceptions import ValidationError
from django.test import TestCase

from . import CreateConfigMixin
from ..models import Config, Device
from ..validators import device_name_validator, mac_address_validator


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
                                status='running')
        self.assertEqual(c.status, 'running')
        c.device.name = 'test-status-modified'
        c.device.full_clean()
        c.device.save()
        c.refresh_from_db()
        self.assertEqual(c.status, 'modified')

    def test_key_validator(self):
        d = Device(name='test',
                   mac_address=self.TEST_MAC_ADDRESS)
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
