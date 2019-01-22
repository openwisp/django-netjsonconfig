from ..models import Device, Vpn
from .generics import (BaseRegisterView, BaseReportStatusView, DeviceChecksumView, DeviceDownloadConfigView,
                       VpnChecksumView, VpnDownloadConfigView)


class DeviceChecksumView(DeviceChecksumView):
    model = Device


class DeviceDownloadConfigView(DeviceDownloadConfigView):
    model = Device


class DeviceReportStatusView(BaseReportStatusView):
    model = Device


class DeviceRegisterView(BaseRegisterView):
    model = Device


class VpnChecksumView(VpnChecksumView):
    model = Vpn


class VpnDownloadConfigView(VpnDownloadConfigView):
    model = Vpn


device_checksum = DeviceChecksumView.as_view()
device_download_config = DeviceDownloadConfigView.as_view()
device_report_status = DeviceReportStatusView.as_view()
device_register = DeviceRegisterView.as_view()
vpn_checksum = VpnChecksumView.as_view()
vpn_download_config = VpnDownloadConfigView.as_view()
