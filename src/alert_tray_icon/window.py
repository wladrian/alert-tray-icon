"""Module of Settings window"""

import tkinter as tk
from tkinter import ttk
from typing import Callable

from alert_tray_icon.config import Configuration
from alert_tray_icon.providers import REGION_UID_BY_NAME


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

        self.group_box = ttk.LabelFrame(
            self.root, text="Регіон моніторингу", padding=10
        )
        regions = list(REGION_UID_BY_NAME.keys())
        self.cb_region_selection = ttk.Combobox(self.group_box, values=regions)
        if self.config.region_to_check_alert in regions:
            self.cb_region_selection.set(self.config.region_to_check_alert)
        self.btn_save = ttk.Button(
            self.root, text="Зберегти", command=self.save_settings
        )
        self.pack_widgets()

    def pack_widgets(self) -> None:
        """Add widgets to window and configure"""
        self.root.title("Налаштування")
        self.group_box.pack(padx=20, pady=20, fill="both", expand=True)
        self.cb_region_selection.pack()
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
        self.config.save_config()
        self.callback()
