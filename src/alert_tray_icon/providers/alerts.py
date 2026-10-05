"""Alert provider API alerts.in.ua"""

import logging
import datetime

import requests
from requests import Response
from pydantic import ValidationError

from .base import (
    AlertState,
    AirAlertLevel,
    AlertProvider,
    AlertProviderResult,
    ProviderResponseStatus,
)
from .models import ActiveAlertsResponse, AlertsInUaLocations

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

        alert_states: dict[int, AlertState | None] = {}

        for active_alert in active_alerts_data.alerts:
            uid = int(active_alert.location_uid)
            now = datetime.datetime.now(datetime.UTC)
            dt_since = datetime.datetime.strptime(
                active_alert.started_at, "%Y-%m-%dT%H:%M:%S.%f%z"
            )
            datetime_string = "%H:%M"
            if now - dt_since > datetime.timedelta(days=1):
                datetime_string += " %d.%m.%Y"

            dt_since = dt_since.astimezone()
            state_since = dt_since.strftime(datetime_string)

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

        result.alerts_by_location = alert_states


class ProxyAlertsInUaProvider(AlertsInUaProvider):
    """Alert provider alerts.in.ua via proxy"""

    BASE_URL: str = "https://proxy-alerts-server.fastapicloud.dev/provider/alerts_in_ua"
    LOCATIONS_URL: str = (
        "https://proxy-alerts-server.fastapicloud.dev/provider/alerts_in_ua/locations"
    )

    def request_locations(self) -> AlertsInUaLocations:
        """Make API call to request locations available to monitor alerts on alerts.in.ua

        :raises RuntimeError: When API response not received, or response code is not OK, or json could not be parsed,
                When provided JSON data from API could not be validated
        :returns: AlertsInUaLocations object
        """
        response: Response | None = None
        for _ in range(3):
            try:
                logger.debug("Sending GET request to %s ...", self.LOCATIONS_URL)
                response = requests.get(self.LOCATIONS_URL, timeout=3)
                break
            except requests.RequestException as exc:
                logger.exception(exc)
        if response is None or response.status_code != 200:
            raise RuntimeError("Could not received locations")

        try:
            raw_data = response.json()
        except requests.exceptions.JSONDecodeError as exc:
            raise RuntimeError("Could not parse data of received locations") from exc

        try:
            result = AlertsInUaLocations.model_validate(raw_data)
        except ValidationError as exc:
            logger.exception(exc)
            raise RuntimeError("Invalid structure of location data") from exc

        return result
