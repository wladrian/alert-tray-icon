import pytest
from pystray import Menu, MenuItem
from alert_tray_icon.icon import TrayIcon


def test_icon_creation():
    def on_exit():
        pass

    test_menu = Menu(
        MenuItem("Exit", on_exit),
    )
    icon = TrayIcon(
        title="Test title",
        color="red",
        menu=test_menu,
        notifications=True,
        app_name="Test app name",
    )

    assert icon.title == "Test title"
    assert icon.color == "red"
