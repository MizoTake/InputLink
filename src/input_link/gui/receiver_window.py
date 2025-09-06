"""Receiver window for Input Link - Apple HIG compliant design."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from input_link.gui.main_window import ModernButton, StatusCard


class VirtualControllerCard(QFrame):
    """Apple HIG-compliant virtual controller status card."""

    def __init__(self, controller_number: int):
        super().__init__()
        self.controller_number = controller_number
        self.is_connected = False
        self.client_info = None
        self._setup_ui()
        self._setup_style()

    def _setup_ui(self):
        """Setup the virtual controller card UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Header
        header_layout = QHBoxLayout()

        # Controller info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        # Controller title
        title_label = QLabel(f"Virtual Controller {self.controller_number}")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1D1D1F;")

        # Connection status
        self.status_label = QLabel("Waiting for connection...")
        status_font = QFont()
        status_font.setPointSize(10)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("color: #8E8E93;")

        info_layout.addWidget(title_label)
        info_layout.addWidget(self.status_label)

        # Connection indicator
        self.connection_indicator = QFrame()
        self.connection_indicator.setFixedSize(12, 12)
        self.connection_indicator.setStyleSheet("""
            QFrame {
                background-color: #8E8E93;
                border-radius: 6px;
            }
        """)

        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.connection_indicator)

        # Client info (hidden by default)
        self.client_info_label = QLabel()
        client_font = QFont()
        client_font.setPointSize(9)
        self.client_info_label.setFont(client_font)
        self.client_info_label.setStyleSheet("color: #8E8E93;")
        self.client_info_label.hide()

        layout.addLayout(header_layout)
        layout.addWidget(self.client_info_label)
        self.setLayout(layout)

    def _setup_style(self):
        """Setup Apple HIG card styling."""
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #E5E5EA;
            }
        """)
        self.setFixedHeight(75)

    def update_connection(self, connected: bool, client_info: str = None):
        """Update connection status."""
        self.is_connected = connected
        self.client_info = client_info

        if connected:
            self.status_label.setText("Connected & Active")
            self.status_label.setStyleSheet("color: #34C759;")
            self.connection_indicator.setStyleSheet("""
                QFrame {
                    background-color: #34C759;
                    border-radius: 6px;
                }
            """)

            if client_info:
                self.client_info_label.setText(f"From: {client_info}")
                self.client_info_label.show()
                self.setFixedHeight(95)
        else:
            self.status_label.setText("Waiting for connection...")
            self.status_label.setStyleSheet("color: #8E8E93;")
            self.connection_indicator.setStyleSheet("""
                QFrame {
                    background-color: #8E8E93;
                    border-radius: 6px;
                }
            """)
            self.client_info_label.hide()
            self.setFixedHeight(75)


class ReceiverWindow(QMainWindow):
    """Receiver window for Input Link application following Apple HIG."""

    # Signals
    start_server = Signal()
    stop_server = Signal()
    settings_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.is_running = False
        self.virtual_controller_cards: List[VirtualControllerCard] = []
        self.client_connections: Dict[str, str] = {}
        self._setup_ui()
        self._setup_style()

    def _setup_ui(self):
        """Setup the receiver window UI."""
        self.setWindowTitle("Input Link - Receiver")
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

        # Server status
        self._create_server_status(main_layout)

        # Virtual controllers
        self._create_virtual_controllers_section(main_layout)

        # Settings
        self._create_settings_section(main_layout)

        # Activity log
        self._create_activity_log(main_layout)

        # Control buttons
        self._create_control_buttons(main_layout)

        # Add stretch
        main_layout.addStretch()

    def _create_header(self, layout: QVBoxLayout):
        """Create the header section."""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        # Title
        title_label = QLabel("Receiver")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1D1D1F;")

        # Subtitle
        subtitle_label = QLabel("Receive and simulate controller inputs")
        subtitle_font = QFont()
        subtitle_font.setPointSize(13)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #8E8E93;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        layout.addLayout(header_layout)

    def _create_server_status(self, layout: QVBoxLayout):
        """Create server status section."""
        status_layout = QGridLayout()
        status_layout.setHorizontalSpacing(12)

        # Server status card
        self.server_card = StatusCard("Server Status", "Stopped")
        status_layout.addWidget(self.server_card, 0, 0)

        # Connection count card
        self.connections_card = StatusCard("Active Connections", "0")
        status_layout.addWidget(self.connections_card, 0, 1)

        layout.addLayout(status_layout)

    def _create_virtual_controllers_section(self, layout: QVBoxLayout):
        """Create virtual controllers section with scroll area."""
        controllers_group = QGroupBox("Virtual Controllers")
        controllers_group.setStyleSheet(self._get_group_style())

        # Create main layout for the group
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(16, 16, 16, 16)
        
        # Create scroll area
        self.controllers_scroll = QScrollArea()
        self.controllers_scroll.setWidgetResizable(True)
        self.controllers_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.controllers_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.controllers_scroll.setMaximumHeight(300)  # Limit height to prevent window overflow
        self.controllers_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #F2F2F7;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #C7C7CC;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #AEAEB2;
            }
        """)
        
        # Create widget to contain the controller cards
        controllers_widget = QWidget()
        self.controllers_layout = QVBoxLayout()
        self.controllers_layout.setContentsMargins(0, 0, 0, 0)
        self.controllers_layout.setSpacing(8)

        # Create virtual controller cards (start with 4, expandable based on needs)
        for i in range(1, 5):  # Default 4 controllers  
            card = VirtualControllerCard(i)
            self.virtual_controller_cards.append(card)
            self.controllers_layout.addWidget(card)
        
        # Add stretch to push cards to top
        self.controllers_layout.addStretch()
        controllers_widget.setLayout(self.controllers_layout)
        
        # Set the widget as the scroll area's widget
        self.controllers_scroll.setWidget(controllers_widget)
        
        # Add scroll area to group layout
        group_layout.addWidget(self.controllers_scroll)
        controllers_group.setLayout(group_layout)
        layout.addWidget(controllers_group)

    def _create_settings_section(self, layout: QVBoxLayout):
        """Create settings section."""
        settings_group = QGroupBox("Server Settings")
        settings_group.setStyleSheet(self._get_group_style())

        settings_layout = QGridLayout()
        settings_layout.setContentsMargins(16, 16, 16, 16)
        settings_layout.setHorizontalSpacing(12)
        settings_layout.setVerticalSpacing(8)

        # Listen port
        port_label = QLabel("Listen Port:")
        port_label.setStyleSheet("color: #1D1D1F; font-size: 12px; font-weight: 600;")

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1000, 65535)
        self.port_spin.setValue(8765)
        self.port_spin.setStyleSheet(self._get_input_style())

        # Max controllers
        controllers_label = QLabel("Max Controllers (0=No Limit):")
        controllers_label.setStyleSheet("color: #1D1D1F; font-size: 12px; font-weight: 600;")

        self.max_controllers_spin = QSpinBox()
        self.max_controllers_spin.setRange(0, 8)
        self.max_controllers_spin.setValue(0)
        self.max_controllers_spin.setStyleSheet(self._get_input_style())
        self.max_controllers_spin.valueChanged.connect(self._update_controller_count)

        # Auto-create virtual controllers
        auto_create_label = QLabel("Auto-create Virtual:")
        auto_create_label.setStyleSheet("color: #1D1D1F; font-size: 12px; font-weight: 600;")

        self.auto_create_checkbox = QCheckBox()
        self.auto_create_checkbox.setChecked(True)
        self.auto_create_checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #D1D1D6;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                border-color: #007AFF;
                background-color: #007AFF;
            }
        """)

        settings_layout.addWidget(port_label, 0, 0)
        settings_layout.addWidget(self.port_spin, 0, 1)
        settings_layout.addWidget(controllers_label, 1, 0)
        settings_layout.addWidget(self.max_controllers_spin, 1, 1)
        settings_layout.addWidget(auto_create_label, 2, 0)
        settings_layout.addWidget(self.auto_create_checkbox, 2, 1)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

    def _create_activity_log(self, layout: QVBoxLayout):
        """Create activity log section."""
        log_group = QGroupBox("Activity Log")
        log_group.setStyleSheet(self._get_group_style())

        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(16, 16, 16, 16)

        self.activity_log = QTextEdit()
        self.activity_log.setMaximumHeight(120)
        self.activity_log.setReadOnly(True)
        self.activity_log.setStyleSheet("""
            QTextEdit {
                background-color: #F2F2F7;
                border: 1px solid #D1D1D6;
                border-radius: 8px;
                padding: 8px;
                font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
                font-size: 10px;
                color: #1D1D1F;
            }
        """)

        log_layout.addWidget(self.activity_log)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

    def _create_control_buttons(self, layout: QVBoxLayout):
        """Create control buttons."""
        button_layout = QHBoxLayout()

        self.start_btn = ModernButton("Start Server", "primary")
        self.start_btn.clicked.connect(self._toggle_server)

        self.back_btn = ModernButton("Back to Main", "secondary")

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.back_btn)

        layout.addLayout(button_layout)

    def _toggle_server(self):
        """Toggle server on/off."""
        if self.is_running:
            self.stop_server.emit()
            self.start_btn.setText("Start Server")
            self.start_btn.button_type = "primary"
            self.start_btn._setup_style()
            self.is_running = False
            self._add_log_message("Server stopped")
        else:
            self.start_server.emit()
            self.start_btn.setText("Stop Server")
            self.start_btn.button_type = "destructive"
            self.start_btn._setup_style()
            self.is_running = True
            port = self.port_spin.value()
            self._add_log_message(f"Server starting on port {port}...")

    def _update_controller_count(self, count: int):
        """Update the number of virtual controller cards."""
        # If count is 0, it means no limit - keep current cards and allow expansion
        if count == 0:
            return
            
        # Remove excess cards
        while len(self.virtual_controller_cards) > count:
            card = self.virtual_controller_cards.pop()
            card.parent().layout().removeWidget(card)
            card.deleteLater()

        # Add new cards if needed
        while len(self.virtual_controller_cards) < count:
            card_number = len(self.virtual_controller_cards) + 1
            card = VirtualControllerCard(card_number)
            self.virtual_controller_cards.append(card)

            # Add to the controllers layout (insert before stretch)
            insert_index = len(self.virtual_controller_cards) - 1
            self.controllers_layout.insertWidget(insert_index, card)

    def update_server_status(self, status: str, color: str = "#8E8E93"):
        """Update server status."""
        self.server_card.update_status(status, color)

    def update_connection_count(self, count: int):
        """Update active connections count."""
        self.connections_card.update_status(str(count), "#007AFF" if count > 0 else "#8E8E93")

    def update_virtual_controller(self, controller_number: int, connected: bool, client_info: str = None):
        """Update virtual controller connection status."""
        # Ensure we have enough cards for this controller number
        while len(self.virtual_controller_cards) < controller_number:
            card_number = len(self.virtual_controller_cards) + 1
            card = VirtualControllerCard(card_number)
            self.virtual_controller_cards.append(card)

            # Add to the controllers layout (insert before stretch)
            insert_index = len(self.virtual_controller_cards) - 1
            self.controllers_layout.insertWidget(insert_index, card)
        
        if 1 <= controller_number <= len(self.virtual_controller_cards):
            card = self.virtual_controller_cards[controller_number - 1]
            card.update_connection(connected, client_info)

    def add_log_message(self, message: str):
        """Add message to activity log."""
        self._add_log_message(message)

    def _add_log_message(self, message: str):
        """Internal method to add log message."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_log.append(f"[{timestamp}] {message}")

        # Auto-scroll to bottom
        scrollbar = self.activity_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

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
            QSpinBox {
                background-color: white;
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 12px;
                color: #1D1D1F;
                min-height: 20px;
            }
            QSpinBox:focus {
                border-color: #007AFF;
                outline: none;
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
