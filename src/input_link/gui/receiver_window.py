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
from input_link.gui.theme_manager import theme_manager
from input_link.gui.enhanced_widgets import (
    AnimatedButton, EnhancedStatusCard, NetworkQualityWidget, EnhancedScrollArea,
    EnhancedVirtualControllerCard
)




class ReceiverWindow(QMainWindow):
    """Receiver window for Input Link application following Apple HIG."""

    # Signals
    start_server = Signal()
    stop_server = Signal()
    settings_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.is_running = False
        self.virtual_controller_cards: List[EnhancedVirtualControllerCard] = []
        self.client_connections: Dict[str, str] = {}
        self._setup_ui()
        self._setup_style()
        
        # Connect to theme changes
        theme_manager.theme_changed.connect(self._setup_style)

    def _setup_ui(self):
        """Setup the receiver window UI."""
        self.setWindowTitle("Input Link - Receiver")
        self.setMinimumSize(550, 750)
        self.resize(620, 800)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 16, 20, 16)  # Reduced margins
        main_layout.setSpacing(16)  # Reduced spacing from 20 to 16
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
        
        # Create enhanced scroll area
        self.controllers_scroll = EnhancedScrollArea()
        self.controllers_scroll.set_max_height(380)  # Increased from 300 to 380
        
        # Create widget to contain the controller cards
        controllers_widget = QWidget()
        self.controllers_layout = QVBoxLayout()
        self.controllers_layout.setContentsMargins(0, 0, 0, 0)
        self.controllers_layout.setSpacing(8)

        # Create virtual controller cards in priority order (start with 4, expandable based on needs)
        for i in range(1, 5):  # Default 4 controllers - most commonly used first  
            card = EnhancedVirtualControllerCard(i)
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

        # Listen host
        host_label = QLabel("Listen Host:")
        host_label.setStyleSheet("color: #1D1D1F; font-size: 12px; font-weight: 600;")

        from PySide6.QtWidgets import QComboBox
        self.host_combo = QComboBox()
        self.host_combo.setEditable(True)
        self.host_combo.addItems(["0.0.0.0", "127.0.0.1", "192.168.1.10", "10.0.0.10"])
        self.host_combo.setStyleSheet(self._get_input_style())
        self.host_combo.currentTextChanged.connect(self._emit_settings)

        # Listen port
        port_label = QLabel("Listen Port:")
        port_label.setStyleSheet("color: #1D1D1F; font-size: 12px; font-weight: 600;")

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1000, 65535)
        self.port_spin.setValue(8765)
        self.port_spin.setStyleSheet(self._get_input_style())
        self.port_spin.valueChanged.connect(lambda _: self._emit_settings())

        # Max controllers
        controllers_label = QLabel("Max Controllers (0=No Limit):")
        controllers_label.setStyleSheet("color: #1D1D1F; font-size: 12px; font-weight: 600;")

        self.max_controllers_spin = QSpinBox()
        self.max_controllers_spin.setRange(0, 128)
        self.max_controllers_spin.setValue(0)
        self.max_controllers_spin.setStyleSheet(self._get_input_style())
        self.max_controllers_spin.valueChanged.connect(self._update_controller_count)
        self.max_controllers_spin.valueChanged.connect(lambda _: self._emit_settings())

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

        settings_layout.addWidget(host_label, 0, 0)
        settings_layout.addWidget(self.host_combo, 0, 1)
        settings_layout.addWidget(port_label, 1, 0)
        settings_layout.addWidget(self.port_spin, 1, 1)
        settings_layout.addWidget(controllers_label, 2, 0)
        settings_layout.addWidget(self.max_controllers_spin, 2, 1)
        settings_layout.addWidget(auto_create_label, 3, 0)
        settings_layout.addWidget(self.auto_create_checkbox, 3, 1)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

    def _emit_settings(self):
        """Emit current receiver settings (host/port/max/auto)."""
        self.settings_changed.emit({
            "host": self.host_combo.currentText().strip(),
            "port": int(self.port_spin.value()),
            "max_controllers": int(self.max_controllers_spin.value()),
            "auto_create": bool(self.auto_create_checkbox.isChecked()),
        })

    def _create_activity_log(self, layout: QVBoxLayout):
        """Create activity log section."""
        log_group = QGroupBox("Activity Log")
        log_group.setStyleSheet(self._get_group_style())

        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(16, 16, 16, 16)

        self.activity_log = QTextEdit()
        self.activity_log.setMaximumHeight(90)  # Reduced from 120 to 90
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

        self.start_btn = AnimatedButton("Start Server", "primary")
        self.start_btn.clicked.connect(self._toggle_server)

        self.back_btn = AnimatedButton("Back to Main", "secondary")

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
            card = EnhancedVirtualControllerCard(card_number)
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
        """Update virtual controller connection status with smart positioning."""
        # Ensure we have enough cards for this controller number
        while len(self.virtual_controller_cards) < controller_number:
            card_number = len(self.virtual_controller_cards) + 1
            card = EnhancedVirtualControllerCard(card_number)
            self.virtual_controller_cards.append(card)

            # Add to the controllers layout (insert before stretch)
            insert_index = len(self.virtual_controller_cards) - 1
            self.controllers_layout.insertWidget(insert_index, card)
        
        if 1 <= controller_number <= len(self.virtual_controller_cards):
            card = self.virtual_controller_cards[controller_number - 1]
            card.update_connection(connected, client_info)
            
            # Reorder cards to show active ones first
            self._reorder_virtual_controller_cards()

    def _reorder_virtual_controller_cards(self):
        """Reorder virtual controller cards to show active ones first."""
        if not self.virtual_controller_cards:
            return
        
        # Sort cards by connection status and controller number
        sorted_cards = sorted(
            self.virtual_controller_cards, 
            key=lambda card: (
                not card.is_connected,  # Connected first (False sorts before True)
                card.controller_number  # Then by controller number
            )
        )
        
        # Remove all cards from layout
        for card in self.virtual_controller_cards:
            self.controllers_layout.removeWidget(card)
        
        # Remove the stretch item temporarily
        stretch_item = self.controllers_layout.takeAt(self.controllers_layout.count() - 1)
        
        # Re-add cards in sorted order
        for card in sorted_cards:
            self.controllers_layout.addWidget(card)
        
        # Re-add stretch to push cards to top
        if stretch_item:
            self.controllers_layout.addItem(stretch_item)
        else:
            self.controllers_layout.addStretch()

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
        return theme_manager.get_group_style()

    def _get_input_style(self) -> str:
        """Get consistent input field styling."""
        return theme_manager.get_input_style()

    def _setup_style(self):
        """Setup window styling."""
        self.auto_create_checkbox.toggled.connect(lambda _: self._emit_settings())
        self.setStyleSheet(theme_manager.get_window_style())
