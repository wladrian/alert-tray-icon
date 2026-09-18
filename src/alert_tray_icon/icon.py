"""Module contains classes related to TrayIcon"""

import logging
import platform
from typing import TYPE_CHECKING
from enum import StrEnum

import pystray
from PIL import Image

if TYPE_CHECKING:
    from PIL.Image import Image as PilImage

logger = logging.getLogger("air_alert_icon")


class IconColor(StrEnum):
    """Enum for Icon colors"""

    RED = "red"
    GREEN = "green"
    BLACK = "black"
    GRAY = "gray"


class TrayIcon:
    """Wrapper class for pystray Icon to encapsulate logic of changing colors and messages"""

    def __init__(
        self,
        title: str,
        color: str,
        menu: pystray.Menu,
        notifications: bool,
        app_name: str = "Air Alert Icon for Ukraine",
    ):
        self.color: str = color
        self.title: str = title
        self.notification_active: bool = notifications
        self.app_name = app_name
        self.icon = pystray.Icon(
            app_name,
            TrayIcon.create_colored_image(self.color),
            self.title,
            menu=menu,
        )
        self.notification_possible: bool = (
            self.icon.HAS_NOTIFICATION and TrayIcon.is_notification_possible()
        )

    @staticmethod
    def is_notification_possible() -> bool:
        """Return True only from Windows"""
        current_os = platform.system()
        return current_os == "Windows"

    def set_color_and_title(self, color: str, title: str) -> None:
        """Set color and title

        :param color: Name of color.  E.g. 'black', 'green'
        :param title: Message on hover icon
        """
        self.set_color(color)
        self.set_title(title)

    def set_color(self, color: str) -> None:
        """Set color of tray icon

        :param color: Name of color. E.g. 'black', 'green'
        """
        if color != self.color:
            self.icon.icon = TrayIcon.create_colored_image(color)
            self.color = color
            logger.info("Changed icon color to '%s'", color)

    def set_title(self, title: str) -> None:
        """Set title displayed on hover of tray icon

        :param title: Text of hover title §of tray icon
        """
        if title != self.title:
            self.icon.title = title
            self.title = title

    def notify(self, message: str) -> None:
        """Create notification baloon in tray. Available only on Windows

        :param message: message text to diplay in notification
        """
        if self.notification_active and self.notification_possible:
            self.icon.notify(message)

    def disable_notifications(self) -> None:
        """Disable displaying notifications under the tray block"""
        self.notification_active = False

    def enable_notifications(self) -> None:
        """Enable displaying notifications under the tray block"""
        self.notification_active = True

    @staticmethod
    def create_colored_image(color: str) -> "PilImage":
        """Helper to generate an image of a specific color.

        :param color: color of image of icon in tray
        :returns: Image of requested color for icon
        """
        image = Image.new("RGB", (64, 64), color)
        return image

    def run(self) -> None:
        """Run blocking call of icon run"""
        self.icon.run()

    def stop(self) -> None:
        """Stop icon run"""
        self.icon.stop()
