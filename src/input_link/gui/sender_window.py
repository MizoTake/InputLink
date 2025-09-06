"""Sender window for Input Link - Apple HIG compliant design."""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from input_link.core.controller_manager import DetectedController
from input_link.gui.main_window import ModernButton, StatusCard


class ControllerCard(QFrame):
    """Apple HIG-compliant controller status card."""

    controller_toggled = Signal(str, bool)  # controller_id, enabled

    def __init__(self, controller: DetectedController):
        super().__init__()
        self.controller = controller
        self.is_enabled = False
        self._setup_ui()
        self._setup_style()

    def _setup_ui(self):
        """Setup the controller card UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Header with controller name and toggle
        header_layout = QHBoxLayout()

        # Controller info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        # Controller name
        name_label = QLabel(self.controller.name)
        name_font = QFont()
        name_font.setPointSize(12)
        name_font.setWeight(QFont.Weight.DemiBold)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #1D1D1F;")

        # Controller details
        player_num = getattr(self.controller, 'assigned_number', 1) or 1
        input_method = getattr(self.controller, 'preferred_input_method', 'XINPUT')
        details = f"Player {player_num} • {input_method.value if hasattr(input_method, 'value') else input_method}"
        details_label = QLabel(details)
        details_font = QFont()
        details_font.setPointSize(10)
        details_label.setFont(details_font)
        details_label.setStyleSheet("color: #8E8E93;")

        info_layout.addWidget(name_label)
        info_layout.addWidget(details_label)

        # Enable toggle
        self.enable_checkbox = QCheckBox()
        self.enable_checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #D1D1D6;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                border-color: #007AFF;
                background-color: #007AFF;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMCAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTggMi41TDQgNi41TDIgNC41IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjEuNSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
        """)
        self.enable_checkbox.toggled.connect(self._on_toggle)

        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.enable_checkbox)

        # Connection status
        self.status_label = QLabel("Ready")
        status_font = QFont()
        status_font.setPointSize(10)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("color: #34C759;")

        layout.addLayout(header_layout)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def _setup_style(self):
        """Setup Apple HIG card styling."""
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #E5E5EA;
            }
            QFrame:hover {
                border-color: #D1D1D6;
            }
        """)
        self.setFixedHeight(85)

    def _on_toggle(self, checked: bool):
        """Handle controller enable/disable toggle."""
        self.is_enabled = checked
        controller_id = getattr(self.controller, 'identifier', f'{self.controller.guid}_{self.controller.device_id}')
        self.controller_toggled.emit(controller_id, checked)

        # Update status based on toggle
        if checked:
            self.status_label.setText("Active")
            self.status_label.setStyleSheet("color: #34C759;")
        else:
            self.status_label.setText("Disabled")
            self.status_label.setStyleSheet("color: #8E8E93;")

    def update_status(self, status: str, color: str = "#8E8E93"):
        """Update controller status."""
        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"color: {color};")


class SenderWindow(QMainWindow):
    """Sender window for Input Link application following Apple HIG."""

    # Signals
    start_capture = Signal()
    stop_capture = Signal()
    controller_enabled = Signal(str, bool)
    settings_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.is_capturing = False
        self.controller_cards: List[ControllerCard] = []
        self._setup_ui()
        self._setup_style()

    def _setup_ui(self):
        """Setup the sender window UI."""
        self.setWindowTitle("Input Link - Sender")
        self.setMinimumSize(450, 650)
        self.resize(480, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(20)
        central_widget.setLayout(main_layout)

        # Header
        self._create_header(main_layout)

        # Connection status
        self._create_connection_status(main_layout)

        # Controller detection and list
        self._create_controller_section(main_layout)

        # Settings
        self._create_settings_section(main_layout)

        # Control buttons
        self._create_control_buttons(main_layout)

        # Add stretch
        main_layout.addStretch()

    def _create_header(self, layout: QVBoxLayout):
        """Create the header section."""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        # Title
        title_label = QLabel("Sender")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1D1D1F;")

        # Subtitle
        subtitle_label = QLabel("Capture and forward controller inputs")
        subtitle_font = QFont()
        subtitle_font.setPointSize(13)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #8E8E93;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        layout.addLayout(header_layout)

    def _create_connection_status(self, layout: QVBoxLayout):
        """Create connection status section."""
        self.connection_card = StatusCard("Connection Status", "Disconnected")
        layout.addWidget(self.connection_card)

    def _create_controller_section(self, layout: QVBoxLayout):
        """Create controller detection and list section."""
        controller_group = QGroupBox("Controllers")
        controller_group.setStyleSheet(self._get_group_style())

        controller_layout = QVBoxLayout()
        controller_layout.setContentsMargins(16, 16, 16, 16)
        controller_layout.setSpacing(12)

        # Detection controls
        detection_layout = QHBoxLayout()

        self.scan_btn = ModernButton("Scan Controllers", "secondary")
        self.scan_btn.clicked.connect(self._scan_controllers)

        self.controller_count_label = QLabel("0 controllers detected")
        self.controller_count_label.setStyleSheet("color: #8E8E93; font-size: 11px;")

        detection_layout.addWidget(self.scan_btn)
        detection_layout.addStretch()
        detection_layout.addWidget(self.controller_count_label)

        # Controller list area
        self.controller_scroll_area = QWidget()
        self.controller_scroll_layout = QVBoxLayout()
        self.controller_scroll_layout.setSpacing(8)
        self.controller_scroll_area.setLayout(self.controller_scroll_layout)

        # No controllers message
        self.no_controllers_label = QLabel("No controllers detected\nConnect a controller and click 'Scan Controllers'")
        self.no_controllers_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_controllers_label.setStyleSheet("""
            color: #8E8E93;
            font-size: 12px;
            padding: 20px;
            border: 2px dashed #D1D1D6;
            border-radius: 8px;
            background-color: #F9F9F9;
        """)
        self.controller_scroll_layout.addWidget(self.no_controllers_label)

        controller_layout.addLayout(detection_layout)
        controller_layout.addWidget(self.controller_scroll_area)

        controller_group.setLayout(controller_layout)
        layout.addWidget(controller_group)

    def _create_settings_section(self, layout: QVBoxLayout):
        """Create settings section."""
        settings_group = QGroupBox("Settings")
        settings_group.setStyleSheet(self._get_group_style())

        settings_layout = QGridLayout()
        settings_layout.setContentsMargins(16, 16, 16, 16)
        settings_layout.setHorizontalSpacing(12)
        settings_layout.setVerticalSpacing(8)

        # Receiver host
        host_label = QLabel("Receiver Host:")
        host_label.setStyleSheet("color: #1D1D1F; font-size: 12px; font-weight: 600;")

        self.host_combo = QComboBox()
        self.host_combo.setEditable(True)
        self.host_combo.addItems(["127.0.0.1", "192.168.1.100", "10.0.0.100"])
        self.host_combo.setStyleSheet(self._get_input_style())

        # Receiver port
        port_label = QLabel("Port:")
        port_label.setStyleSheet("color: #1D1D1F; font-size: 12px; font-weight: 600;")

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1000, 65535)
        self.port_spin.setValue(8765)
        self.port_spin.setStyleSheet(self._get_input_style())

        # Polling rate
        rate_label = QLabel("Polling Rate (Hz):")
        rate_label.setStyleSheet("color: #1D1D1F; font-size: 12px; font-weight: 600;")

        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(30, 120)
        self.rate_spin.setValue(60)
        self.rate_spin.setStyleSheet(self._get_input_style())

        settings_layout.addWidget(host_label, 0, 0)
        settings_layout.addWidget(self.host_combo, 0, 1)
        settings_layout.addWidget(port_label, 1, 0)
        settings_layout.addWidget(self.port_spin, 1, 1)
        settings_layout.addWidget(rate_label, 2, 0)
        settings_layout.addWidget(self.rate_spin, 2, 1)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

    def _create_control_buttons(self, layout: QVBoxLayout):
        """Create control buttons."""
        button_layout = QHBoxLayout()

        self.start_btn = ModernButton("Start Capturing", "primary")
        self.start_btn.clicked.connect(self._toggle_capture)

        self.back_btn = ModernButton("Back to Main", "secondary")

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.back_btn)

        layout.addLayout(button_layout)

    def _scan_controllers(self):
        """Handle controller scanning."""
        # Emit signal to trigger controller scan
        # This will be connected to the actual controller manager
        # For now, we'll add a placeholder message
        print("Scan Controllers button clicked")

    def _toggle_capture(self):
        """Toggle capture on/off."""
        if self.is_capturing:
            self.stop_capture.emit()
            self.start_btn.setText("Start Capturing")
            self.start_btn.button_type = "primary"
            self.start_btn._setup_style()
            self.is_capturing = False
        else:
            self.start_capture.emit()
            self.start_btn.setText("Stop Capturing")
            self.start_btn.button_type = "destructive"
            self.start_btn._setup_style()
            self.is_capturing = True

    def update_controllers(self, controllers: List[DetectedController]):
        """Update the controller list."""
        # Clear existing cards
        for card in self.controller_cards:
            self.controller_scroll_layout.removeWidget(card)
            card.deleteLater()
        self.controller_cards.clear()

        # Remove no controllers message
        self.no_controllers_label.hide()

        if not controllers:
            self.no_controllers_label.show()
            self.controller_count_label.setText("0 controllers detected")
            return

        # Add new controller cards
        for controller in controllers:
            card = ControllerCard(controller)
            card.controller_toggled.connect(self.controller_enabled.emit)
            self.controller_cards.append(card)
            self.controller_scroll_layout.addWidget(card)

        # Update count
        count = len(controllers)
        self.controller_count_label.setText(f"{count} controller{'s' if count != 1 else ''} detected")

    def update_connection_status(self, status: str, color: str = "#8E8E93"):
        """Update connection status."""
        self.connection_card.update_status(status, color)

    def _get_group_style(self) -> str:
        """Get consistent group box styling."""
        return """
            QGroupBox {
                font-size: 13px;
                font-weight: 600;
                color: #1D1D1F;
                border: 1px solid #E5E5EA;
                border-radius: 12px;
                margin: 8px 0;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: #F2F2F7;
            }
        """

    def _get_input_style(self) -> str:
        """Get consistent input field styling."""
        return """
            QComboBox, QSpinBox {
                background-color: white;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 12px;
                color: #1D1D1F;
                min-height: 20px;
            }
            QComboBox:focus, QSpinBox:focus {
                border-color: #007AFF;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #8E8E93;
                margin-right: 8px;
            }
        """

    def _setup_style(self):
        """Setup window styling."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F2F2F7;
            }
            QWidget {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
        """)
