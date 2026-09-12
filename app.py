"""AlertMonitoringApp class"""
import logging
import threading
import queue

import pystray

from pystray import Icon
from pystray import MenuItem

from config import Configuration
from icon import TrayIcon
from worker import PollingThread
from providers import (
    AlertProviderResult,
    AirAlertLevel,
    AlertState,
    UbillingProvider,
    REGION_UID_BY_NAME,
    ProviderResponseStatus,
    ALERT_PROVIDERS,
)

logger = logging.getLogger("air_alert_icon")


class AlertMonitoringApp:
    """Bootstrap TrayIcon and PollingThread"""

    def __init__(self, configuration: "Configuration") -> None:
        self.config = configuration
        self.icon: TrayIcon | None = None
        self.polling_thread: PollingThread | None = None
        self.updates_queue: queue.Queue = queue.Queue()
        self.alert_status: AlertState | None = None

    def start_polling_thread(self) -> None:
        """Create and start polling thread"""
        if self.polling_thread is None or not self.polling_thread.is_alive():
            logger.info("Polling thread started!")
            provider = ALERT_PROVIDERS.get(self.config.api_provider, UbillingProvider)
            self.polling_thread = PollingThread(
                alert_provider=provider(""),
                interval=self.config.api_polling_interval,
                results_queue=self.updates_queue,
            )
            self.polling_thread.start()
            threading.Thread(target=self.poll_queue_listener, daemon=True).start()

    def set_alert_status(self, data: AlertProviderResult) -> None:
        """Set status of alert for TrayIcon based on data received from AlertProvider

        :param data: AlertState object
        """
        state_changed = False
        if self.icon is None:
            logger.warning("Tray Icon object is not created")
            return

        if data.states is None:
            logger.warning("Empty alert data from provider")
            return

        try:
            region_uid = REGION_UID_BY_NAME[self.config.region_to_check_alert]
        except KeyError as exc:
            logger.exception(exc)
            self.icon.set_color_and_title(
                "black", f"Регіон {self.config.region_to_check_alert} не знайдено"
            )
            return
        alert_data = data.states[region_uid]
        if alert_data is None:
            self.icon.set_color_and_title(
                "green", f"Немає тривоги в {self.config.region_to_check_alert} [{data.source}]"
            )
            return
        if self.alert_status != alert_data:
            logger.debug(
                f"There is change in alert status for {self.config.region_to_check_alert}"
            )
            state_changed = True

        state_since = f" з {alert_data.since}" if alert_data.since else ""

        if alert_data.alert:
            logger.debug("As Alert active, change color...")
            match alert_data.level:
                case AirAlertLevel.RED:
                    color = "red"
                    level_message = "червоний"
                case AirAlertLevel.YELLOW:
                    color = "yellow"
                    level_message = "жовтий"
                case _:
                    color = "crimson"
                    level_message = "не визначено"
            self.icon.set_color_and_title(
                color,
                f"Тривога в {self.config.region_to_check_alert} {state_since}  ([{data.source}])",
            )
            if state_changed:
                self.icon.notify(
                    f"Оголошено тривогу ({level_message} рівень)!  [{data.source}]"
                )
        else:
            logger.debug("As Alert not active, change color to GREEN")
            self.icon.set_color_and_title(
                "green",
                f"Немає тривоги в "
                f"{self.config.region_to_check_alert}{state_since} [{data.source}]",
            )
            if state_changed and self.alert_status:
                self.icon.notify(f"Відбій тривоги  [{data.source}]")
        self.alert_status = alert_data

    def handle_worker_update(self, response: AlertProviderResult) -> None:
        """Handle update from polling thread and update tray icon state

        :param response: AlertProviderResult object received from AlertProvider
        """

        if self.icon is None:
            logger.warning("Tray Icon object is not created")
            return

        match response.status:
            case ProviderResponseStatus.SUCCESS:
                self.set_alert_status(response)
            case ProviderResponseStatus.API_ERROR:
                self.icon.set_color_and_title(
                    "gray", f"Error {response.error_code} during API call"
                )
            case ProviderResponseStatus.NETWORK_ERROR:
                self.icon.set_color_and_title("black", "Network problem")
            case ProviderResponseStatus.UNKNOWN_PROVIDER_ERROR:
                self.icon.set_color_and_title("black", "Unknown alert provider error")
            case ProviderResponseStatus.RESPONSE_PARSE_ERROR:
                self.icon.set_color_and_title(
                    "black", "Error during parsing API response"
                )

    def poll_queue_listener(self) -> None:
        """Listen for data from PollingThread"""

        while self.polling_thread and self.polling_thread.is_alive():
            try:
                logger.debug("Listening for message from polling thread...")
                message = self.updates_queue.get(timeout=2)
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
        if self.icon and self.icon.is_notification_possible():
            return self.config.enabled_notifications
        return False

    def is_notifications_disabled(self, item: MenuItem) -> bool:
        """Returns True is notifications in tray are disabled

        :param item: pystay Menu Item object
        :returns: True, if notifications enabled, False otherwise
        """
        logger.debug(f"Toggle menu item {item}")
        if self.icon and self.icon.is_notification_possible():
            return not self.config.enabled_notifications
        return False

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
        logger.info(f"Connecting to '{self.config.api_provider}' \
            'with interval {self.config.api_polling_interval}' \
            'for region {self.config.region_to_check_alert}")
        logger.info(f"Tray notifications enabled: {self.config.enabled_notifications}")

        self.icon.run()
