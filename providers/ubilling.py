"""Alert provider API ubilling.net.ua"""
import logging
import requests
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

    def request(self) -> AlertProviderResult:
        result = AlertProviderResult(status=ProviderResponseStatus.INIT)
        try:
            logger.debug(f"Sending GET request to {self.BASE_URL} ...")
            response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)

            if response.status_code == 200:
                try:
                    result.raw_data = response.json()
                except requests.exceptions.JSONDecodeError:
                    result.status = ProviderResponseStatus.RESPONSE_PARSE_ERROR
                    return result
                result.status = ProviderResponseStatus.SUCCESS
                return result

            result.status = ProviderResponseStatus.API_ERROR
            result.error_code = response.status_code
            return result
        except requests.RequestException as exc:
            logger.exception(exc)
            result.status = ProviderResponseStatus.NETWORK_ERROR
        return result

    def extract_alert_state(self, result: AlertProviderResult) -> None:
        try:
            raw_data = result.raw_data
            if raw_data is None:
                logger.error("Empty response from API")
                result.status = ProviderResponseStatus.RESPONSE_EMPTY
                return
            logger.info(f"Response json: {raw_data}")
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
                        alert=active_alert, level=AirAlertLevel.UNKNOWN, since=state_since
                    )
                    alert_states[uid] = alert_state
        except KeyError as ex:
            logger.exception(f"Error while parsing response from server: {ex}")
            result.status = ProviderResponseStatus.RESPONSE_PARSE_ERROR
            return
        result.states = alert_states
