from django.conf import settings

DEFAULT_BACKENDS = [
    ('netjsonconfig.OpenWrt', 'OpenWRT'),
    ('netjsonconfig.OpenWisp', 'OpenWISP'),
]

BACKENDS = DEFAULT_BACKENDS + getattr(settings, 'NETJSONCONFIG_BACKENDS', [])
