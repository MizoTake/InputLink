"""Theme management for Input Link GUI - supports light and dark modes."""

from __future__ import annotations

from enum import Enum
from typing import Dict

from PySide6.QtCore import QObject, QSettings, Signal


class ThemeMode(Enum):
    """Available theme modes."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"  # Follow system theme


class ThemeColors:
    """Color definitions for different themes."""

    LIGHT = {
        # Primary colors
        "primary": "#007AFF",
        "primary_hover": "#0056CC",
        "primary_pressed": "#004499",
        "primary_disabled": "#E5E5EA",

        # Secondary colors
        "secondary": "#F2F2F7",
        "secondary_border": "#D1D1D6",
        "secondary_hover": "#E5E5EA",
        "secondary_pressed": "#D1D1D6",

        # Success/Warning/Error
        "success": "#34C759",
        "warning": "#FF9F0A",
        "error": "#FF3B30",
        "error_hover": "#D70015",
        "error_pressed": "#A20000",

        # Background colors
        "window_bg": "#F2F2F7",
        "card_bg": "#FFFFFF",
        "input_bg": "#FFFFFF",
        "button_bg": "#F2F2F7",

        # Text colors
        "text_primary": "#1D1D1F",
        "text_secondary": "#8E8E93",
        "text_tertiary": "#C7C7CC",
        "text_inverse": "#FFFFFF",

        # Border colors
        "border_primary": "#E5E5EA",
        "border_secondary": "#D1D1D6",
        "border_focus": "#007AFF",

        # Gaming accent colors
        "gaming_blue": "#00D4FF",
        "gaming_purple": "#AF52DE",
        "gaming_green": "#30D158",
        "gaming_orange": "#FF9F0A",
    }

    DARK = {
        # Primary colors (slightly adjusted for dark mode)
        "primary": "#0A84FF",
        "primary_hover": "#409CFF",
        "primary_pressed": "#0056CC",
        "primary_disabled": "#3A3A3C",

        # Secondary colors
        "secondary": "#2C2C2E",
        "secondary_border": "#48484A",
        "secondary_hover": "#3A3A3C",
        "secondary_pressed": "#48484A",

        # Success/Warning/Error (brighter for dark mode)
        "success": "#30D158",
        "warning": "#FF9F0A",
        "error": "#FF453A",
        "error_hover": "#FF6961",
        "error_pressed": "#D70015",

        # Background colors
        "window_bg": "#1C1C1E",
        "card_bg": "#2C2C2E",
        "input_bg": "#3A3A3C",
        "button_bg": "#2C2C2E",

        # Text colors
        "text_primary": "#FFFFFF",
        "text_secondary": "#8E8E93",
        "text_tertiary": "#48484A",
        "text_inverse": "#000000",

        # Border colors
        "border_primary": "#48484A",
        "border_secondary": "#3A3A3C",
        "border_focus": "#0A84FF",

        # Gaming accent colors (brighter for dark mode)
        "gaming_blue": "#64D2FF",
        "gaming_purple": "#BF5AF2",
        "gaming_green": "#32D74B",
        "gaming_orange": "#FF9F0A",
    }


class ThemeManager(QObject):
    """Manages application theming and provides theme-aware colors."""

    theme_changed = Signal(str)  # Emits theme name when changed

    def __init__(self):
        super().__init__()
        self.settings = QSettings("InputLink", "Theme")
        self._current_theme: ThemeMode = ThemeMode.LIGHT
        self._colors: dict[str, str] = ThemeColors.LIGHT
        self._load_saved_theme()

    def _load_saved_theme(self):
        """Load previously saved theme from settings."""
        saved_theme = self.settings.value("theme_mode", ThemeMode.LIGHT.value)
        try:
            self._current_theme = ThemeMode(saved_theme)
        except ValueError:
            self._current_theme = ThemeMode.LIGHT
        self._update_colors()

    def _update_colors(self):
        """Update color palette based on current theme."""
        if self._current_theme == ThemeMode.DARK:
            self._colors = ThemeColors.DARK
        else:
            self._colors = ThemeColors.LIGHT

    @property
    def current_theme(self) -> ThemeMode:
        """Get current theme mode."""
        return self._current_theme

    @property
    def is_dark(self) -> bool:
        """Check if current theme is dark."""
        return self._current_theme == ThemeMode.DARK

    def set_theme(self, theme: ThemeMode):
        """Set the application theme."""
        if theme != self._current_theme:
            self._current_theme = theme
            self._update_colors()
            self.settings.setValue("theme_mode", theme.value)
            self.theme_changed.emit(theme.value)

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        if self._current_theme == ThemeMode.LIGHT:
            self.set_theme(ThemeMode.DARK)
        else:
            self.set_theme(ThemeMode.LIGHT)

    def get_color(self, color_name: str) -> str:
        """Get a color value by name for the current theme."""
        return self._colors.get(color_name, "#000000")

    def get_button_style(self, button_type: str = "primary") -> str:
        """Get themed button stylesheet."""
        if button_type == "primary":
            return f"""
                QPushButton {{
                    background-color: {self.get_color('primary')};
                    border: none;
                    border-radius: 8px;
                    color: {self.get_color('text_inverse')};
                    font-weight: 600;
                    font-size: 13px;
                    padding: 8px 16px;
                    min-width: 120px;
                }}
                QPushButton:hover {{
                    background-color: {self.get_color('primary_hover')};
                }}
                QPushButton:pressed {{
                    background-color: {self.get_color('primary_pressed')};
                }}
                QPushButton:disabled {{
                    background-color: {self.get_color('primary_disabled')};
                    color: {self.get_color('text_secondary')};
                }}
            """
        if button_type == "secondary":
            return f"""
                QPushButton {{
                    background-color: {self.get_color('secondary')};
                    border: 1px solid {self.get_color('secondary_border')};
                    border-radius: 8px;
                    color: {self.get_color('primary')};
                    font-weight: 600;
                    font-size: 13px;
                    padding: 8px 16px;
                    min-width: 120px;
                }}
                QPushButton:hover {{
                    background-color: {self.get_color('secondary_hover')};
                }}
                QPushButton:pressed {{
                    background-color: {self.get_color('secondary_pressed')};
                }}
            """
        # destructive
        return f"""
                QPushButton {{
                    background-color: {self.get_color('error')};
                    border: none;
                    border-radius: 8px;
                    color: {self.get_color('text_inverse')};
                    font-weight: 600;
                    font-size: 13px;
                    padding: 8px 16px;
                    min-width: 120px;
                }}
                QPushButton:hover {{
                    background-color: {self.get_color('error_hover')};
                }}
                QPushButton:pressed {{
                    background-color: {self.get_color('error_pressed')};
                }}
            """

    def get_card_style(self) -> str:
        """Get themed card stylesheet."""
        return f"""
            QFrame {{
                background-color: {self.get_color('card_bg')};
                border-radius: 12px;
                border: 1px solid {self.get_color('border_primary')};
            }}
            QFrame:hover {{
                border-color: {self.get_color('border_secondary')};
            }}
        """

    def get_group_style(self) -> str:
        """Get themed group box stylesheet."""
        return f"""
            QGroupBox {{
                font-size: 13px;
                font-weight: 600;
                color: {self.get_color('text_primary')};
                border: 1px solid {self.get_color('border_primary')};
                border-radius: 12px;
                margin: 8px 0;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: {self.get_color('window_bg')};
            }}
        """

    def get_input_style(self) -> str:
        """Get themed input field stylesheet."""
        return f"""
            QComboBox, QSpinBox {{
                background-color: {self.get_color('input_bg')};
                border: 1px solid {self.get_color('border_secondary')};
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 12px;
                color: {self.get_color('text_primary')};
                min-height: 20px;
            }}
            QComboBox:focus, QSpinBox:focus {{
                border-color: {self.get_color('border_focus')};
                outline: none;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {self.get_color('text_secondary')};
                margin-right: 8px;
            }}
        """

    def get_window_style(self) -> str:
        """Get themed main window stylesheet."""
        return f"""
            QMainWindow {{
                background-color: {self.get_color('window_bg')};
            }}
            QWidget {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                color: {self.get_color('text_primary')};
            }}
            QTextEdit {{
                background-color: {self.get_color('input_bg')};
                border: 1px solid {self.get_color('border_secondary')};
                border-radius: 8px;
                padding: 8px;
                font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
                font-size: 10px;
                color: {self.get_color('text_primary')};
            }}
        """

    def get_checkbox_style(self) -> str:
        """Get themed checkbox stylesheet."""
        return f"""
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid {self.get_color('border_secondary')};
                background-color: {self.get_color('input_bg')};
            }}
            QCheckBox::indicator:checked {{
                border-color: {self.get_color('primary')};
                background-color: {self.get_color('primary')};
            }}
        """


# Global theme manager instance
theme_manager = ThemeManager()

