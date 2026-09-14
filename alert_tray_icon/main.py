"""
Module starts AlertMonitoringApp
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

from config import Configuration, SETTINGS_FILE
from app import AlertMonitoringApp
from providers import alert_providers_keys

logger = logging.getLogger("air_alert_icon")


def setup_logger() -> None:
    """Setup application logger to log file"""
    logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler(
        "air_alert_icon_app.log", maxBytes=10_000_000, backupCount=1, encoding="utf-8"
    )
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


if __name__ == "__main__":
    setup_logger()
    load_dotenv()
    alerts_api_key = os.getenv("ALERTS_API_KEY", "")
    alert_providers_keys["alerts.in.ua"] = alerts_api_key
    app_config = Configuration(SETTINGS_FILE)
    app = AlertMonitoringApp(app_config, alert_providers_keys)
    app.run()
