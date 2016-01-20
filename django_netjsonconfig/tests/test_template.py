from django.test import TestCase
from django.core.exceptions import ValidationError

from netjsonconfig import OpenWrt

from ..models import Template, Config


class TestTemplate(TestCase):
    """
    tests for Template model
    """
    def _create_template(self):
        t = Template(**{
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
        })
        t.full_clean()
        t.save()
        return t

    def test_str(self):
        t = Template(name='test', backend='netjsonconfig.OpenWrt')
        self.assertEqual(str(t), '[OpenWRT] test')

    def test_backend_class(self):
        t = Template(name='test', backend='netjsonconfig.OpenWrt')
        self.assertIs(t.backend_class, OpenWrt)

    def test_backend_instance(self):
        config = {'general': {'hostname': 'template'}}
        t = Template(name='test', backend='netjsonconfig.OpenWrt', config=config)
        self.assertIsInstance(t.backend_instance, OpenWrt)

    def test_validation(self):
        config = {'interfaces': {'invalid': True}}
        t = Template(name='test', backend='netjsonconfig.OpenWrt', config=config)
        # ensure django ValidationError is raised
        with self.assertRaises(ValidationError):
            t.full_clean()

    def test_config_status_modified_after_change(self):
        t = self._create_template()
        c = Config(name='test-status',
                   backend='netjsonconfig.OpenWrt',
                   config={'general': {}})
        c.full_clean()
        c.save()
        c.templates.add(t)
        c.status = 'running'
        c.save()
        c.refresh_from_db()
        self.assertEqual(c.status, 'running')
        t.config['interfaces'][0]['name'] = 'eth1'
        t.full_clean()
        t.save()
        c.refresh_from_db()
        self.assertEqual(c.status, 'modified')

    def test_no_auto_hostname(self):
        t = self._create_template()
        self.assertNotIn('general', t.backend_instance.config)
        t.refresh_from_db()
        self.assertNotIn('general', t.config)
