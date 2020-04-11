from django.dispatch import Signal

checksum_requested = Signal(providing_args=['instance', 'request'])
config_download_requested = Signal(providing_args=['instance', 'request'])
config_modified = Signal(providing_args=['device', 'config'])
