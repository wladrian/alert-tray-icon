"""Alert provider base class and related structures"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, IntEnum, auto

import requests
from requests import Response

logger = logging.getLogger("air_alert_icon")


class AirAlertLevel(Enum):
    """Air Alert levels Enum"""

    YELLOW = 1  # Single drone
    RED = 2  # Massive drone attack, or ballistic missile, or cruise missile
    UNKNOWN = 3  # Air alert but level could not be determined


class ProviderResponseStatus(IntEnum):
    """Provider Response Status Enum"""

    INIT = auto()
    SUCCESS = auto()
    API_ERROR = auto()
    NETWORK_ERROR = auto()
    RESPONSE_EMPTY = auto()
    RESPONSE_PARSE_ERROR = auto()
    UNKNOWN_PROVIDER_ERROR = auto()


class RegionUID(IntEnum):
    """Ukraine Regions UID Enum"""

    KHMELNYTSKYI = 3
    VINNYTSIA = 4
    RIVNE = 5
    VOLYN = 8
    DNIPROPETROVSK = 9
    ZHYTOMYR = 10
    ZAKARPATTIA = 11
    ZAPORIZHZHIA = 12
    IVANO_FRANKIVSK = 13
    KYIV_REGION = 14
    KIROVOHRAD = 15
    LUHANSK = 16
    MYKOLAIV = 17
    ODESA = 18
    POLTAVA = 19
    SUMY = 20
    TERNOPIL = 21
    KHARKIV = 22
    KHERSON = 23
    CHERKASY = 24
    CHERNIHIV = 25
    CHERNIVTSI = 26
    LVIV = 27
    DONETSK = 28
    CRIMEA = 29
    SEVASTOPOL = 30
    KYIV = 31


# Mapping spelling to Region UID
REGION_UID_BY_NAME = {
    "Хмельницька область": RegionUID.KHMELNYTSKYI,
    "Вінницька область": RegionUID.VINNYTSIA,
    "Рівненська область": RegionUID.RIVNE,
    "Волинська область": RegionUID.VOLYN,
    "Дніпропетровська область": RegionUID.DNIPROPETROVSK,
    "Житомирська область": RegionUID.ZHYTOMYR,
    "Закарпатська область": RegionUID.ZAKARPATTIA,
    "Запорізька область": RegionUID.ZAPORIZHZHIA,
    "Івано-Франківська область": RegionUID.IVANO_FRANKIVSK,
    "Київська область": RegionUID.KYIV_REGION,
    "Кіровоградська область": RegionUID.KIROVOHRAD,
    "Луганська область": RegionUID.LUHANSK,
    "Миколаївська область": RegionUID.MYKOLAIV,
    "Одеська область": RegionUID.ODESA,
    "Полтавська область": RegionUID.POLTAVA,
    "Сумська область": RegionUID.SUMY,
    "Тернопільська область": RegionUID.TERNOPIL,
    "Харківська область": RegionUID.KHARKIV,
    "Херсонська область": RegionUID.KHERSON,
    "Черкаська область": RegionUID.CHERKASY,
    "Чернігівська область": RegionUID.CHERNIHIV,
    "Чернівецька область": RegionUID.CHERNIVTSI,
    "Львівська область": RegionUID.LVIV,
    "Донецька область": RegionUID.DONETSK,
    "Автономна Республіка Крим": RegionUID.CRIMEA,
    "м. Севастополь": RegionUID.SEVASTOPOL,
    "м. Київ": RegionUID.KYIV,
}


@dataclass
class AlertState:
    """Alert State"""

    alert: bool
    level: AirAlertLevel
    since: str


@dataclass
class AlertProviderResult:
    """Alert Provider Resul. Encapsulate status of result, data and source"""

    status: ProviderResponseStatus
    source: str | None = None
    states: dict[int, AlertState | None] | None = None
    error_code: int | None = None
    error_message: str | None = None
    raw_data: dict | None = None


class AlertProvider(ABC):
    """Base class for Alert Provider"""

    BASE_URL: str
    REQUEST_LIMIT: int

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def _request(self) -> Response:
        """Make provider-specific API call

        :returns: Response object
        """

    def request(self) -> AlertProviderResult:
        """Make API call to Alert Data Provider

        :returns: AlertProviderResult object
        """
        result = AlertProviderResult(status=ProviderResponseStatus.INIT)
        logger.debug("Sending GET request to %s ...", self.BASE_URL)
        try:
            response = self._request()
        except requests.RequestException as exc:
            logger.exception(exc)
            result.status = ProviderResponseStatus.NETWORK_ERROR
            return result

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
        result.error_message = response.json()
        return result

    @abstractmethod
    def extract_alert_state(self, result: AlertProviderResult) -> None:
        """Convert provider response to application"""

    def get_data(self) -> AlertProviderResult:
        """Get alert data from provider"""
        result: AlertProviderResult = self.request()
        if result.status == ProviderResponseStatus.SUCCESS:
            self.extract_alert_state(result)
        return result

    @staticmethod
    def empty_provider_response(result: AlertProviderResult) -> bool:
        """Check AlertProviderResult for empty response
        :param result: AlertProviderResult
        :returns True if Alert API returned empty payload
        """
        if result.raw_data is None:
            result.status = ProviderResponseStatus.RESPONSE_EMPTY
            logger.error("Empty response from API.")
            return True
        return False
