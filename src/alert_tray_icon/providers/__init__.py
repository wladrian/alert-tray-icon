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
from .ubilling import UbillingProvider, ProxyUbillingProvider
from .alerts import AlertsInUaProvider, ProxyAlertsInUaProvider


ALERT_PROVIDERS: dict[str, type[AlertProvider]] = {
    "ubilling.net.ua": UbillingProvider,
    "alerts.in.ua": AlertsInUaProvider,
    "proxy.ubilling.net.ua": ProxyUbillingProvider,
    "proxy.alerts.in.ua": ProxyAlertsInUaProvider,
}

alert_providers_keys = {"ubilling.net.ua": "", "alerts.in.ua": "", "proxy.ubilling.net.ua": "", "proxy.alerts.in.ua": ""}
