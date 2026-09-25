"""JSON and other structures related to Alert API providers"""

from enum import StrEnum
from pydantic import BaseModel


class LocationType(StrEnum):
    """Location type Enum"""

    OBLAST = "oblast"
    RAION = "raion"
    CITY = "city"
    HROMADA = "hromada"
    UNKNOWN = "unknown"


class AlertType(StrEnum):
    """Alert type Enum"""

    AIR_RAID = "air_raid"
    ARTILLERY_SHELLING = "artillery_shelling"
    URBAN_FIGHTS = "urban_fights"
    CHEMICAL = "chemical"
    NUCLEAR = "nuclear"


class AlertLevel(StrEnum):
    """Alert level enum"""

    YELLOW = "yellow"
    RED = "red"
    UNKNOWN = "unknown"


class ThreatType(StrEnum):
    """Threat type enum"""

    TACTIC_AIRCRAFT_ACTIVITY = "tactic_aircraft_activity"
    STRATEGIC_AIRCRAFT_ACTIVITY = "strategic_aircraft_activity"
    MIG31K_DEPARTURE = "mig31k_departure"
    BALLISTIC_MISSILES = "ballistic_missiles"
    CRUISE_MISSILES = "cruise_missiles"
    UNSPECIFIED_MISSILES = "unspecified_missiles"
    DRONES = "drones"
    GUIDED_AERIAL_BOMBS = "guided_aerial_bombs"
    AIR_DEFENSE = "air_defense"
    UNKNOWN = "unknown"


class ActiveThreat(BaseModel):
    """Active threat entity from API alerts.in.ua"""

    threat_type: ThreatType
    level: str
    started_at: str
    source_message: str = ""


class ActiveAlert(BaseModel):
    """Active alert entity from API alerts.in.ua"""

    id: int
    location_title: str
    location_title_en: str
    location_type: LocationType
    started_at: str
    finished_at: str | None
    updated_at: str
    alert_type: AlertType
    location_uid: str
    location_oblast: str
    location_raion: str | None = None
    notes: str | None = None
    alert_level: AlertLevel
    threats: list[ActiveThreat] = []


class ActiveAlertsResponse(BaseModel):
    """Active alerts entity from API alerts.in.ua"""

    alerts: list[ActiveAlert]
