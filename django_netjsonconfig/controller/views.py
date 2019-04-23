from ..models import Device, Vpn
from .generics import (BaseDeviceChecksumView, BaseDeviceDownloadConfigView, BaseDeviceRegisterView,
                       BaseDeviceReportStatusView, BaseVpnChecksumView, BaseVpnDownloadConfigView)


class DeviceChecksumView(BaseDeviceChecksumView):
    model = Device


class DeviceDownloadConfigView(BaseDeviceDownloadConfigView):
    model = Device


class DeviceReportStatusView(BaseDeviceReportStatusView):
    model = Device


class DeviceRegisterView(BaseDeviceRegisterView):
    model = Device


class VpnChecksumView(BaseVpnChecksumView):
    model = Vpn


class VpnDownloadConfigView(BaseVpnDownloadConfigView):
    model = Vpn


device_checksum = DeviceChecksumView.as_view()
device_download_config = DeviceDownloadConfigView.as_view()
device_report_status = DeviceReportStatusView.as_view()
device_register = DeviceRegisterView.as_view()
vpn_checksum = VpnChecksumView.as_view()
vpn_download_config = VpnDownloadConfigView.as_view()
