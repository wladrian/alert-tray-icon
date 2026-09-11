"""
Module starts AlertMonitoringApp
"""

import logging
from logging.handlers import RotatingFileHandler

from config import Configuration, SETTINGS_FILE
from app import AlertMonitoringApp

logger = logging.getLogger("air_alert_icon")


def setup_logger():
    """Setup application logger to log file"""
    logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler(
        "air_alert_icon_app.log", maxBytes=2_000_000, backupCount=1, encoding="utf-8"
    )
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


if __name__ == "__main__":
    setup_logger()
    app_config = Configuration(SETTINGS_FILE)
    app = AlertMonitoringApp(app_config)
    app.run()
