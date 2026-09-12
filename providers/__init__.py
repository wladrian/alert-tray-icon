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

ALERT_PROVIDERS = {
    "ubilling.net.ua": UbillingProvider,
}
