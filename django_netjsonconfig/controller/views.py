from ..models import Device
from .generics import (BaseChecksumView, BaseDownloadConfigView,
                       BaseRegisterView, BaseReportStatusView)


class ChecksumView(BaseChecksumView):
    model = Device


class DownloadConfigView(BaseDownloadConfigView):
    model = Device


class ReportStatusView(BaseReportStatusView):
    model = Device


class RegisterView(BaseRegisterView):
    model = Device


checksum = ChecksumView.as_view()
download_config = DownloadConfigView.as_view()
report_status = ReportStatusView.as_view()
register = RegisterView.as_view()
