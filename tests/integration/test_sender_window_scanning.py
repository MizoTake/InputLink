"""Integration tests for SenderWindow controller scanning."""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from input_link.gui.sender_window import SenderWindow
from input_link.core import DetectedController
from input_link.core.controller_manager import ControllerConnectionState


@pytest.fixture
def qt_app():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    if app:
        app.quit()


@pytest.fixture
def sender_window(qt_app):
    """Create SenderWindow instance for tests."""
    window = SenderWindow()
    yield window
    window.close()


class TestSenderWindowScanning:
    """Test SenderWindow controller scanning UI behavior."""

    def test_scan_button_reset_after_update(self, sender_window):
        """Should reset scan button state after controller update."""
        # Initially scan button should be enabled
        assert sender_window.scan_btn.isEnabled()
        assert sender_window.scan_btn.text() == "Scan Controllers"

        # Simulate scanning state
        sender_window.scan_btn.setText("Scanning...")
        sender_window.scan_btn.setEnabled(False)

        # Create mock controller
        controller = DetectedController(
            pygame_id=0,
            device_id=1,
            name="Test Controller",
            guid="test_guid",
            num_axes=6,
            num_buttons=14,
            num_hats=1,
            state=ControllerConnectionState.CONNECTED,
            assigned_number=1
        )

        # Update controllers should reset button
        sender_window.update_controllers([controller])

        # Button should be reset
        assert sender_window.scan_btn.isEnabled()
        assert sender_window.scan_btn.text() == "Scan Controllers"

    def test_scan_button_reset_after_empty_update(self, sender_window):
        """Should reset scan button state even with empty controller list."""
        # Simulate scanning state
        sender_window.scan_btn.setText("Scanning...")
        sender_window.scan_btn.setEnabled(False)

        # Update with empty list
        sender_window.update_controllers([])

        # Button should be reset
        assert sender_window.scan_btn.isEnabled()
        assert sender_window.scan_btn.text() == "Scan Controllers"

    def test_controller_list_updates_correctly(self, sender_window):
        """Should update controller list correctly on multiple scans."""
        # First update - add controller
        controller1 = DetectedController(
            pygame_id=0,
            device_id=1,
            name="Xbox Controller",
            guid="xbox_guid",
            num_axes=6,
            num_buttons=14,
            num_hats=1,
            state=ControllerConnectionState.CONNECTED,
            assigned_number=1
        )

        sender_window.update_controllers([controller1])

        assert len(sender_window.controller_cards) == 1
        assert sender_window.controller_count_label.text() == "1 controller detected"

        # Second update - different controller
        controller2 = DetectedController(
            pygame_id=0,
            device_id=2,
            name="DualShock 4",
            guid="ps_guid",
            num_axes=6,
            num_buttons=14,
            num_hats=1,
            state=ControllerConnectionState.CONNECTED,
            assigned_number=1
        )

        sender_window.update_controllers([controller2])

        # Should replace previous controller
        assert len(sender_window.controller_cards) == 1
        assert sender_window.controller_count_label.text() == "1 controller detected"

        # Third update - empty list
        sender_window.update_controllers([])

        assert len(sender_window.controller_cards) == 0
        assert sender_window.controller_count_label.text() == "0 controllers detected"

    def test_scan_controllers_signal_emission(self, sender_window):
        """Should emit scan_controllers_requested signal when scan button clicked."""
        signal_emitted = []
        sender_window.scan_controllers_requested.connect(lambda: signal_emitted.append(True))

        # Click scan button
        QTest.mouseClick(sender_window.scan_btn, 1)  # Qt::LeftButton = 1

        # Should emit signal
        assert len(signal_emitted) == 1

    def test_controller_display_consistency(self, sender_window):
        """Should consistently display same controllers across multiple updates."""
        controller = DetectedController(
            pygame_id=0,
            device_id=1,
            name="Consistent Controller",
            guid="consistent_guid",
            num_axes=6,
            num_buttons=14,
            num_hats=1,
            state=ControllerConnectionState.CONNECTED,
            assigned_number=1
        )

        # First update
        sender_window.update_controllers([controller])
        first_card_name = sender_window.controller_cards[0].controller_name_label.text()

        # Second update with same controller
        sender_window.update_controllers([controller])
        second_card_name = sender_window.controller_cards[0].controller_name_label.text()

        # Names should be consistent
        assert first_card_name == second_card_name
        assert "Consistent Controller" in first_card_name

    def test_empty_state_handling(self, sender_window):
        """Should handle empty controller state correctly."""
        # Start with some controllers
        controller = DetectedController(
            pygame_id=0,
            device_id=1,
            name="Temporary Controller",
            guid="temp_guid",
            num_axes=6,
            num_buttons=14,
            num_hats=1,
            state=ControllerConnectionState.CONNECTED,
            assigned_number=1
        )

        sender_window.update_controllers([controller])
        assert len(sender_window.controller_cards) == 1

        # Update with empty list
        sender_window.update_controllers([])

        # Should show empty state
        assert len(sender_window.controller_cards) == 0
        assert sender_window.controller_count_label.text() == "0 controllers detected"

        # Re-add controller
        sender_window.update_controllers([controller])
        assert len(sender_window.controller_cards) == 1
        assert sender_window.controller_count_label.text() == "1 controller detected"