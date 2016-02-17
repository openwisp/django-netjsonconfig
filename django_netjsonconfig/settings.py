from django.conf import settings

DEFAULT_BACKENDS = [
    ('netjsonconfig.OpenWrt', 'OpenWRT'),
    ('netjsonconfig.OpenWisp', 'OpenWISP'),
]

BACKENDS = DEFAULT_BACKENDS + getattr(settings, 'NETJSONCONFIG_BACKENDS', [])
REGISTRATION_ENABLED = getattr(settings, 'NETJSONCONFIG_REGISTRATION_ENABLED', True)
SHARED_SECRET = getattr(settings, 'NETJSONCONFIG_SHARED_SECRET', '')
CONTEXT = getattr(settings, 'NETJSONCONFIG_CONTEXT', {})
