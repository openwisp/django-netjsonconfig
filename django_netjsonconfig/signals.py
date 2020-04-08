from django.dispatch import Signal

checksum_generated = Signal(providing_args=['device', 'vpn'])
config_downloaded = Signal(providing_args=['device', 'vpn'])
config_modified = Signal(providing_args=['device', 'config'])
