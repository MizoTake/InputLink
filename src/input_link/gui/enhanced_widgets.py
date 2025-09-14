"""Enhanced widgets with animations and modern UI elements for Input Link."""

from __future__ import annotations

from typing import Optional, Dict, Any
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, 
    QAbstractAnimation, Signal, QRect, Property
)
from PySide6.QtGui import QFont, QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import (
    QPushButton, QFrame, QLabel, QVBoxLayout, QHBoxLayout, 
    QWidget, QProgressBar, QGraphicsOpacityEffect, QScrollArea,
    QSpinBox, QCheckBox
)

from input_link.gui.theme_manager import theme_manager


class AnimatedButton(QPushButton):
    """Enhanced button with hover animations and gaming-style effects."""
    
    def __init__(self, text: str, button_type: str = "primary"):
        super().__init__(text)
        self.button_type = button_type
        self._animation = QPropertyAnimation(self, b"geometry")
        self._opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self._opacity_effect)
        self._setup_style()
        self._setup_animations()
        
        # Connect to theme changes
        theme_manager.theme_changed.connect(self._setup_style)
    
    def _setup_style(self):
        """Setup button styling based on current theme."""
        self.setStyleSheet(theme_manager.get_button_style(self.button_type))
    
    def _setup_animations(self):
        """Setup button animations."""
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def enterEvent(self, event):
        """Handle mouse enter with animation."""
        super().enterEvent(event)
        self._animate_scale(1.02)
    
    def leaveEvent(self, event):
        """Handle mouse leave with animation."""
        super().leaveEvent(event)
        self._animate_scale(1.0)
    
    def _animate_scale(self, scale: float):
        """Animate button scale."""
        current_geometry = self.geometry()
        center = current_geometry.center()
        
        new_width = int(current_geometry.width() * scale)
        new_height = int(current_geometry.height() * scale)
        
        new_geometry = QRect(
            center.x() - new_width // 2,
            center.y() - new_height // 2,
            new_width,
            new_height
        )
        
        self._animation.setStartValue(current_geometry)
        self._animation.setEndValue(new_geometry)
        self._animation.start()


class ConnectionStatusIndicator(QWidget):
    """Animated connection status indicator with pulse effects."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.connection_status = "disconnected"
        self.signal_strength = 0  # 0-100
        self.latency = 0  # milliseconds
        self._pulse_timer = QTimer()
        self._pulse_opacity = 1.0
        self._pulse_direction = -1
        
        self.setFixedSize(24, 24)
        self._setup_pulse_animation()
    
    def _setup_pulse_animation(self):
        """Setup pulsing animation for connected status."""
        self._pulse_timer.timeout.connect(self._update_pulse)
        self._pulse_timer.setInterval(50)  # 20 FPS
    
    def _update_pulse(self):
        """Update pulse animation."""
        self._pulse_opacity += self._pulse_direction * 0.05
        if self._pulse_opacity <= 0.3:
            self._pulse_direction = 1
            self._pulse_opacity = 0.3
        elif self._pulse_opacity >= 1.0:
            self._pulse_direction = -1
            self._pulse_opacity = 1.0
        self.update()
    
    def set_connection_status(self, status: str, signal_strength: int = 0, latency: int = 0):
        """Update connection status and metrics."""
        self.connection_status = status
        self.signal_strength = max(0, min(100, signal_strength))
        self.latency = max(0, latency)
        
        # Start/stop pulse animation based on status
        if status == "connected":
            self._pulse_timer.start()
        else:
            self._pulse_timer.stop()
            self._pulse_opacity = 1.0
        
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for connection indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get colors based on status
        if self.connection_status == "connected":
            color = QColor(theme_manager.get_color("success"))
        elif self.connection_status == "connecting":
            color = QColor(theme_manager.get_color("warning"))
        else:
            color = QColor(theme_manager.get_color("text_secondary"))
        
        # Apply pulse opacity for connected status
        if self.connection_status == "connected":
            color.setAlphaF(self._pulse_opacity)
        
        # Draw main circle
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(120), 1))
        painter.drawEllipse(2, 2, 20, 20)
        
        # Draw signal strength indicators for connected status
        if self.connection_status == "connected" and self.signal_strength > 0:
            bar_color = QColor(theme_manager.get_color("gaming_blue"))
            bar_color.setAlphaF(0.8)
            painter.setBrush(QBrush(bar_color))
            painter.setPen(QPen(bar_color, 1))
            
            # Draw 3 signal bars
            bar_count = max(1, int(self.signal_strength / 33.33))  # 0-3 bars
            for i in range(3):
                if i < bar_count:
                    painter.drawRect(8 + i * 3, 16 - i * 2, 2, 4 + i * 2)


class NetworkQualityWidget(QFrame):
    """Widget showing network quality metrics with visual indicators."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._setup_style()
        
        # Connect to theme changes
        theme_manager.theme_changed.connect(self._setup_style)
    
    def _setup_ui(self):
        """Setup the network quality UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(12)
        
        # Connection indicator
        self.connection_indicator = ConnectionStatusIndicator()
        
        # Metrics layout
        metrics_layout = QVBoxLayout()
        metrics_layout.setSpacing(2)
        
        # Latency
        self.latency_label = QLabel("Latency: --ms")
        self.latency_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')}; font-size: 10px;")
        
        # Quality
        self.quality_label = QLabel("Quality: Unknown")
        self.quality_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')}; font-size: 10px;")
        
        metrics_layout.addWidget(self.latency_label)
        metrics_layout.addWidget(self.quality_label)
        
        layout.addWidget(self.connection_indicator)
        layout.addLayout(metrics_layout)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def _setup_style(self):
        """Setup widget styling."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {theme_manager.get_color('card_bg')};
                border: 1px solid {theme_manager.get_color('border_primary')};
                border-radius: 8px;
            }}
        """)
        self.setMaximumHeight(42)  # Reduced from 50 to 42
        
        # Update label colors
        self.latency_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')}; font-size: 10px;")
        self.quality_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')}; font-size: 10px;")
    
    def update_metrics(self, status: str, latency: int = 0, signal_strength: int = 0, packet_loss: float = 0.0):
        """Update network quality metrics."""
        # Update connection status
        self.connection_indicator.set_connection_status(status, signal_strength, latency)
        
        # Update latency display
        if status == "connected":
            self.latency_label.setText(f"Latency: {latency}ms")
            
            # Determine quality based on latency and packet loss
            if latency < 30 and packet_loss < 1.0:
                quality = "Excellent"
                quality_color = theme_manager.get_color("success")
            elif latency < 60 and packet_loss < 3.0:
                quality = "Good" 
                quality_color = theme_manager.get_color("gaming_green")
            elif latency < 100 and packet_loss < 5.0:
                quality = "Fair"
                quality_color = theme_manager.get_color("warning")
            else:
                quality = "Poor"
                quality_color = theme_manager.get_color("error")
            
            self.quality_label.setText(f"Quality: {quality}")
            self.quality_label.setStyleSheet(f"color: {quality_color}; font-size: 10px; font-weight: 600;")
        else:
            self.latency_label.setText("Latency: --ms")
            self.quality_label.setText("Quality: Unknown")
            self.quality_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')}; font-size: 10px;")


class ControllerVisualization(QFrame):
    """Visual representation of controller state with real-time input feedback."""
    
    def __init__(self, controller_name: str = "Controller"):
        super().__init__()
        self.controller_name = controller_name
        self.button_states: Dict[str, bool] = {}
        self.axis_values: Dict[str, float] = {}
        
        self._setup_ui()
        self._setup_style()
        
        # Connect to theme changes
        theme_manager.theme_changed.connect(self._setup_style)
    
    def _setup_ui(self):
        """Setup controller visualization UI."""
        self.setMinimumSize(200, 120)
        self.setMaximumSize(400, 160)
    
    def _setup_style(self):
        """Setup styling."""
        self.setStyleSheet(theme_manager.get_card_style())
    
    def update_input_state(self, button_states: Dict[str, bool], axis_values: Dict[str, float]):
        """Update controller input state for visualization."""
        self.button_states = button_states.copy()
        self.axis_values = axis_values.copy()
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for controller visualization."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fill background
        rect = self.rect()
        painter.fillRect(rect, QColor(theme_manager.get_color("card_bg")))
        
        # If no controller data, show placeholder
        if not self.button_states and not self.axis_values:
            painter.setPen(QPen(QColor(theme_manager.get_color("text_secondary")), 1))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, 
                           f"🎮\n{self.controller_name}\nNo input data")
            return
        
        # Calculate scaling based on widget size
        scale_x = rect.width() / 200.0
        scale_y = rect.height() / 120.0
        scale = min(scale_x, scale_y, 1.5)  # Limit maximum scale
        
        # Center the controller drawing
        offset_x = (rect.width() - int(180 * scale)) // 2
        offset_y = (rect.height() - int(80 * scale)) // 2
        
        # Draw controller outline
        painter.setPen(QPen(QColor(theme_manager.get_color("border_secondary")), int(2 * scale)))
        painter.setBrush(QBrush(QColor(theme_manager.get_color("input_bg"))))
        
        # Draw basic controller shape (simplified Xbox-style)
        controller_rect = QRect(
            offset_x + int(10 * scale), 
            offset_y + int(20 * scale), 
            int(160 * scale), 
            int(60 * scale)
        )
        painter.drawRoundedRect(controller_rect, int(15 * scale), int(15 * scale))
        
        # Draw D-pad
        dpad_color = QColor(theme_manager.get_color("gaming_blue"))
        if self.button_states.get("dpad_up", False) or self.button_states.get("dpad_down", False) or \
           self.button_states.get("dpad_left", False) or self.button_states.get("dpad_right", False):
            dpad_color = QColor(theme_manager.get_color("success"))
        
        painter.setBrush(QBrush(dpad_color))
        # D-pad vertical bar
        painter.drawRect(
            offset_x + int(30 * scale), 
            offset_y + int(35 * scale), 
            int(15 * scale), 
            int(25 * scale)
        )
        # D-pad horizontal bar  
        painter.drawRect(
            offset_x + int(25 * scale), 
            offset_y + int(40 * scale), 
            int(25 * scale), 
            int(15 * scale)
        )
        
        # Draw face buttons (A, B, X, Y)
        button_positions = [
            (offset_x + int(130 * scale), offset_y + int(30 * scale)),  # Y
            (offset_x + int(145 * scale), offset_y + int(45 * scale)),  # B  
            (offset_x + int(115 * scale), offset_y + int(45 * scale)),  # X
            (offset_x + int(130 * scale), offset_y + int(60 * scale)),  # A
        ]
        button_names = ["Y", "B", "X", "A"]
        
        for i, (x, y) in enumerate(button_positions):
            button_name = button_names[i].lower()
            if self.button_states.get(button_name, False):
                painter.setBrush(QBrush(QColor(theme_manager.get_color("success"))))
            else:
                painter.setBrush(QBrush(QColor(theme_manager.get_color("text_tertiary"))))
            
            painter.drawEllipse(x, y, int(12 * scale), int(12 * scale))
        
        # Draw analog sticks
        left_stick_base = (offset_x + int(60 * scale), offset_y + int(45 * scale))
        right_stick_base = (offset_x + int(100 * scale), offset_y + int(55 * scale))
        
        for stick_name, (base_x, base_y) in [("left", left_stick_base), ("right", right_stick_base)]:
            # Stick base
            painter.setBrush(QBrush(QColor(theme_manager.get_color("text_tertiary"))))
            painter.drawEllipse(
                base_x - int(8 * scale), 
                base_y - int(8 * scale), 
                int(16 * scale), 
                int(16 * scale)
            )
            
            # Stick position based on axis values
            x_axis = self.axis_values.get(f"{stick_name}_x", 0.0)
            y_axis = self.axis_values.get(f"{stick_name}_y", 0.0)
            
            stick_x = base_x + int(x_axis * 5 * scale)  # Scale movement
            stick_y = base_y + int(y_axis * 5 * scale)
            
            # Active stick color
            if abs(x_axis) > 0.1 or abs(y_axis) > 0.1:
                stick_color = QColor(theme_manager.get_color("gaming_orange"))
            else:
                stick_color = QColor(theme_manager.get_color("border_secondary"))
            
            painter.setBrush(QBrush(stick_color))
            painter.drawEllipse(
                stick_x - int(4 * scale), 
                stick_y - int(4 * scale), 
                int(8 * scale), 
                int(8 * scale)
            )


class ThemeToggleButton(QPushButton):
    """Button for toggling between light and dark themes."""
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(40, 24)
        self.setCheckable(True)
        self.setChecked(theme_manager.is_dark)
        self.clicked.connect(self._toggle_theme)
        self._setup_style()
        
        # Connect to theme changes
        theme_manager.theme_changed.connect(self._on_theme_changed)
    
    def _setup_style(self):
        """Setup toggle button styling."""
        if theme_manager.is_dark:
            # Dark mode - show moon icon
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme_manager.get_color('primary')};
                    border: none;
                    border-radius: 12px;
                    color: {theme_manager.get_color('text_inverse')};
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: {theme_manager.get_color('primary_hover')};
                }}
            """)
            self.setText("🌙")
        else:
            # Light mode - show sun icon  
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme_manager.get_color('secondary')};
                    border: 1px solid {theme_manager.get_color('border_secondary')};
                    border-radius: 12px;
                    color: {theme_manager.get_color('text_primary')};
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: {theme_manager.get_color('secondary_hover')};
                }}
            """)
            self.setText("☀️")
    
    def _toggle_theme(self):
        """Toggle the application theme."""
        theme_manager.toggle_theme()
    
    def _on_theme_changed(self, theme_name: str):
        """Handle theme change."""
        self.setChecked(theme_manager.is_dark)
        self._setup_style()


class EnhancedStatusCard(QFrame):
    """Enhanced status card with animations and better visual hierarchy."""
    
    def __init__(self, title: str, status: str = "Unknown"):
        super().__init__()
        self.title = title
        self.status = status
        self._setup_ui()
        self._setup_style()
        
        # Connect to theme changes
        theme_manager.theme_changed.connect(self._setup_style)
    
    def _setup_ui(self):
        """Setup the enhanced card UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        
        # Header layout with title and indicator
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_label.setFont(title_font)
        
        # Status indicator dot
        self.status_dot = QFrame()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setStyleSheet(f"""
            QFrame {{
                background-color: {theme_manager.get_color('text_secondary')};
                border-radius: 4px;
            }}
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_dot)
        
        # Status text
        self.status_label = QLabel(self.status)
        status_font = QFont()
        status_font.setPointSize(11)
        self.status_label.setFont(status_font)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.status_label)
        self.setLayout(layout)
    
    def _setup_style(self):
        """Setup enhanced card styling."""
        self.setStyleSheet(theme_manager.get_card_style())
        self.setFixedHeight(72)  # Reduced from 85 to 72
        
        # Update text colors
        title_label = self.layout().itemAt(0).layout().itemAt(0).widget()
        title_label.setStyleSheet(f"color: {theme_manager.get_color('text_primary')};")
        self.status_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')};")
    
    def update_status(self, status: str, status_type: str = "info"):
        """Update status with type-based coloring."""
        self.status = status
        self.status_label.setText(status)
        
        # Update colors based on status type
        if status_type == "success":
            color = theme_manager.get_color("success")
        elif status_type == "warning":
            color = theme_manager.get_color("warning")
        elif status_type == "error":
            color = theme_manager.get_color("error")
        elif status_type == "info":
            color = theme_manager.get_color("primary")
        else:
            color = theme_manager.get_color("text_secondary")
        
        self.status_label.setStyleSheet(f"color: {color}; font-weight: 600;")
        self.status_dot.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)


class EnhancedScrollArea(QScrollArea):
    """Improved scroll area with smooth scrolling and modern styling."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_scroll_area()
        self._setup_style()
        
        # Connect to theme changes
        theme_manager.theme_changed.connect(self._setup_style)
    
    def _setup_scroll_area(self):
        """Setup scroll area properties."""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.Shape.NoFrame)
        
        # Enable smooth scrolling
        self.verticalScrollBar().setSingleStep(20)
        self.verticalScrollBar().setPageStep(100)
    
    def _setup_style(self):
        """Setup modern scroll area styling."""
        self.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background: {theme_manager.get_color('window_bg')};
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {theme_manager.get_color('text_tertiary')};
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {theme_manager.get_color('text_secondary')};
            }}
            QScrollBar::handle:vertical:pressed {{
                background: {theme_manager.get_color('primary')};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
    
    def set_max_height(self, height: int):
        """Set maximum height with smooth transition."""
        self.setMaximumHeight(height)
    
    def wheelEvent(self, event):
        """Enhanced wheel scrolling with smooth animation."""
        # Smooth scroll animation
        scroll_bar = self.verticalScrollBar()
        current_value = scroll_bar.value()
        
        # Calculate scroll delta
        delta = -event.angleDelta().y() // 3  # Reduce scroll speed for smoothness
        new_value = max(scroll_bar.minimum(), min(scroll_bar.maximum(), current_value + delta))
        
        # Animate scroll
        self._smooth_scroll(current_value, new_value)
        event.accept()
    
    def _smooth_scroll(self, start_value: int, end_value: int):
        """Animate smooth scrolling."""
        if not hasattr(self, '_scroll_animation'):
            self._scroll_animation = QPropertyAnimation(self.verticalScrollBar(), b"value")
            self._scroll_animation.setDuration(150)
            self._scroll_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self._scroll_animation.setStartValue(start_value)
        self._scroll_animation.setEndValue(end_value)
        self._scroll_animation.start()


class ModernCardScrollArea(EnhancedScrollArea):
    """Specialized scroll area for card-based layouts."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards_widget = QWidget()
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(4)  # Reduced spacing for compact cards
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add stretch to push cards to top
        self.cards_layout.addStretch()
        
        self.cards_widget.setLayout(self.cards_layout)
        self.setWidget(self.cards_widget)
    
    def add_card(self, card_widget: QWidget):
        """Add a card to the scroll area with smart positioning."""
        # Insert before stretch
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card_widget)
        
        # Auto-scroll to show new card if it's at the top (high priority)
        if self.cards_layout.count() <= 3:  # First few cards
            QTimer.singleShot(100, lambda: self.ensureWidgetVisible(card_widget))
    
    def remove_card(self, card_widget: QWidget):
        """Remove a card from the scroll area."""
        self.cards_layout.removeWidget(card_widget)
        card_widget.deleteLater()
    
    def clear_cards(self):
        """Remove all cards with smooth animation."""
        while self.cards_layout.count() > 1:  # Keep stretch item
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def set_empty_message(self, message: str):
        """Set a message to display when no cards are present."""
        if not hasattr(self, '_empty_label'):
            self._empty_label = QLabel()
            self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._empty_label.setStyleSheet(f"""
                QLabel {{
                    color: {theme_manager.get_color('text_secondary')};
                    font-size: 12px;
                    padding: 20px;
                    border: 2px dashed {theme_manager.get_color('border_secondary')};
                    border-radius: 8px;
                    background-color: {theme_manager.get_color('window_bg')};
                    margin: 10px;
                }}
            """)
        
        self._empty_label.setText(message)
    
    def show_empty_message(self, show: bool = True):
        """Show or hide the empty message."""
        if hasattr(self, '_empty_label'):
            if show and self.cards_layout.count() <= 1:  # Only stretch item
                self.cards_layout.insertWidget(0, self._empty_label)
            elif not show:
                self.cards_layout.removeWidget(self._empty_label)
                self._empty_label.setParent(None)


class EnhancedControllerCard(QFrame):
    """Enhanced controller card with clean vertical layout design."""
    
    controller_number_changed = Signal(str, int)  # controller_id, player number
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._setup_ui()
        self._setup_style()
        
        # Connect to theme changes
        theme_manager.theme_changed.connect(self._setup_style)
    
    def _setup_ui(self):
        """Setup Windows-standard controller card UI with horizontal layout."""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(16, 8, 16, 8)  # Windows-standard margins
        main_layout.setSpacing(12)  # Standard spacing
        
        # Left section: Controller info (horizontal layout)
        left_section = QHBoxLayout()
        left_section.setSpacing(8)
        
        # Controller icon (non-interactive, smaller)
        self.controller_icon = QLabel("🎮")
        self.controller_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.controller_icon.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                color: {theme_manager.get_color('gaming_blue')};
                min-width: 18px;
                max-width: 18px;
            }}
        """)
        
        # Controller info container
        info_container = QVBoxLayout()
        info_container.setSpacing(2)
        
        # Controller name (non-interactive, smaller)
        name_label = QLabel(self.controller.name)
        name_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        name_font = QFont()
        name_font.setPointSize(11)
        name_font.setWeight(QFont.Weight.DemiBold)
        name_label.setFont(name_font)
        name_label.setStyleSheet(f"color: {theme_manager.get_color('text_primary')};")
        
        # Input method badge (smaller, inline)
        input_method = getattr(self.controller, 'preferred_input_method', 'XINPUT')
        method_display = input_method.value if hasattr(input_method, 'value') else input_method
        
        method_label = QLabel(method_display)
        method_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        method_label.setStyleSheet(f"""
            QLabel {{
                color: {theme_manager.get_color('text_secondary')};
                font-size: 9px;
                background-color: {theme_manager.get_color('secondary')};
                border-radius: 4px;
                padding: 1px 4px;
                font-weight: 500;
            }}
        """)
        
        info_container.addWidget(name_label)
        info_container.addWidget(method_label)
        
        left_section.addWidget(self.controller_icon)
        left_section.addLayout(info_container)
        left_section.addStretch()  # Push everything to the left
        
        # Right section: Player number controls (Windows-standard horizontal layout)
        right_section = QHBoxLayout()
        right_section.setSpacing(4)
        right_section.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Player label (compact)
        player_label = QLabel("Player:")
        player_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        player_label.setStyleSheet(f"""
            QLabel {{
                color: {theme_manager.get_color('text_secondary')};
                font-size: 10px;
                font-weight: 500;
            }}
        """)
        
        # Decrease button
        player_num = getattr(self.controller, 'assigned_number', 1) or 1
        self.decrease_button = QPushButton("−")
        self.decrease_button.setFixedSize(24, 24)
        
        # Player number display (compact)
        self.player_display = QLabel(str(player_num))
        self.player_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.player_display.setFixedSize(32, 24)
        self.player_display.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Increase button
        self.increase_button = QPushButton("＋")
        self.increase_button.setFixedSize(24, 24)
        
        # Apply Windows-standard button styling
        player_colors = self._get_player_colors(player_num)
        self._update_player_controls_styling(player_colors)
        
        self.decrease_button.clicked.connect(self._decrement_player)
        self.increase_button.clicked.connect(self._increment_player)
        
        # Store current player number
        self.current_player_num = player_num
        
        right_section.addWidget(player_label)
        right_section.addWidget(self.decrease_button)
        right_section.addWidget(self.player_display)
        right_section.addWidget(self.increase_button)
        
        # Add sections to main layout
        main_layout.addLayout(left_section, 1)
        main_layout.addLayout(right_section, 0)
        
        self.setLayout(main_layout)
    
    def _get_player_colors(self, player_num: int) -> dict:
        """Get color scheme based on player number."""
        # Define color schemes for different player numbers
        color_schemes = [
            # Player 1 - Blue scheme
            {
                'bg_light': '#E3F2FD', 'bg_dark': '#BBDEFB',
                'bg_hover_light': '#F3F8FF', 'bg_hover_dark': '#E3F2FD',
                'border': '#2196F3', 'border_hover': '#1976D2',
                'text': '#0D47A1', 'button_bg': '#E3F2FD', 'button_hover': '#BBDEFB',
                'arrow': '#1976D2'
            },
            # Player 2 - Red scheme  
            {
                'bg_light': '#FFEBEE', 'bg_dark': '#FFCDD2',
                'bg_hover_light': '#FFF5F5', 'bg_hover_dark': '#FFEBEE',
                'border': '#F44336', 'border_hover': '#D32F2F',
                'text': '#B71C1C', 'button_bg': '#FFEBEE', 'button_hover': '#FFCDD2',
                'arrow': '#D32F2F'
            },
            # Player 3 - Green scheme
            {
                'bg_light': '#E8F5E8', 'bg_dark': '#C8E6C9',
                'bg_hover_light': '#F1F8F1', 'bg_hover_dark': '#E8F5E8',
                'border': '#4CAF50', 'border_hover': '#388E3C',
                'text': '#1B5E20', 'button_bg': '#E8F5E8', 'button_hover': '#C8E6C9',
                'arrow': '#388E3C'
            },
            # Player 4 - Orange scheme
            {
                'bg_light': '#FFF3E0', 'bg_dark': '#FFE0B2',
                'bg_hover_light': '#FFF8F0', 'bg_hover_dark': '#FFF3E0',
                'border': '#FF9800', 'border_hover': '#F57C00',
                'text': '#E65100', 'button_bg': '#FFF3E0', 'button_hover': '#FFE0B2',
                'arrow': '#F57C00'
            },
            # Player 5+ - Purple scheme
            {
                'bg_light': '#F3E5F5', 'bg_dark': '#E1BEE7',
                'bg_hover_light': '#FAF0FB', 'bg_hover_dark': '#F3E5F5',
                'border': '#9C27B0', 'border_hover': '#7B1FA2',
                'text': '#4A148C', 'button_bg': '#F3E5F5', 'button_hover': '#E1BEE7',
                'arrow': '#7B1FA2'
            }
        ]
        
        # Select color scheme based on player number
        scheme_index = min((player_num - 1) % len(color_schemes), len(color_schemes) - 1)
        return color_schemes[scheme_index]
    
    def _update_player_controls_styling(self, player_colors: dict):
        """Update styling for player control buttons and display."""
        # Button styling (Windows-standard)
        button_style = f"""
            QPushButton {{
                background-color: {theme_manager.get_color('window_bg')};
                border: 1px solid {player_colors['border']};
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                color: {player_colors['text']};
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {player_colors['button_hover']};
                border-color: {player_colors['border_hover']};
            }}
            QPushButton:pressed {{
                background-color: {player_colors['bg_dark']};
                border-color: {player_colors['border_hover']};
            }}
        """
        
        # Display styling (compact)
        display_style = f"""
            QLabel {{
                background-color: {player_colors['bg_light']};
                border: 1px solid {player_colors['border']};
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                color: {player_colors['text']};
            }}
        """
        
        self.decrease_button.setStyleSheet(button_style)
        self.increase_button.setStyleSheet(button_style)
        self.player_display.setStyleSheet(display_style)
    
    def _setup_style(self):
        """Setup Windows-standard card styling."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {theme_manager.get_color('card_bg')};
                border-radius: 8px;
                border: 1px solid {theme_manager.get_color('border_secondary')};
            }}
            QFrame:hover {{
                background-color: {theme_manager.get_color('window_bg')};
                border-color: {theme_manager.get_color('border_primary')};
            }}
        """)
        self.setFixedHeight(56)  # Windows-standard list item height
        
        # Update icon color to match new size
        self.controller_icon.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                color: {theme_manager.get_color('gaming_blue')};
                min-width: 18px;
                max-width: 18px;
            }}
        """)
    
    
    def _increment_player(self):
        """Increment player number."""
        new_value = min(self.current_player_num + 1, 128)
        self._update_player_number(new_value)
    
    def _decrement_player(self):
        """Decrement player number.""" 
        new_value = max(self.current_player_num - 1, 1)
        self._update_player_number(new_value)
    
    def _update_player_number(self, value: int):
        """Update player number and UI with Windows-standard styling."""
        self.current_player_num = value
        self.player_display.setText(str(value))
        
        # Update colors based on new player number
        player_colors = self._get_player_colors(value)
        self._update_player_controls_styling(player_colors)
        
        # Emit signal
        controller_id = getattr(self.controller, 'identifier', f'{self.controller.guid}_{self.controller.device_id}')
        self.controller_number_changed.emit(controller_id, value)


class EnhancedVirtualControllerCard(QFrame):
    """Enhanced virtual controller card with better visual design."""
    
    def __init__(self, controller_number: int):
        super().__init__()
        self.controller_number = controller_number
        self.is_connected = False
        self.client_info = None
        self._setup_ui()
        self._setup_style()
        
        # Connect to theme changes
        theme_manager.theme_changed.connect(self._setup_style)
    
    def _setup_ui(self):
        """Setup enhanced virtual controller card UI with optimized sizing."""
        layout = QVBoxLayout()
        layout.setContentsMargins(14, 10, 14, 10)  # More compact margins
        layout.setSpacing(4)  # Tighter spacing
        
        # Header layout
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Virtual controller icon - smaller
        self.controller_icon = QLabel("🖥️")
        self.controller_icon.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                color: {theme_manager.get_color('gaming_purple')};
                min-width: 18px;
                max-width: 18px;
            }}
        """)
        
        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)  # Tighter spacing
        
        # Title - more compact
        title_label = QLabel("Virtual Controller")
        title_font = QFont()
        title_font.setPointSize(11)  # Slightly smaller
        title_font.setWeight(QFont.Weight.DemiBold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {theme_manager.get_color('text_primary')};")
        
        # Details layout with all info in one line
        details_layout = QHBoxLayout()
        details_layout.setSpacing(6)
        
        # Number badge - more compact
        self.number_badge = QLabel(f"#{self.controller_number}")
        self.number_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {theme_manager.get_color('gaming_purple')};
                color: {theme_manager.get_color('text_inverse')};
                border-radius: 6px;
                padding: 1px 6px;
                font-size: 9px;
                font-weight: bold;
                min-width: 16px;
            }}
        """)
        
        # Status with icon - inline
        self.status_icon = QLabel("○")
        self.status_icon.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')}; font-size: 9px;")
        
        self.status_label = QLabel("Waiting...")
        self.status_label.setStyleSheet(f"""
            color: {theme_manager.get_color('text_secondary')};
            font-size: 10px;
        """)
        
        details_layout.addWidget(self.number_badge)
        details_layout.addWidget(self.status_icon)
        details_layout.addWidget(self.status_label)
        details_layout.addStretch()
        
        info_layout.addWidget(title_label)
        info_layout.addLayout(details_layout)
        
        # Connection indicator - simple dot
        self.connection_indicator = QLabel("●")
        self.connection_indicator.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')}; font-size: 12px;")
        
        header_layout.addWidget(self.controller_icon)
        header_layout.addLayout(info_layout, 1)
        header_layout.addWidget(self.connection_indicator)
        
        # Client info (hidden by default)
        self.client_info_label = QLabel()
        self.client_info_label.setStyleSheet(f"""
            color: {theme_manager.get_color('text_tertiary')};
            font-size: 9px;
            padding-left: 26px;
        """)
        self.client_info_label.hide()
        
        layout.addLayout(header_layout)
        layout.addWidget(self.client_info_label)
        
        self.setLayout(layout)
    
    def _setup_style(self):
        """Setup enhanced card styling."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {theme_manager.get_color('card_bg')};
                border-radius: 12px;
                border: 1px solid {theme_manager.get_color('border_primary')};
            }}
            QFrame:hover {{
                border-color: {theme_manager.get_color('gaming_purple')};
                box-shadow: 0px 2px 8px rgba(175, 82, 222, 0.1);
            }}
        """)
        self.setFixedHeight(58)  # More compact height
        
        # Update icon color
        self.controller_icon.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                color: {theme_manager.get_color('gaming_purple')};
                min-width: 18px;
                max-width: 18px;
            }}
        """)
    
    def update_connection(self, connected: bool, client_info: str = None):
        """Update connection status with enhanced visuals."""
        self.is_connected = connected
        self.client_info = client_info
        
        # Update connection indicator
        self.connection_indicator.set_connection_status(
            "connected" if connected else "disconnected",
            signal_strength=100 if connected else 0
        )
        
        if connected:
            self.status_icon.setText("●")
            self.status_icon.setStyleSheet(f"color: {theme_manager.get_color('success')}; font-size: 10px;")
            self.status_label.setText("Connected & Active")
            self.status_label.setStyleSheet(f"color: {theme_manager.get_color('success')}; font-size: 11px; font-weight: 600;")
            
            # Update icon to show active state
            self.controller_icon.setStyleSheet(f"""
                QLabel {{
                    font-size: 18px;
                    color: {theme_manager.get_color('success')};
                    min-width: 24px;
                    max-width: 24px;
                }}
            """)
            
            if client_info:
                self.client_info_label.setText(f"📡 From: {client_info}")
                self.client_info_label.show()
                self.setFixedHeight(95)
        else:
            self.status_icon.setText("○")
            self.status_icon.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')}; font-size: 10px;")
            self.status_label.setText("Waiting for connection...")
            self.status_label.setStyleSheet(f"color: {theme_manager.get_color('text_secondary')}; font-size: 11px;")
            
            # Reset icon color
            self.controller_icon.setStyleSheet(f"""
                QLabel {{
                    font-size: 18px;
                    color: {theme_manager.get_color('gaming_purple')};
                    min-width: 24px;
                    max-width: 24px;
                }}
            """)
            
            self.client_info_label.hide()
            self.setFixedHeight(75)