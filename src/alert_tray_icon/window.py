"""Module of Settings window"""

import tkinter as tk
from tkinter import ttk
from typing import Callable
import platform
import ctypes
from ctypes import wintypes


from alert_tray_icon.config import Configuration
from alert_tray_icon.providers import REGION_UID_BY_NAME, ALERT_PROVIDERS
from alert_tray_icon._version import __version__

SPI_GETWORKAREA = 0x0030


class SettingsWindow:
    """Window to allow change app settings"""

    def __init__(self, configuration: "Configuration", callback: Callable):
        """Init Settings window

        :param configuration: Configuration object
        :param callback: Callable to call when hide window
        """
        self.config = configuration
        self.callback = callback
        self.root = tk.Tk()

        self.group_box_provider = ttk.LabelFrame(self.root, text="Сервер тривог")
        api_providers = list(ALERT_PROVIDERS.keys())
        self.cb_provider_selection = ttk.Combobox(
            self.group_box_provider, values=api_providers, state="readonly"
        )
        self.group_box = ttk.LabelFrame(
            self.root, text="Регіон моніторингу", padding=10
        )
        regions = list(REGION_UID_BY_NAME.keys())
        self.cb_region_selection = ttk.Combobox(
            self.group_box, values=regions, state="readonly"
        )
        if self.config.region_to_check_alert in regions:
            self.cb_region_selection.set(self.config.region_to_check_alert)
        if self.config.api_provider in api_providers:
            self.cb_provider_selection.set(self.config.api_provider)
        self.notif_var = tk.BooleanVar()
        self.checkbox_notifications = ttk.Checkbutton(
            self.root,
            text="Нотифікації",
            padding=20,
            variable=self.notif_var,
            onvalue=True,
            offvalue=False,
        )
        self.notif_var.set(self.config.enabled_notifications)
        self.lbl_version = ttk.Label(
            self.root, text=f"Alert Tray Icon v.{__version__}", font=("Courier", 10)
        )
        self.btn_save = ttk.Button(
            self.root, text="Зберегти", command=self.save_settings
        )
        self.pack_widgets()

        width, height = 250, 330
        x, y = 0, 0
        current_os = platform.system()
        if current_os == "Windows":
            margin_x = 10
            margin_y = 35

            # Get Windows work area (screen area excluding the taskbar)
            work_area = wintypes.RECT()
            ctypes.windll.user32.SystemParametersInfoW(  # type: ignore[attr-defined]
                SPI_GETWORKAREA, 0, ctypes.byref(work_area), 0
            )

            x = work_area.right - width - margin_x
            y = work_area.bottom - height - margin_y

        if current_os == "Darwin":
            x = self.root.winfo_screenwidth()
            self.checkbox_notifications.state(["disabled"])

        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def pack_widgets(self) -> None:
        """Add widgets to window and configure"""
        self.root.title("Налаштування")
        self.group_box_provider.pack(padx=20, pady=20, fill="both", expand=True)
        self.group_box.pack(padx=20, pady=20, fill="both", expand=True)
        self.cb_provider_selection.pack()
        self.cb_region_selection.pack()
        self.checkbox_notifications.pack()
        self.lbl_version.pack()

        self.btn_save.pack()

    def withdraw(self) -> None:
        """Hide window"""
        self.root.withdraw()

    def set_hide_mode_on_close(self) -> None:
        """Change window behavior"""
        self.root.protocol("WM_DELETE_WINDOW", self.callback)

    def show_window(self) -> None:
        """Show window"""
        self.set_hide_mode_on_close()
        self.root.after(0, self.root.deiconify)

    def destroy(self) -> None:
        """Destroy window on app exit"""
        self.root.destroy()

    def run(self) -> None:
        """Run main loop (blocking)"""
        self.root.mainloop()

    def save_settings(self) -> None:
        """Save app settings selected in window"""
        self.config.region_to_check_alert = self.cb_region_selection.get()
        self.config.api_provider = self.cb_provider_selection.get()
        self.config.enabled_notifications = self.notif_var.get()
        self.config.save_config()
        self.callback()
