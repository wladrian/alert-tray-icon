import pytest
from unittest.mock import MagicMock, patch
from pystray import Menu, MenuItem
from alert_tray_icon.icon import TrayIcon


@pytest.fixture(scope="function")
def mock_icon_class(mocker) -> MagicMock:
    """Mocks the pystray.Icon class and provides a mock instance."""
    mock_icon = MagicMock()
    # Mock pystray.Icon to return our mock instance
    mocker.patch('pystray.Icon', return_value=mock_icon)
    return mock_icon

def test_tray_icon_init(mock_icon_class):
    icon_instance = mock_icon_class

    test_title = "Test title"
    test_color = "gray"

    icon = TrayIcon(test_title, test_color, None, notifications=False)
    # Assert that the icon object was correctly assigned
    assert icon.icon == icon_instance
    # Assert initial state defaults
    assert icon.color == test_color
    assert icon.title == test_title
    assert icon.notification_active == False
    assert icon.notification_possible == TrayIcon.is_notification_possible()



