"""Module with configuration class"""

import configparser
import logging

from alert_tray_icon.providers.models import Location

logger = logging.getLogger("air_alert_icon")

DEFAULT_ALERT_API = "ubilling.net.ua"
DEFAULT_API_REQUEST_INTERVAL = 5
DEFAULT_LOCATION_UID = 31  # Kyiv
SETTINGS_FILE = "settings.ini"


class Configuration:
    """Configuration object for alert icon application settings"""

    def __init__(self, config_filename: str):
        self.filename: str = config_filename
        self.api_provider: str = DEFAULT_ALERT_API
        self.api_polling_interval: int = DEFAULT_API_REQUEST_INTERVAL
        self.location_uid_to_check_alert: int = DEFAULT_LOCATION_UID
        self.enabled_notifications: bool = True
        self.locations: dict[int, Location] = {}

        if not self.load_config():
            logger.info(
                "No config file found. Will create config file with current settings."
            )
            self.save_config()

    @property
    def location_name(self) -> str:
        """Return location name to monitor Alert"""
        location = self.locations.get(int(self.location_uid_to_check_alert))
        if location is None:
            return ""
        return location.name

    def load_config(self) -> bool:
        """Load config from filename

        :returns: True if config is loaded from file, False otherwise
        """
        # Initialize the parser
        config = configparser.ConfigParser()

        # Read the ini file
        files_read_ok = config.read(SETTINGS_FILE, encoding="UTF-8")

        if not files_read_ok:
            return False
        try:
            self.api_provider = config.get("server", "name")
            self.api_polling_interval = config.getint("server", "interval")
            self.location_uid_to_check_alert = int(config.get("place", "location_uid"))
            self.enabled_notifications = config.getboolean("settings", "notifications")
        except (
            configparser.NoSectionError,
            configparser.NoOptionError,
            configparser.InterpolationError,
        ) as exc:
            logger.exception(
                "Exception during getting values from configuration file: %s", exc
            )
            return False
        return True

    def save_config(self) -> None:
        """Save configuration to ini file"""
        config = configparser.ConfigParser()
        config.add_section("server")
        config.add_section("place")
        config.add_section("settings")

        config["server"]["name"] = self.api_provider
        config["server"]["interval"] = str(self.api_polling_interval)
        config["place"]["location_uid"] = str(self.location_uid_to_check_alert)
        config["settings"]["notifications"] = str(self.enabled_notifications)

        with open(self.filename, "w", encoding="UTF-8") as configfile:
            config.write(configfile)
        logger.info("Setting file '%s' written successfully", configfile)
