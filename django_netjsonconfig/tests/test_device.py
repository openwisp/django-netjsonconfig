from django.core.exceptions import ValidationError
from django.test import TestCase

from . import CreateConfigMixin
from ..models import Config, Device


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
                   mac_address='WRONG',
                   key=self.TEST_KEY)
        try:
            d.full_clean()
        except ValidationError as e:
            self.assertIn('mac_address', e.message_dict)
        else:
            self.fail('ValidationError not raised')

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

    def test_last_ip(self):
        d = self._create_device()
        self.assertEqual(d.last_ip, None)
        c = self._create_config(device=d, last_ip='10.0.0.250')
        self.assertIsNotNone(d.last_ip)
        self.assertEqual(d.last_ip, c.last_ip)

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
            'openwisp,mydomain.test'
        ]
        for hosts in bad_host_name_list:
            try:
                self._create_device(name=hosts)
            except ValidationError as e:
                self.assertEqual(
                    'Must be a valid hostname.',
                    e.message_dict['name'][0]
                    )
