"""Sender window for Input Link - Apple HIG compliant design."""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt, Signal, QTimer
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
from input_link.gui.theme_manager import theme_manager
from input_link.gui.enhanced_widgets import (
    AnimatedButton, EnhancedStatusCard, ControllerVisualization,
    NetworkQualityWidget, ModernCardScrollArea, EnhancedControllerCard
)



class SenderWindow(QMainWindow):
    """Sender window for Input Link application following Apple HIG."""

    # Signals
    start_capture = Signal()
    stop_capture = Signal()
    settings_changed = Signal(dict)
    scan_controllers_requested = Signal()
    # Backward-compatible signal expected by integration tests
    controller_enabled = Signal(str, bool)

    def __init__(self):
        super().__init__()
        self.is_capturing = False
        self.controller_cards: List[EnhancedControllerCard] = []
        self._setup_ui()
        self._setup_style()
        
        # Connect to theme changes
        theme_manager.theme_changed.connect(self._setup_style)
        
        # Setup auto-scan timer
        self._auto_scan_timer = QTimer()
        self._auto_scan_timer.setSingleShot(True)
        self._auto_scan_timer.timeout.connect(self._perform_auto_scan)

    def showEvent(self, event):
        """Handle window show event and trigger auto-scan."""
        super().showEvent(event)
        # Trigger auto-scan after a short delay to ensure window is fully loaded
        self._auto_scan_timer.start(500)  # 500ms delay
        
    def _perform_auto_scan(self):
        """Perform automatic controller scan when window opens only if no controllers are detected."""
        # Only auto-scan if no controllers are currently detected
        if len(self.controller_cards) == 0:
            self._scan_controllers()

    def _setup_ui(self):
        """Setup the sender window UI."""
        self.setWindowTitle("Input Link - Sender")
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

        self.scan_btn = AnimatedButton("Scan Controllers", "secondary")
        self.scan_btn.clicked.connect(self._scan_controllers)

        self.controller_count_label = QLabel("0 controllers detected")
        self.controller_count_label.setStyleSheet("color: #8E8E93; font-size: 11px;")

        detection_layout.addWidget(self.scan_btn)
        detection_layout.addStretch()
        detection_layout.addWidget(self.controller_count_label)

        # Controller list area with modern scroll
        self.controller_scroll_area = ModernCardScrollArea()
        self.controller_scroll_area.set_max_height(240)  # Optimized for 56px card height
        
        # Set empty message for when no controllers are detected
        self.controller_scroll_area.set_empty_message(
            "No controllers detected\nConnect a controller and click 'Scan Controllers'"
        )
        self.controller_scroll_area.show_empty_message(True)
        # Backward-compatible alias for tests
        # Expose the internal empty label as `no_controllers_label`
        if hasattr(self.controller_scroll_area, '_empty_label'):
            self.no_controllers_label = self.controller_scroll_area._empty_label
        else:
            # Ensure the attribute exists; will be populated after first set_empty_message
            self.no_controllers_label = QLabel("")

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
        self.host_combo.currentTextChanged.connect(self._emit_settings)

        # Receiver port
        port_label = QLabel("Port:")
        port_label.setStyleSheet("color: #1D1D1F; font-size: 12px; font-weight: 600;")

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1000, 65535)
        self.port_spin.setValue(8765)
        self.port_spin.setStyleSheet(self._get_input_style())
        self.port_spin.valueChanged.connect(lambda _: self._emit_settings())

        # Polling rate
        rate_label = QLabel("Polling Rate (Hz):")
        rate_label.setStyleSheet("color: #1D1D1F; font-size: 12px; font-weight: 600;")

        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(30, 120)
        self.rate_spin.setValue(60)
        self.rate_spin.setStyleSheet(self._get_input_style())
        self.rate_spin.valueChanged.connect(lambda _: self._emit_settings())

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

        self.start_btn = AnimatedButton("Start Capturing", "primary")
        self.start_btn.clicked.connect(self._toggle_capture)

        self.back_btn = AnimatedButton("Back to Main", "secondary")

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.back_btn)

        layout.addLayout(button_layout)

    def _scan_controllers(self):
        """Handle controller scanning."""
        print(f"\n=== SenderWindow._scan_controllers() DEBUG ===")
        print("User clicked scan button")

        # Emit signal to trigger controller scan
        print("About to emit scan_controllers_requested signal")
        self.scan_controllers_requested.emit()
        print("scan_controllers_requested signal emitted")

        # Update button state to show scanning
        self.scan_btn.setText("Scanning...")
        self.scan_btn.setEnabled(False)
        print("Scan button updated to 'Scanning...' state")
        print(f"=== _scan_controllers() DEBUG END ===\n")
        
        # Re-enable button after a short delay (will be properly handled by the app)
        QTimer.singleShot(1500, self._reset_scan_button)
    
    def _reset_scan_button(self):
        """Reset scan button to normal state."""
        self.scan_btn.setText("Scan Controllers") 
        self.scan_btn.setEnabled(True)

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

    def _sort_controllers_for_display(self, controllers: List[DetectedController]) -> List[DetectedController]:
        """Sort controllers in optimal display order."""
        def controller_priority(controller):
            """Calculate priority score for controller display order."""
            score = 0
            
            # Priority 1: Already assigned/enabled controllers first
            if getattr(controller, 'assigned_number', None):
                score += 1000
            
            # Priority 2: Xbox controllers (typically most compatible)
            name_lower = controller.name.lower()
            if 'xbox' in name_lower or 'xinput' in name_lower:
                score += 500
                
            # Priority 3: PlayStation controllers
            elif 'playstation' in name_lower or 'dualshock' in name_lower or 'dualsense' in name_lower:
                score += 400
                
            # Priority 4: Generic/DirectInput controllers
            elif 'controller' in name_lower or 'gamepad' in name_lower:
                score += 300
                
            # Priority 5: Other input devices (keyboards, mice, etc.)
            else:
                score += 100
            
            # Sub-priority: Prefer lower device IDs (typically connected first)
            score += (1000 - controller.device_id) if controller.device_id < 1000 else 0
            
            # Sub-priority: Prefer XINPUT over DirectInput
            input_method = getattr(controller, 'preferred_input_method', 'XINPUT')
            if input_method == 'XINPUT' or (hasattr(input_method, 'value') and input_method.value == 'XINPUT'):
                score += 50
            
            return score
        
        # Sort by priority score (highest first)
        return sorted(controllers, key=controller_priority, reverse=True)

    def update_controllers(self, controllers: List[DetectedController]):
        """Update the controller list with optimized display order."""
        print(f"\n=== SenderWindow.update_controllers() DEBUG ===")
        print(f"Received {len(controllers)} controllers")
        for i, controller in enumerate(controllers):
            print(f"  [{i}] {controller.name} - {controller.state} - {controller.identifier}")

        # Reset scan button state
        self.scan_btn.setText("Scan Controllers")
        self.scan_btn.setEnabled(True)
        print(f"Scan button reset: '{self.scan_btn.text()}' - Enabled: {self.scan_btn.isEnabled()}")

        # Clear existing cards
        print(f"Before clear - Cards: {len(self.controller_cards)}")
        self.controller_scroll_area.clear_cards()
        self.controller_cards.clear()
        print(f"After clear - Cards: {len(self.controller_cards)}")

        if not controllers:
            self.controller_scroll_area.show_empty_message(True)
            self.controller_count_label.setText("0 controllers detected")
            print("No controllers - showing empty message")
            return

        # Hide empty message
        self.controller_scroll_area.show_empty_message(False)
        print("Controllers found - hiding empty message")

        # Sort controllers for optimal display order
        sorted_controllers = self._sort_controllers_for_display(controllers)
        print(f"Sorted controllers: {len(sorted_controllers)}")

        # Add new controller cards in optimal order
        for i, controller in enumerate(sorted_controllers):
            print(f"Creating card for controller [{i}]: {controller.name}")
            card = EnhancedControllerCard(controller)
            card.controller_number_changed.connect(self._on_controller_number_changed)
            self.controller_cards.append(card)
            self.controller_scroll_area.add_card(card)
            print(f"Card created and added - Total cards: {len(self.controller_cards)}")

        # Update count
        count = len(controllers)
        self.controller_count_label.setText(f"{count} controller{'s' if count != 1 else ''} detected")
        print(f"Count label updated: '{self.controller_count_label.text()}'")
        print(f"=== update_controllers() END ===\n")

    def update_connection_status(self, status: str, color: str = "#8E8E93"):
        """Update connection status."""
        self.connection_card.update_status(status, color)

    def _on_controller_number_changed(self, controller_id: str, number: int):
        """Emit settings change when a controller number changes."""
        self.settings_changed.emit({
            "type": "controller_number",
            "controller_id": controller_id,
            "number": number,
        })

    def _emit_settings(self):
        """Emit current sender settings (host/port/polling)."""
        self.settings_changed.emit({
            "type": "sender_network",
            "host": self.host_combo.currentText().strip(),
            "port": int(self.port_spin.value()),
            "polling_rate": int(self.rate_spin.value()),
        })

    def _get_group_style(self) -> str:
        """Get consistent group box styling."""
        return theme_manager.get_group_style()

    def _get_input_style(self) -> str:
        """Get consistent input field styling."""
        return theme_manager.get_input_style()

    def _setup_style(self):
        """Setup window styling."""
        self.setStyleSheet(theme_manager.get_window_style())
