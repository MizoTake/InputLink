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


class ModernButton(QPushButton):
    """Apple HIG-compliant modern button with rounded corners."""

    def __init__(self, text: str, button_type: str = "primary"):
        super().__init__(text)
        self.button_type = button_type
        self._setup_style()

    def _setup_style(self):
        """Setup Apple HIG button styling."""
        if self.button_type == "primary":
            style = """
                QPushButton {
                    background-color: #007AFF;
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-weight: 600;
                    font-size: 13px;
                    padding: 8px 16px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #0056CC;
                }
                QPushButton:pressed {
                    background-color: #004499;
                }
                QPushButton:disabled {
                    background-color: #E5E5EA;
                    color: #8E8E93;
                }
            """
        elif self.button_type == "secondary":
            style = """
                QPushButton {
                    background-color: #F2F2F7;
                    border: 1px solid #D1D1D6;
                    border-radius: 8px;
                    color: #007AFF;
                    font-weight: 600;
                    font-size: 13px;
                    padding: 8px 16px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #E5E5EA;
                }
                QPushButton:pressed {
                    background-color: #D1D1D6;
                }
            """
        else:  # destructive
            style = """
                QPushButton {
                    background-color: #FF3B30;
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-weight: 600;
                    font-size: 13px;
                    padding: 8px 16px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #D70015;
                }
                QPushButton:pressed {
                    background-color: #A20000;
                }
            """
        self.setStyleSheet(style)


class StatusCard(QFrame):
    """Apple HIG-compliant status card widget."""

    def __init__(self, title: str, status: str = "Not Connected"):
        super().__init__()
        self.title = title
        self.status = status
        self._setup_ui()
        self._setup_style()

    def _setup_ui(self):
        """Setup the card UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        # Title
        title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1D1D1F;")

        # Status
        self.status_label = QLabel(self.status)
        status_font = QFont()
        status_font.setPointSize(11)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("color: #8E8E93;")

        layout.addWidget(title_label)
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
        """)
        self.setFixedHeight(80)

    def update_status(self, status: str, color: str = "#8E8E93"):
        """Update the status text and color."""
        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"color: {color};")


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

    def _setup_ui(self):
        """Setup the main user interface."""
        self.setWindowTitle("Input Link")
        self.setMinimumSize(400, 600)
        self.resize(480, 650)

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
        """Create the header section."""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        # App title
        title_label = QLabel("Input Link")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1D1D1F;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Subtitle
        subtitle_label = QLabel("Network Controller Forwarding")
        subtitle_font = QFont()
        subtitle_font.setPointSize(13)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #8E8E93;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        layout.addLayout(header_layout)

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
        control_group.setStyleSheet("""
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
        """)

        control_layout = QVBoxLayout()
        control_layout.setContentsMargins(16, 16, 16, 16)
        control_layout.setSpacing(12)

        # Button row 1
        button_row1 = QHBoxLayout()
        self.start_sender_btn = ModernButton("Start Sender", "primary")
        self.start_receiver_btn = ModernButton("Start Receiver", "primary")

        button_row1.addWidget(self.start_sender_btn)
        button_row1.addWidget(self.start_receiver_btn)

        # Button row 2
        button_row2 = QHBoxLayout()
        self.stop_btn = ModernButton("Stop All", "destructive")
        self.config_btn = ModernButton("Settings", "secondary")

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
        config_group.setStyleSheet("""
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
        """)

        config_layout = QGridLayout()
        config_layout.setContentsMargins(16, 16, 16, 16)
        config_layout.setHorizontalSpacing(12)
        config_layout.setVerticalSpacing(8)

        # Host/Port display
        host_label = QLabel("Host:")
        host_label.setStyleSheet("color: #8E8E93; font-size: 11px;")
        self.host_value = QLabel("127.0.0.1")
        self.host_value.setStyleSheet("color: #1D1D1F; font-size: 11px;")

        port_label = QLabel("Port:")
        port_label.setStyleSheet("color: #8E8E93; font-size: 11px;")
        self.port_value = QLabel("8765")
        self.port_value.setStyleSheet("color: #1D1D1F; font-size: 11px;")

        config_layout.addWidget(host_label, 0, 0)
        config_layout.addWidget(self.host_value, 0, 1)
        config_layout.addWidget(port_label, 1, 0)
        config_layout.addWidget(self.port_value, 1, 1)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

    def _create_log_section(self, layout: QVBoxLayout):
        """Create log display section."""
        log_group = QGroupBox("Activity Log")
        log_group.setStyleSheet("""
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
        """)

        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(16, 16, 16, 16)

        self.log_display = QTextEdit()
        self.log_display.setMaximumHeight(150)
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("""
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
        """Setup global application styling."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F2F2F7;
            }
            QWidget {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
        """)

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
