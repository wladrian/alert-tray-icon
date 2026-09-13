"""Alert provider API ubilling.net.ua"""

import logging
import requests
from requests import Response
from .base import (
    AlertState,
    AirAlertLevel,
    AlertProvider,
    AlertProviderResult,
    REGION_UID_BY_NAME,
    RegionUID,
    ProviderResponseStatus,
)

logger = logging.getLogger("air_alert_icon")


class UbillingProvider(AlertProvider):
    """Alert provider ubilling.net.ua"""

    BASE_URL: str = "https://ubilling.net.ua/aerialalerts/"
    REQUEST_LIMIT: int = 5  # seconds
    TIMEOUT: int = 5  # seconds

    def _request(self) -> Response:
        return requests.get(self.BASE_URL, timeout=self.TIMEOUT)

    def extract_alert_state(self, result: AlertProviderResult) -> None:
        raw_data = result.raw_data
        if UbillingProvider.empty_provider_response(result):
            return
        if raw_data is None:
            return

        try:
            logger.debug("Response json: %s", raw_data)
            result.source = raw_data["source"]
            regions_data = raw_data["states"]

            alert_states: dict[int, AlertState | None] = dict.fromkeys(
                [e.value for e in RegionUID], None
            )
            for region, alert_status in regions_data.items():
                if region in REGION_UID_BY_NAME:
                    uid = REGION_UID_BY_NAME[region]
                    active_alert = alert_status["alertnow"]
                    state_since = alert_status["changed"]
                    if state_since == "1970-01-01 03:00:00":
                        state_since = ""
                    alert_state = AlertState(
                        alert=active_alert,
                        level=AirAlertLevel.UNKNOWN,
                        since=state_since,
                    )
                    alert_states[uid] = alert_state
        except KeyError as ex:
            logger.exception("Error while parsing response from server: %s", ex)
            result.status = ProviderResponseStatus.RESPONSE_PARSE_ERROR
            return
        result.states = alert_states
