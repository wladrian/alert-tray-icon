"""Module of AlertProviders and friends"""

from .base import (
    AlertProvider,
    AlertProviderResult,
    AlertState,
    AirAlertLevel,
    ProviderResponseStatus,
    RegionUID,
    REGION_UID_BY_NAME,
)
from .ubilling import UbillingProvider
from .alerts import AlertsInUaProvider

ALERT_PROVIDERS = {
    "ubilling.net.ua": UbillingProvider,
    "alerts.in.ua": AlertsInUaProvider,
}

alert_providers_keys = {"ubilling.net.ua": "", "alerts.in.ua": ""}
