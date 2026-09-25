import pytest
from pytest_mock import MockerFixture
from unittest.mock import MagicMock, patch
from pystray import Menu, MenuItem
from PIL import Image
from src.alert_tray_icon.icon import TrayIcon


@pytest.fixture(scope="function")
def mock_icon_class(mocker: MockerFixture) -> MagicMock:
    """Mocks the pystray.Icon class and provides a mock instance."""
    mock_icon = MagicMock()
    # Mock pystray.Icon to return our mock instance
    mocker.patch('pystray.Icon', return_value=mock_icon)
    return mock_icon

@pytest.fixture
def mock_image(mocker: MockerFixture) -> MagicMock:
    """Mocks PIL.Image creation."""
    # Patch Image.new to ensure it returns a controlled mock object
    mock_image_instance = MagicMock(spec=Image)
    mocker.patch('main.Image', MagicMock(new_side_effect=lambda *args, **kwargs: mock_image_instance))
    return mock_image_instance

def test_tray_icon_init(mock_icon_class: MagicMock) -> None:
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



