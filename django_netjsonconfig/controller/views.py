from ..models import Config
from .generics import (BaseChecksumView, BaseDownloadConfigView,
                       BaseRegisterView, BaseReportStatusView)


class ChecksumView(BaseChecksumView):
    model = Config


class DownloadConfigView(BaseDownloadConfigView):
    model = Config


class ReportStatusView(BaseReportStatusView):
    model = Config


class RegisterView(BaseRegisterView):
    model = Config


checksum = ChecksumView.as_view()
download_config = DownloadConfigView.as_view()
report_status = ReportStatusView.as_view()
register = RegisterView.as_view()
