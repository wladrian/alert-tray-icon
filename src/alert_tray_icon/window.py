"""Module of Settings window"""

import tkinter as tk
from tkinter import ttk
from typing import Callable
import platform
import ctypes
from ctypes import wintypes


from alert_tray_icon.config import Configuration
from alert_tray_icon.providers import ALERT_PROVIDERS
from alert_tray_icon.providers.models import DescriptionLocationType
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
        self.location_items_oblast: list[tuple[int, str]] = [
            (t.uid, t.name)
            for t in self.config.locations.values()
            if t.location_type
            in [DescriptionLocationType.OBLAST, DescriptionLocationType.CITY_SPECIAL]
        ]
        self.location_items_raion: list[tuple[int, str]] = []
        self.location_items_hromada: list[tuple[int, str]] = []

        self.cb_oblast_selection = ttk.Combobox(
            self.group_box,
            values=[name for uid, name in self.location_items_oblast],
            state="readonly",
        )
        self.cb_oblast_selection.bind("<<ComboboxSelected>>", self.on_oblast_selection)
        self.cb_raion_selection = ttk.Combobox(
            self.group_box, values=[], state="disabled"
        )
        self.cb_raion_selection.bind("<<ComboboxSelected>>", self.on_raion_selection)
        self.cb_hromada_selection = ttk.Combobox(
            self.group_box, values=[], state="disabled"
        )

        self.set_init_combobox_locations()

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

        width, height = 250, 350
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

    def get_selected_location_uid(self) -> int:
        """Get selected location UID. Inner of selected sub locations.

        :return: UID of selected inner location
        """
        index_oblast = self.cb_oblast_selection.current()
        index_raion = self.cb_raion_selection.current()
        index_hromada = self.cb_hromada_selection.current()
        if index_hromada >= 0:
            return self.location_items_hromada[index_hromada][0]
        if index_raion >= 0:
            return self.location_items_raion[index_raion][0]
        if index_oblast >= 0:
            return self.location_items_oblast[index_oblast][0]
        return -1

    def pack_widgets(self) -> None:
        """Add widgets to window and configure"""
        self.root.title("Налаштування")
        self.group_box_provider.pack(padx=20, pady=20, fill="both", expand=True)
        self.group_box.pack(padx=20, pady=20, fill="both", expand=True)
        self.cb_provider_selection.pack()
        self.cb_oblast_selection.pack()
        self.cb_raion_selection.pack()
        self.cb_hromada_selection.pack()
        self.checkbox_notifications.pack()
        self.lbl_version.pack()

        self.btn_save.pack()

    def withdraw(self) -> None:
        """Hide window"""
        self.root.grab_release()
        self.root.withdraw()

    def set_hide_mode_on_close(self) -> None:
        """Change window behavior"""
        self.root.protocol("WM_DELETE_WINDOW", self.callback)

    def show_window(self) -> None:
        """Show window"""
        self.set_hide_mode_on_close()
        self.root.lift()
        self.root.focus_force()
        self.root.grab_set()
        self.root.after(0, self.root.deiconify)

    def destroy(self) -> None:
        """Destroy window on app exit"""
        self.root.destroy()

    def run(self) -> None:
        """Run main loop (blocking)"""
        self.root.mainloop()

    def save_settings(self) -> None:
        """Save app settings selected in window"""
        self.config.location_uid_to_check_alert = self.get_selected_location_uid()
        self.config.api_provider = self.cb_provider_selection.get()
        self.config.enabled_notifications = self.notif_var.get()
        self.config.save_config()
        self.callback()

    def on_oblast_selection(self, _: tk.Event | None) -> None:
        """On selection of oblast combobox

        :param _: tk.Event object
        """
        self.cb_raion_selection.set("")
        self.cb_hromada_selection.set("")
        index = self.cb_oblast_selection.current()
        uid = self.location_items_oblast[index][0]
        raions = [
            item for item in self.config.locations.values() if item.parent_uid == uid
        ]
        if raions:
            self.location_items_raion = [(t.uid, t.name) for t in raions]
            values = [item[1] for item in self.location_items_raion]
            self.cb_raion_selection["values"] = values
            self.cb_raion_selection["state"] = "readonly"
            return
        self.cb_raion_selection["state"] = "disabled"
        self.cb_raion_selection["values"] = []
        self.cb_hromada_selection["state"] = "disabled"
        self.cb_hromada_selection["values"] = []

    def on_raion_selection(self, _: tk.Event | None) -> None:
        """On selection of raion combobox

        :param _: tk.Event object
        """
        self.cb_hromada_selection.set("")
        index = self.cb_raion_selection.current()
        uid = self.location_items_raion[index][0]
        hromadas = [
            item for item in self.config.locations.values() if item.parent_uid == uid
        ]
        if hromadas:
            self.location_items_hromada = [(t.uid, t.name) for t in hromadas]
            values = [item[1] for item in self.location_items_hromada]
            self.cb_hromada_selection["values"] = values
            self.cb_hromada_selection["state"] = "readonly"
            return
        self.cb_hromada_selection["state"] = "disabled"
        self.cb_hromada_selection["values"] = []

    def set_init_combobox_locations(self) -> None:
        """Set Init value on location combo boxes"""
        uid = int(self.config.location_uid_to_check_alert)
        locations_to_check = [self.config.location_uid_to_check_alert]
        location = self.config.locations[uid]
        limit = 3
        while location.parent_uid is not None and limit > 0:
            locations_to_check.append(location.parent_uid)
            location = self.config.locations[location.parent_uid]
            limit -= 1
        locations = [self.config.locations[int(uid)] for uid in locations_to_check]

        for location in locations[::-1]:
            if location.location_type in [
                DescriptionLocationType.OBLAST,
                DescriptionLocationType.CITY_SPECIAL,
            ]:
                self.cb_oblast_selection.set(location.name)
                self.on_oblast_selection(None)
            if location.location_type == DescriptionLocationType.RAION:
                self.cb_raion_selection.set(location.name)
                self.cb_raion_selection["state"] = "readonly"
                self.on_raion_selection(None)
            if location.location_type == DescriptionLocationType.HROMADA:
                self.cb_hromada_selection.set(location.name)
                self.cb_hromada_selection["state"] = "readonly"
