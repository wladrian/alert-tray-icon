"""Alert provider API alerts.in.ua"""

import logging
import requests
from requests import Response
from pydantic import ValidationError

from .base import (
    AlertState,
    AirAlertLevel,
    AlertProvider,
    AlertProviderResult,
    RegionUID,
    ProviderResponseStatus,
)
from .models import ActiveAlertsResponse

logger = logging.getLogger("air_alert_icon")


class AlertsInUaProvider(AlertProvider):
    """Alert provider alerts.in.ua"""

    BASE_URL: str = "https://api.alerts.in.ua/v1/alerts/active.json"
    REQUEST_LIMIT: int = 10  # seconds
    TIMEOUT: int = 5  # seconds

    def _request(self) -> Response:
        response = requests.get(
            self.BASE_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=self.TIMEOUT,
        )
        return response

    def extract_alert_state(self, result: AlertProviderResult) -> None:
        raw_data = result.raw_data
        if AlertProvider.empty_provider_response(result):
            return
        if raw_data is None:
            return
        logger.info("Response json: %s", raw_data)
        result.source = "alerts.in.ua"
        try:
            active_alerts_data: ActiveAlertsResponse = ActiveAlertsResponse(**raw_data)
        except ValidationError as e:
            logger.exception("Error while parsing response from server: %s", e.errors())
            result.status = ProviderResponseStatus.RESPONSE_PARSE_ERROR
            return

        alert_states: dict[int, AlertState | None] = dict.fromkeys(
            [e.value for e in RegionUID], None
        )
        for active_alert in active_alerts_data.alerts:
            uid = int(active_alert.location_uid)
            if uid not in alert_states:
                continue

            state_since = active_alert.started_at
            level = (
                AirAlertLevel.RED
                if active_alert.alert_level == "red"
                else AirAlertLevel.UNKNOWN
            )
            level = (
                AirAlertLevel.YELLOW if active_alert.alert_level == "yellow" else level
            )

            alert_state = AlertState(
                alert=True,
                level=level,
                since=state_since,
            )
            alert_states[uid] = alert_state

        result.states = alert_states
