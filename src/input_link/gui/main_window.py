"""Main window for Input Link - Apple HIG compliant design."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from input_link.models import ConfigModel
from input_link.gui.theme_manager import theme_manager
from input_link.gui.enhanced_widgets import (
    AnimatedButton, EnhancedStatusCard, ThemeToggleButton,
    NetworkQualityWidget
)


# Legacy ModernButton class - kept for backward compatibility
class ModernButton(AnimatedButton):
    """Apple HIG-compliant modern button with animations - enhanced version."""
    pass


# Legacy StatusCard class - kept for backward compatibility
class StatusCard(EnhancedStatusCard):
    """Apple HIG-compliant status card widget - enhanced version."""
    
    def update_status(self, status: str, color: str = "#8E8E93"):
        """Update the status text and color (legacy method)."""
        # Map old color values to new status types
        if color == "#34C759":
            status_type = "success"
        elif color == "#FF9F0A":
            status_type = "warning"
        elif color == "#FF3B30":
            status_type = "error"
        elif color == "#007AFF":
            status_type = "info"
        else:
            status_type = "info"
        
        super().update_status(status, status_type)


class MainWindow(QMainWindow):
    """Main window for Input Link application following Apple HIG."""

    # Signals
    start_sender = Signal()
    start_receiver = Signal()
    stop_services = Signal()

    def __init__(self):
        super().__init__()
        self.config: Optional[ConfigModel] = None
        self.tray_icon: Optional[QSystemTrayIcon] = None
        self._setup_ui()
        self._setup_tray()
        self._setup_style()
        
        # Connect to theme changes
        theme_manager.theme_changed.connect(self._setup_style)

    def _setup_ui(self):
        """Setup the main user interface."""
        self.setWindowTitle("Input Link")
        self.setMinimumSize(520, 700)
        self.resize(600, 750)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 16, 20, 16)  # Reduced margins
        main_layout.setSpacing(16)  # Reduced spacing from 20 to 16
        central_widget.setLayout(main_layout)

        # Header with theme toggle
        self._create_header(main_layout)
        
        # Network quality indicator
        self._create_network_section(main_layout)

        # Status cards
        self._create_status_section(main_layout)

        # Control buttons
        self._create_control_section(main_layout)

        # Configuration section
        self._create_config_section(main_layout)

        # Log section
        self._create_log_section(main_layout)

        # Add stretch to push everything up
        main_layout.addStretch()

    def _create_header(self, layout: QVBoxLayout):
        """Create the header section with theme toggle."""
        header_container = QHBoxLayout()
        
        # Left side - title and subtitle
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        # App title
        title_label = QLabel("Input Link")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {theme_manager.get_color('text_primary')};")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Subtitle
        subtitle_label = QLabel("Network Controller Forwarding")
        subtitle_font = QFont()
        subtitle_font.setPointSize(13)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')};")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        # Right side - theme toggle
        theme_toggle = ThemeToggleButton()
        
        header_container.addLayout(header_layout)
        header_container.addStretch()
        header_container.addWidget(theme_toggle, 0, Qt.AlignmentFlag.AlignTop)
        
        layout.addLayout(header_container)
    
    def _create_network_section(self, layout: QVBoxLayout):
        """Create network quality section."""
        self.network_quality = NetworkQualityWidget()
        layout.addWidget(self.network_quality)

    def _create_status_section(self, layout: QVBoxLayout):
        """Create status cards section."""
        status_layout = QGridLayout()
        status_layout.setHorizontalSpacing(12)
        status_layout.setVerticalSpacing(12)

        # Sender status card
        self.sender_card = StatusCard("Sender", "Ready")
        status_layout.addWidget(self.sender_card, 0, 0)

        # Receiver status card
        self.receiver_card = StatusCard("Receiver", "Ready")
        status_layout.addWidget(self.receiver_card, 0, 1)

        layout.addLayout(status_layout)

    def _create_control_section(self, layout: QVBoxLayout):
        """Create control buttons section."""
        control_group = QGroupBox("Control")
        control_group.setStyleSheet(theme_manager.get_group_style())

        control_layout = QVBoxLayout()
        control_layout.setContentsMargins(16, 16, 16, 16)
        control_layout.setSpacing(12)

        # Button row 1
        button_row1 = QHBoxLayout()
        self.start_sender_btn = AnimatedButton("Start Sender", "primary")
        self.start_receiver_btn = AnimatedButton("Start Receiver", "primary")

        button_row1.addWidget(self.start_sender_btn)
        button_row1.addWidget(self.start_receiver_btn)

        # Button row 2
        button_row2 = QHBoxLayout()
        self.stop_btn = AnimatedButton("Stop All", "destructive")
        self.config_btn = AnimatedButton("Settings", "secondary")

        button_row2.addWidget(self.stop_btn)
        button_row2.addWidget(self.config_btn)

        control_layout.addLayout(button_row1)
        control_layout.addLayout(button_row2)
        control_group.setLayout(control_layout)

        layout.addWidget(control_group)

        # Connect signals
        self.start_sender_btn.clicked.connect(self.start_sender.emit)
        self.start_receiver_btn.clicked.connect(self.start_receiver.emit)
        self.stop_btn.clicked.connect(self.stop_services.emit)
        self.config_btn.clicked.connect(self._show_settings)

    def _create_config_section(self, layout: QVBoxLayout):
        """Create configuration display section."""
        config_group = QGroupBox("Connection Settings")
        config_group.setStyleSheet(theme_manager.get_group_style())

        config_layout = QGridLayout()
        config_layout.setContentsMargins(16, 16, 16, 16)
        config_layout.setHorizontalSpacing(12)
        config_layout.setVerticalSpacing(8)

        # Host/Port display
        host_label = QLabel("Host:")
        host_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')}; font-size: 11px;")
        self.host_value = QLabel("127.0.0.1")
        self.host_value.setStyleSheet(f"color: {theme_manager.get_color('text_primary')}; font-size: 11px;")

        port_label = QLabel("Port:")
        port_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')}; font-size: 11px;")
        self.port_value = QLabel("8765")
        self.port_value.setStyleSheet(f"color: {theme_manager.get_color('text_primary')}; font-size: 11px;")

        config_layout.addWidget(host_label, 0, 0)
        config_layout.addWidget(self.host_value, 0, 1)
        config_layout.addWidget(port_label, 1, 0)
        config_layout.addWidget(self.port_value, 1, 1)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

    def _create_log_section(self, layout: QVBoxLayout):
        """Create log display section."""
        log_group = QGroupBox("Activity Log")
        log_group.setStyleSheet(theme_manager.get_group_style())

        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(16, 16, 16, 16)

        self.log_display = QTextEdit()
        self.log_display.setMaximumHeight(100)  # Reduced from 150 to 100
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme_manager.get_color('input_bg')};
                border: 1px solid {theme_manager.get_color('border_secondary')};
                border-radius: 8px;
                padding: 8px;
                font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
                font-size: 10px;
                color: {theme_manager.get_color('text_primary')};
            }}
        """)

        log_layout.addWidget(self.log_display)
        log_group.setLayout(log_layout)

        layout.addWidget(log_group)

    def _setup_tray(self):
        """Setup system tray icon."""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)

            # Create tray menu
            tray_menu = QMenu()

            show_action = QAction("Show Input Link", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)

            tray_menu.addSeparator()

            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(QApplication.quit)
            tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self._tray_activated)

            # Set tray icon (placeholder)
            self.tray_icon.show()

    def _setup_style(self):
        """Setup global application styling with theme support."""
        self.setStyleSheet(theme_manager.get_window_style())

    def _show_settings(self):
        """Show settings dialog."""
        # Placeholder for settings dialog
        QMessageBox.information(self, "Settings", "Settings dialog will be implemented here.")

    def _tray_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()

    def closeEvent(self, event):
        """Handle close event - minimize to tray if available."""
        if self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()

    def update_sender_status(self, status: str, color: str = "#8E8E93"):
        """Update sender status card."""
        self.sender_card.update_status(status, color)

    def update_receiver_status(self, status: str, color: str = "#8E8E93"):
        """Update receiver status card."""
        self.receiver_card.update_status(status, color)

    def add_log_message(self, message: str):
        """Add message to activity log."""
        from PySide6.QtCore import QTime
        current_time = QTime.currentTime().toString('hh:mm:ss')
        self.log_display.append(f"[{current_time}] {message}")

    def update_config_display(self, config: ConfigModel):
        """Update configuration display."""
        if hasattr(config, "sender_config"):
            self.host_value.setText(config.sender_config.receiver_host)
            self.port_value.setText(str(config.sender_config.receiver_port))
        elif hasattr(config, "receiver_config"):
            self.port_value.setText(str(config.receiver_config.listen_port))
    
    def update_network_quality(self, status: str, latency: int = 0, signal_strength: int = 0, packet_loss: float = 0.0):
        """Update network quality indicators."""
        self.network_quality.update_metrics(status, latency, signal_strength, packet_loss)
