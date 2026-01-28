"""REST request builders for National Grid."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from .rest import RestRequest

AMI_INTERVAL_READS_PATH = (
    "amiadapter-cu-uwp-sys/v1/interval/reads/{premise_number}/{service_point_number}"
)


@dataclass(slots=True)
class RealtimeMeterInfo:
    """Parameters for the interval reads REST endpoint."""

    premise_number: str
    service_point_number: str
    start_datetime: str
    params: Mapping[str, str] | None = None
    headers: Mapping[str, str] | None = None

    def to_request(self) -> RestRequest:
        if not self.start_datetime:
            raise ValueError("start_datetime is required for interval reads requests.")
        merged_params: dict[str, str] = {"StartDateTime": self.start_datetime}
        if self.params:
            merged_params.update(self.params)
        _validate_start_datetime(merged_params.get("StartDateTime", ""))
        path = AMI_INTERVAL_READS_PATH.format(
            premise_number=self.premise_number,
            service_point_number=self.service_point_number,
        )
        return RestRequest(
            method="GET",
            path_or_url=path,
            params=merged_params,
            headers=self.headers,
        )


def realtime_meter_info_request(
    *,
    premise_number: str,
    service_point_number: str,
    start_datetime: str,
    params: Mapping[str, str] | None = None,
    headers: Mapping[str, str] | None = None,
) -> RestRequest:
    """Build the interval reads REST request."""

    return RealtimeMeterInfo(
        premise_number=premise_number,
        service_point_number=service_point_number,
        start_datetime=start_datetime,
        params=params,
        headers=headers,
    ).to_request()


def _validate_start_datetime(value: str) -> None:
    if not value:
        raise ValueError("StartDateTime is required and must be YYYY-MM-DD hh:mm:ss.")
    try:
        datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise ValueError(
            "StartDateTime must be YYYY-MM-DD hh:mm:ss, e.g. 2024-01-01 00:00:00"
        ) from exc
