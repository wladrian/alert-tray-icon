"""Module contains PollingThread for polling alert results from AlertProviders via API"""

import logging
import time
import threading
import queue

from alert_tray_icon.providers import (
    AlertProvider,
    ProviderResponseStatus,
    AlertProviderResult,
)

logger = logging.getLogger("air_alert_icon")


class PollingThread(threading.Thread):
    """Thread to poll API and return result in Queue"""

    def __init__(
        self, alert_provider: AlertProvider, interval: int, results_queue: queue.Queue
    ):
        super().__init__()
        self.alert_provider = alert_provider
        self.interval = max(self.alert_provider.REQUEST_LIMIT, interval)
        self.results_queue = results_queue
        self.stop_event = threading.Event()
        self.daemon = True  # Thread should not live when app exits

    def run(self) -> None:
        """Polling loop of thread"""
        logger.debug("Start of polling thread run")
        while not self.stop_event.is_set():
            logger.debug("Cycle of polling thread run")
            try:
                alert_result: AlertProviderResult = self.alert_provider.get_data()
                logger.debug(alert_result)
                if alert_result.status == ProviderResponseStatus.SUCCESS:
                    self.results_queue.put(alert_result)
                else:
                    if (
                        alert_result.status == ProviderResponseStatus.API_ERROR
                        and alert_result.error_code == 429
                    ):
                        logger.warning(
                            "Error 429 - Too many requests. "
                            "Increase polling interval once to twice size."
                        )
                        time.sleep(self.interval * 2)
                        self.interval += 1

            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.exception(exc)
                self.results_queue.put(
                    AlertProviderResult(
                        status=ProviderResponseStatus.UNKNOWN_PROVIDER_ERROR
                    )
                )
            if self.stop_event.wait(timeout=self.interval):
                break

    def stop(self) -> None:
        """Stop polling thread"""
        self.stop_event.set()
