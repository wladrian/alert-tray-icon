"""AlertMonitoringApp class"""

import logging
import threading
import queue
from copy import deepcopy

import pystray
from pystray import Icon
from pystray import MenuItem

from alert_tray_icon.config import Configuration
from alert_tray_icon.icon import TrayIcon
from alert_tray_icon.worker import PollingThread
from alert_tray_icon.providers import (
    AlertProviderResult,
    AirAlertLevel,
    AlertState,
    UbillingProvider,
    ProviderResponseStatus,
    ALERT_PROVIDERS,
    ProxyAlertsInUaProvider,
)
from alert_tray_icon.providers.models import Location, DescriptionLocationType
from alert_tray_icon.providers.base import UID_TO_REGION
from alert_tray_icon.window import SettingsWindow

logger = logging.getLogger("air_alert_icon")


class AlertMonitoringApp:
    """Bootstrap TrayIcon and PollingThread"""

    def __init__(
        self, configuration: "Configuration", api_keys: dict[str, str]
    ) -> None:
        # Config
        self.config = configuration
        self.config_backup = deepcopy(configuration)
        self.api_keys = api_keys
        self.config.locations = self.get_locations()

        # GUI
        self.settings_window = SettingsWindow(configuration, self.withdraw_window)
        self.icon: TrayIcon = self.create_icon()

        # Model
        self.polling_thread: PollingThread | None = None
        self.updates_queue: queue.Queue = queue.Queue()
        self.result_listener: threading.Thread | None = None
        self.alert_status: AlertState | None = None

        # Polling alerts
        self.start_polling_thread()
        logger.info(
            "Connecting to '%s' with interval %s for location UID %s",
            self.config.api_provider,
            self.config.api_polling_interval,
            self.config.location_uid_to_check_alert,
        )
        logger.info("Tray notifications enabled: %s", self.config.enabled_notifications)

        # GUI take control of main loop
        self.settings_window.set_hide_mode_on_close()
        self.withdraw_window()
        self.settings_window.run()

    def start_polling_thread(self) -> None:
        """Create and start polling thread"""
        if self.polling_thread is None or not self.polling_thread.is_alive():
            logger.info("Polling thread started for %s", self.config.api_provider)
            provider = ALERT_PROVIDERS.get(self.config.api_provider, UbillingProvider)
            api_key: str = self.api_keys.get(self.config.api_provider, "")
            self.polling_thread = PollingThread(
                alert_provider=provider(api_key),
                interval=self.config.api_polling_interval,
                results_queue=self.updates_queue,
            )
            self.polling_thread.start()
            self.result_listener = threading.Thread(
                target=self.poll_queue_listener, daemon=True
            )
            self.result_listener.start()

    def set_alert_status(self, data: AlertProviderResult) -> None:
        """Set status of alert for TrayIcon based on data received from AlertProvider

        :param data: AlertState object
        """
        if self.icon is None:
            logger.warning("Tray Icon object is not created")
            return

        if data.alerts_by_location is None:
            logger.warning("Empty alert data from provider")
            return

        location_uid = int(self.config.location_uid_to_check_alert)
        if location_uid not in self.config.locations:
            self.icon.set_color_and_title(
                "blue",
                "Регіон моніторингу помилковий або не встановлений",
            )
            return
        location_name = self.config.locations[location_uid].name

        locations_to_check = [location_uid]
        if not self.config.locations[location_uid].separate_alarm:
            limit = 3
            location = self.config.locations[location_uid]
            while location.parent_uid is not None and limit > 0:
                locations_to_check.append(location.parent_uid)
                location = self.config.locations[location.parent_uid]
                limit -= 1

        alert_data = None
        alert_data_list = [
            data.alerts_by_location.get(uid) for uid in locations_to_check
        ]
        for alert_data_elem in alert_data_list:
            if alert_data_elem is not None:
                alert_data = alert_data_elem
                break
        color, title, state_changed = self._determine_color_and_title_by_alert(
            location_name, alert_data, data.source
        )
        self.icon.set_color_and_title(color, title)

        if state_changed:
            msg = (
                f"Оголошено тривогу в {location_name}! [{data.source}]"
                if color in ["red", "yellow"]
                else ""
            )
            msg = f"Відбій тривоги  [{data.source}]" if color == "green" else msg
            self.icon.notify(msg)

        self.alert_status = alert_data

    def _determine_color_and_title_by_alert(
        self, location_name: str, alert_data: AlertState | None, source: str | None
    ) -> tuple[str, str, bool]:
        """Determine color by alert data

        :param location_name: Location name
        :param alert_data: Alert data from provider
        :param source: Source of alert data
        :returns: (color, title, state_changed)
        """
        state_changed: bool = self.alert_status != alert_data
        source = "" if source is None else source

        if alert_data is None:
            return (
                "green",
                f"Немає тривоги в " f"{location_name} [{source}]",
                state_changed,
            )

        state_since = f" з {alert_data.since}" if alert_data.since else ""
        logger.debug(
            "There is%s change in alert status for %s",
            "" if state_changed else " no",
            location_name,
        )

        if not alert_data.alert:
            return (
                "green",
                f"Немає тривоги в " f"{location_name}{state_since} [{source}]",
                state_changed,
            )

        match alert_data.level:
            case AirAlertLevel.RED:
                color = "red"
            case AirAlertLevel.YELLOW:
                color = "yellow"
            case _:
                color = "crimson"

        title = f"Тривога в {location_name} {state_since} [{source}]"
        return color, title, state_changed

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
        logger.debug("Toggle menu item %s", item)
        """
        logger.debug("Toggle menu item %s", item)
        if self.polling_thread:
            self.polling_thread.stop()
            self.polling_thread.join()
        icon.stop()
        self.settings_window.destroy()

    def is_notifications_enabled(self, item: MenuItem) -> bool:
        """Returns True is notifications in tray are enabled

            :param item: pystay Menu Item object
        logger.debug("Toggle menu item %s", item)
            :returns: True, if notifications enabled, False otherwise
        """
        logger.debug("Toggle menu item %s", item)
        if self.icon and self.icon.is_notification_possible():
            return self.config.enabled_notifications
        return False

    def is_notifications_disabled(self, item: MenuItem) -> bool:
        """Returns True is notifications in tray are disabled

        logger.debug("Toggle menu item %s", item)
            :param item: pystay Menu Item object
            :returns: True, if notifications enabled, False otherwise
        """
        logger.debug("Toggle menu item %s", item)
        if self.icon and self.icon.is_notification_possible():
            return not self.config.enabled_notifications
        return False

    def notify_off(self, icon: "Icon", item: MenuItem) -> None:
        """Disable icon notifications

            :param icon: pystray Icon object
        logger.debug("Toggle menu item %s", item)
            :param item: pystay Menu Item object
        """
        self.config.enabled_notifications = False
        icon.disable_notifications()
        logger.debug("Toggle menu item %s", item)

    def notify_on(self, icon: "Icon", item: MenuItem) -> None:
        """Enable icon notifications

        logger.debug("Toggle menu item %s", item)
            :param icon: pystray Icon object
            :param item: pystay Menu Item object
        """
        self.config.enabled_notifications = True
        icon.enable_notifications()
        logger.debug("Toggle menu item %s", item)

    def create_icon(self) -> TrayIcon:
        """Create TrayIcon"""
        # Setup menu
        icon_menu = pystray.Menu(
            MenuItem("Налаштування", self.show_window),
            MenuItem("Вихід", self.on_exit),
        )

        default_title = f"Стан тривоги в {self.config.location_name} [{self.config.api_provider.strip('proxy.')}]"

        # Setup the tray icon with dynamic options
        return TrayIcon(
            title=default_title,
            color="white",
            menu=icon_menu,
            notifications=self.config.enabled_notifications,
        )

    def run(self) -> None:
        """Bootstrap icon, polling thread and start them"""
        self.icon.run()

    def show_window(self) -> None:
        """Hide icon and show settings window"""
        self.icon.stop()
        self.settings_window.show_window()

    def withdraw_window(self) -> None:
        """Hide settings window and show icon"""
        self.settings_window.withdraw()
        self.check_provider_change()
        self.icon = self.create_icon()
        self.icon.run()

    def check_provider_change(self) -> None:
        """Check change of API provider and restart polling"""
        if self.config_backup.api_provider != self.config.api_provider:
            logger.info("Changed API provider to %s", self.config.api_provider)
            # Stop current API polling
            if self.polling_thread is not None:
                self.polling_thread.stop()
                self.polling_thread.join()
            if self.result_listener is not None:
                self.result_listener.join()
            # Start new API polling
            self.start_polling_thread()
            # Update backup
            self.config_backup = deepcopy(self.config)

    @staticmethod
    def get_locations() -> dict[int, Location]:
        """Request locations dictionary from API of proxy server"""
        provider = ProxyAlertsInUaProvider("")
        locations = {}
        try:
            data = provider.request_locations()
        except RuntimeError as exc:
            logger.exception(exc)
            # Return common locations
            for uid, name in UID_TO_REGION.items():
                if uid == 31:
                    locations[uid] = Location(
                        uid=uid,
                        name=name,
                        location_type=DescriptionLocationType.CITY_SPECIAL,
                        separate_alarm=False,
                        parent_uid=None,
                    )
                locations[uid] = Location(
                    uid=uid,
                    name=name,
                    location_type=DescriptionLocationType.OBLAST,
                    separate_alarm=False,
                    parent_uid=None,
                )

            return locations

        for location in data.locations:
            locations[int(location.uid)] = location
        return locations
