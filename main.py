"""
Module introduce Air Alert Train icon app
"""

import configparser
import datetime as dt
import logging
import time
import threading
import queue

from logging.handlers import RotatingFileHandler
from typing import TYPE_CHECKING

import pystray
import requests

from PIL import Image

from pystray import Icon
from pystray import MenuItem

if TYPE_CHECKING:
    from PIL.Image import Image as PilImage

logger = logging.getLogger("air_alert_icon")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler("air_alert_icon_app.log", maxBytes=20000, backupCount=3, encoding="utf-8")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


DEFAULT_API_ALERT_LINK = "https://ubilling.net.ua/aerialalerts/"
DEFAULT_API_REQUEST_INTERVAL = 5
DEFAULT_REGION = "м. Київ"
SETTINGS_FILE = "settings.ini"


class TrayIcon:
    """Wrapper class for pystray Icon to incapsulate logic of changing colors and messages"""

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
        self.icon = pystray.Icon(
            app_name,
            TrayIcon.create_colored_image(self.color),
            self.title,
            menu=menu,
        )
        self.notification_possible: bool = self.icon.HAS_NOTIFICATION

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
            logger.info(f"Changed icon color to '{color}'")

    def set_title(self, title: str) -> None:
        """Set title displayed on hover of tray icon

        :param title: Text of hover title of tray icon
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


class PollingThread(threading.Thread):
    """Thread to poll API and return result in Queue"""

    def __init__(
        self, url: str, interval: int, results_queue: queue.Queue, timeout: int = 5
    ):
        super().__init__()
        self.url = url
        self.interval = interval
        self.results_queue = results_queue
        self.stop_event = threading.Event()
        self.timeout = timeout
        self.daemon = True  # Thread should not live when app exits

    def run(self) -> None:
        """Polling loop of thread

        Possible event status:
            - success
            - error
            - network_error
        """
        while not self.stop_event.is_set():
            try:
                logger.debug(f"Sending GET request to {self.url}")
                response = requests.get(self.url, timeout=self.timeout)
                logger.debug(response)

                if response.status_code == 200:
                    self.results_queue.put(
                        {"status": "success", "data": response.json()}
                    )
                else:
                    self.results_queue.put(
                        {"status": "error", "code": response.status_code}
                    )

                if response.status_code == 429:
                    time.sleep(
                        self.interval
                    )  # Additional sleep to increase waiting time
            except requests.RequestException as exc:
                logger.exception(exc)
                self.results_queue.put({"status": "network_error"})
            if self.stop_event.wait(timeout=self.interval):
                break

    def stop(self) -> None:
        """Stop polling thread"""
        self.stop_event.set()


class AlertMonitoringApp:
    """Bootstrap TrayIcon and PollingThread"""

    def __init__(self, configuration: "Configuration") -> None:
        self.config = configuration
        self.icon: TrayIcon | None = None
        self.polling_thread: PollingThread | None = None
        self.updates_queue: queue.Queue  = queue.Queue()
        self.alert_status: dict[str, str] = {}

    def start_polling_thread(self) -> None:
        """Create and start polling thread"""
        if self.polling_thread is None or not self.polling_thread.is_alive():
            logger.info("Polling thread started!")
            self.polling_thread = PollingThread(
                url=self.config.api_url,
                interval=self.config.api_polling_interval,
                results_queue=self.updates_queue,
            )
            self.polling_thread.start()
            threading.Thread(target=self.poll_queue_listener, daemon=True).start()

    def set_alert_status(self, data: dict) -> None:
        """Set status of alert for TrayIcon based on data dictionary received in JSON payload
        
        :param data: Dictionary with json payload
        """
        if self.icon is None:
            logger.warning("Tray Icon object is not created")
            return
        if not data:
            logger.warning(f"Data for parsing result is empty {data}")
            return
        state_changed = False
        try:
            logger.info(f"Response json: {data}")
            status = data["states"][self.config.region_to_check_alert]
            if self.alert_status != status:
                logger.info(
                    f"There is change in alert status for {self.config.region_to_check_alert}"
                )
                state_changed = True

            active_alert = status["alertnow"]
            state_since = status["changed"]
        except KeyError as ex:
            logger.info(f"Error while parsing response from server: {ex}")
            self.icon.set_color_and_title(
                "gray", "Помилка під час опрацювання даних від API тривог"
            )
        if active_alert:
            logger.info("As Alert active, change color to RED")
            self.icon.set_color_and_title(
                "red", f"Тривога в {self.config.region_to_check_alert} з {state_since}"
            )
            if state_changed:
                self.icon.notify("Оголошено тривогу!")
        else:
            logger.info("As Alert not active, change color to GREEN")
            self.icon.set_color_and_title("green", f"Немає тривоги з {state_since}")
            if state_changed and self.alert_status:
                self.icon.notify("Відбій тривоги")
        self.alert_status = status

    def handle_worker_update(self, msg: dict) -> None:
        """Handle update from polling thread and update tray icon state

        :param msg: message to handling from PolllingThread
        """

        status = msg.get("status")

        if self.icon is None:
            logger.warning("Tray Icon object is not created")
            return

        match status:
            case "success":
                data = msg.get("data", {})
                self.set_alert_status(data)
            case "error":
                self.icon.set_color_and_title(
                    "gray", f"Error {msg.get('code')} during API call"
                )
            case "network_error":
                self.icon.set_color_and_title("black", "Network problem")

    def poll_queue_listener(self) -> None:
        """Listen for data from PollingThread"""

        while self.polling_thread and self.polling_thread.is_alive():
            try:
                logger.info("Listening for message from polling thread...")
                message = self.updates_queue.get(timeout=1)
                self.handle_worker_update(message)
            except queue.Empty:
                continue

    def on_exit(self, icon: "Icon", item: MenuItem) -> None:
        """Stop running polling thread and icon app

        :param icon: pystray Icon object
        :param item: pystay MenuItem object
        """
        logger.debug(f"Toggle menu item {item}")
        if self.polling_thread:
            self.polling_thread.stop()
            self.polling_thread.join()
        icon.stop()

    def is_notifications_enabled(self, item: MenuItem) -> bool:
        """Returns True is notifications in tray are enabled

        :param item: pystay Menu Item object
        :returns: True, if notifications enabled, False otherwise
        """
        logger.debug(f"Toggle menu item {item}")
        return self.config.enabled_notifications

    def is_notifications_disabled(self, item: MenuItem) -> bool:
        """Returns True is notifications in tray are disabled

        :param item: pystay Menu Item object
        :returns: True, if notifications enabled, False otherwise
        """
        logger.debug(f"Toggle menu item {item}")
        return not self.config.enabled_notifications

    def notify_off(self, icon: "Icon", item: MenuItem) -> None:
        """Disable icon notifications

        :param icon: pystray Icon object
        :param item: pystay Menu Item object
        """
        self.config.enabled_notifications = False
        icon.disable_notifications()
        logger.debug(f"Toggle menu item {item}")

    def notify_on(self, icon: "Icon", item: MenuItem) -> None:
        """Enable icon notifications

        :param icon: pystray Icon object
        :param item: pystay Menu Item object
        """
        self.config.enabled_notifications = True
        icon.enable_notifications()
        logger.debug(f"Toggle menu item {item}")

    def run(self) -> None:
        """Bootstrap icon, polling thread and start them"""
        # Setup menu
        icon_menu = pystray.Menu(
            MenuItem(
                "Turn Off Notifications",
                self.notify_off,
                visible=self.is_notifications_enabled,
            ),
            MenuItem(
                "Turn On Notifications",
                self.notify_on,
                visible=self.is_notifications_disabled,
            ),
            MenuItem("Exit", self.on_exit),
        )
        # Setup the tray icon with dynamic options
        self.icon = TrayIcon(
            title="Дані відсутні",
            color="white",
            menu=icon_menu,
            notifications=self.config.enabled_notifications,
        )

        self.start_polling_thread()
        logger.info(
            f"Connecting to '{self.config.api_url}' \
            'with interval {self.config.api_polling_interval}' \
            'for region {self.config.region_to_check_alert}"
        )
        logger.info(f"Tray notifications enabled: {self.config.enabled_notifications}")

        self.icon.run()


class Configuration:
    """Configuration object for alert icon application settings"""

    def __init__(self, config_filename: str):
        self.filename = config_filename
        self.api_url = DEFAULT_API_ALERT_LINK
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
            self.api_url = config.get("server", "url")
            self.api_polling_interval = config.getint("server", "interval")
            self.region_to_check_alert = config.get("place", "region")
            self.enabled_notifications = config.getboolean("settings", "notifications")
        except (
            configparser.NoSectionError,
            configparser.NoOptionError,
            configparser.InterpolationError,
        ) as exc:
            logger.exception(
                f"Exception during getting values from configuration file: {exc}"
            )
            return False
        return True

    def save_config(self) -> None:
        """Save configuration to ini file"""
        config = configparser.ConfigParser()
        config.add_section("server")
        config.add_section("place")
        config.add_section("settings")

        config["server"]["url"] = self.api_url
        config["server"]["interval"] = str(self.api_polling_interval)
        config["place"]["region"] = self.region_to_check_alert
        config["settings"]["notifications"] = str(self.enabled_notifications)

        with open(self.filename, "w", encoding="UTF-8") as configfile:
            config.write(configfile)
        logger.info(f"Setting file '{configfile}' written successfuly")


if __name__ == "__main__":
    app_config = Configuration(SETTINGS_FILE)
    app = AlertMonitoringApp(app_config)
    app.run()
