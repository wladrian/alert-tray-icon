"""Module with configuration class"""

import configparser
import logging

logger = logging.getLogger("air_alert_icon")

DEFAULT_ALERT_API = "ubilling.net.ua"
DEFAULT_API_REQUEST_INTERVAL = 5
DEFAULT_REGION = "м. Київ"
SETTINGS_FILE = "settings.ini"


class Configuration:
    """Configuration object for alert icon application settings"""

    def __init__(self, config_filename: str):
        self.filename = config_filename
        self.api_provider = DEFAULT_ALERT_API
        self.api_polling_interval = DEFAULT_API_REQUEST_INTERVAL
        self.region_to_check_alert = DEFAULT_REGION
        self.enabled_notifications = True

        if not self.load_config():
            logger.info(
                "No config file found. Will create config file with current settings."
            )
            self.save_config()

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
            self.region_to_check_alert = config.get("place", "region")
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
        config["place"]["region"] = self.region_to_check_alert
        config["settings"]["notifications"] = str(self.enabled_notifications)

        with open(self.filename, "w", encoding="UTF-8") as configfile:
            config.write(configfile)
        logger.info("Setting file '%s' written successfully", configfile)
