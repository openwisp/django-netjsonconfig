from django.test import TestCase

from netjsonconfig import OpenWrt

from ..models import Template


class TestTemplate(TestCase):
    """
    tests for Template model
    """
    def test_str(self):
        t = Template(name='test', backend='netjsonconfig.OpenWrt')
        self.assertEqual(str(t), '[OpenWRT] test')

    def test_backend_class(self):
        t = Template(name='test', backend='netjsonconfig.OpenWrt')
        self.assertIs(t.backend_class, OpenWrt)

    def test_backend_instance(self):
        config = {'general':{'hostname':'template'}}
        t = Template(name='test', backend='netjsonconfig.OpenWrt', config=config)
        self.assertDictEqual(t.backend_instance.config, config)
