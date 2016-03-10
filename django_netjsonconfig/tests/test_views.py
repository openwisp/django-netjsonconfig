from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase

User = get_user_model()


class TestViews(TestCase):
    """
    tests for django_netjsonconfig.views
    """
    fixtures = ['test_users']

    def test_schema_403(self):
        response = self.client.get(reverse('netjsonconfig:schema'))
        self.assertEqual(response.status_code, 403)
        self.assertIn('error', response.json())

    def test_schema_200(self):
        self.client.force_login(User.objects.get(pk=1))
        response = self.client.get(reverse('netjsonconfig:schema'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('netjsonconfig.OpenWrt', response.json())
