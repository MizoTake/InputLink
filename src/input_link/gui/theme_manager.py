"""Simplified theme management for Input Link GUI - Light mode only."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class ThemeColors:
    """Color definitions for light theme."""

    # Primary colors
    PRIMARY = "#007AFF"
    PRIMARY_HOVER = "#0056CC"
    PRIMARY_PRESSED = "#004499"
    PRIMARY_DISABLED = "#E5E5EA"

    # Secondary colors
    SECONDARY = "#F2F2F7"
    SECONDARY_BORDER = "#D1D1D6"
    SECONDARY_HOVER = "#E5E5EA"
    SECONDARY_PRESSED = "#D1D1D6"

    # Success/Warning/Error
    SUCCESS = "#34C759"
    WARNING = "#FF9F0A"
    ERROR = "#FF3B30"
    ERROR_HOVER = "#D70015"
    ERROR_PRESSED = "#A20000"

    # Background colors
    WINDOW_BG = "#F2F2F7"
    CARD_BG = "#FFFFFF"
    INPUT_BG = "#FFFFFF"
    BUTTON_BG = "#F2F2F7"

    # Text colors
    TEXT_PRIMARY = "#1D1D1F"
    TEXT_SECONDARY = "#8E8E93"
    TEXT_TERTIARY = "#C7C7CC"
    TEXT_INVERSE = "#FFFFFF"

    # Border colors
    BORDER_PRIMARY = "#E5E5EA"
    BORDER_SECONDARY = "#D1D1D6"
    BORDER_FOCUS = "#007AFF"

    # Gaming accent colors
    GAMING_BLUE = "#00D4FF"
    GAMING_PURPLE = "#AF52DE"
    GAMING_GREEN = "#30D158"
    GAMING_ORANGE = "#FF9F0A"


class ThemeManager(QObject):
    """Simplified theme manager with light mode only."""

    theme_changed = Signal(str)  # For compatibility

    def __init__(self):
        super().__init__()

    def get_color(self, color_name: str) -> str:
        """Get a color value by name."""
        # Map old color names to constants
        color_map = {
            "primary": ThemeColors.PRIMARY,
            "primary_hover": ThemeColors.PRIMARY_HOVER,
            "primary_pressed": ThemeColors.PRIMARY_PRESSED,
            "primary_disabled": ThemeColors.PRIMARY_DISABLED,
            "secondary": ThemeColors.SECONDARY,
            "secondary_border": ThemeColors.SECONDARY_BORDER,
            "secondary_hover": ThemeColors.SECONDARY_HOVER,
            "secondary_pressed": ThemeColors.SECONDARY_PRESSED,
            "success": ThemeColors.SUCCESS,
            "warning": ThemeColors.WARNING,
            "error": ThemeColors.ERROR,
            "error_hover": ThemeColors.ERROR_HOVER,
            "error_pressed": ThemeColors.ERROR_PRESSED,
            "window_bg": ThemeColors.WINDOW_BG,
            "card_bg": ThemeColors.CARD_BG,
            "input_bg": ThemeColors.INPUT_BG,
            "button_bg": ThemeColors.BUTTON_BG,
            "text_primary": ThemeColors.TEXT_PRIMARY,
            "text_secondary": ThemeColors.TEXT_SECONDARY,
            "text_tertiary": ThemeColors.TEXT_TERTIARY,
            "text_inverse": ThemeColors.TEXT_INVERSE,
            "border_primary": ThemeColors.BORDER_PRIMARY,
            "border_secondary": ThemeColors.BORDER_SECONDARY,
            "border_focus": ThemeColors.BORDER_FOCUS,
            "gaming_blue": ThemeColors.GAMING_BLUE,
            "gaming_purple": ThemeColors.GAMING_PURPLE,
            "gaming_green": ThemeColors.GAMING_GREEN,
            "gaming_orange": ThemeColors.GAMING_ORANGE,
        }
        return color_map.get(color_name, "#000000")

    def get_button_style(self, button_type: str = "primary") -> str:
        """Get button stylesheet with DPI-aware sizing."""
        if button_type == "primary":
            return f"""
                QPushButton {{
                    background-color: {ThemeColors.PRIMARY};
                    border: none;
                    border-radius: 6px;
                    color: {ThemeColors.TEXT_INVERSE};
                    font-weight: 600;
                    font-size: 13px;
                    padding: 8px 16px;
                    min-width: 100px;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: {ThemeColors.PRIMARY_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {ThemeColors.PRIMARY_PRESSED};
                }}
                QPushButton:disabled {{
                    background-color: {ThemeColors.PRIMARY_DISABLED};
                    color: {ThemeColors.TEXT_SECONDARY};
                }}
            """
        if button_type == "secondary":
            return f"""
                QPushButton {{
                    background-color: {ThemeColors.SECONDARY};
                    border: 1px solid {ThemeColors.SECONDARY_BORDER};
                    border-radius: 6px;
                    color: {ThemeColors.PRIMARY};
                    font-weight: 600;
                    font-size: 13px;
                    padding: 8px 16px;
                    min-width: 100px;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: {ThemeColors.SECONDARY_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {ThemeColors.SECONDARY_PRESSED};
                }}
            """
        # destructive
        return f"""
                QPushButton {{
                    background-color: {ThemeColors.ERROR};
                    border: none;
                    border-radius: 6px;
                    color: {ThemeColors.TEXT_INVERSE};
                    font-weight: 600;
                    font-size: 13px;
                    padding: 8px 16px;
                    min-width: 100px;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: {ThemeColors.ERROR_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {ThemeColors.ERROR_PRESSED};
                }}
            """

    def get_card_style(self) -> str:
        """Get card stylesheet."""
        return f"""
            QFrame {{
                background-color: {ThemeColors.CARD_BG};
                border-radius: 12px;
                border: 1px solid {ThemeColors.BORDER_PRIMARY};
            }}
            QFrame:hover {{
                border-color: {ThemeColors.BORDER_SECONDARY};
            }}
        """

    def get_group_style(self) -> str:
        """Get group box stylesheet."""
        return f"""
            QGroupBox {{
                font-size: 14px;
                font-weight: 600;
                color: {ThemeColors.TEXT_PRIMARY};
                border: 1px solid {ThemeColors.BORDER_PRIMARY};
                border-radius: 12px;
                margin: 12px 0;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px 0 8px;
                background-color: {ThemeColors.WINDOW_BG};
            }}
        """

    def get_input_style(self) -> str:
        """Get input field stylesheet with DPI-aware sizing."""
        return f"""
            QComboBox, QSpinBox {{
                background-color: {ThemeColors.INPUT_BG};
                border: 1px solid {ThemeColors.BORDER_SECONDARY};
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 13px;
                color: {ThemeColors.TEXT_PRIMARY};
                min-height: 28px;
            }}
            QComboBox:focus, QSpinBox:focus {{
                border-color: {ThemeColors.BORDER_FOCUS};
                outline: none;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 28px;
                padding-right: 4px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {ThemeColors.TEXT_SECONDARY};
                margin-right: 8px;
            }}
        """

    def get_window_style(self) -> str:
        """Get main window stylesheet."""
        return f"""
            QMainWindow {{
                background-color: {ThemeColors.WINDOW_BG};
            }}
            QWidget {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            QTextEdit {{
                background-color: {ThemeColors.INPUT_BG};
                border: 1px solid {ThemeColors.BORDER_SECONDARY};
                border-radius: 8px;
                padding: 10px;
                font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
                font-size: 11px;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
            QScrollBar:vertical {{
                border: none;
                background-color: {ThemeColors.WINDOW_BG};
                width: 12px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: {ThemeColors.BORDER_SECONDARY};
                min-height: 30px;
                border-radius: 6px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {ThemeColors.TEXT_SECONDARY};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """

    def get_checkbox_style(self) -> str:
        """Get checkbox stylesheet."""
        return f"""
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 5px;
                border: 2px solid {ThemeColors.BORDER_SECONDARY};
                background-color: {ThemeColors.INPUT_BG};
            }}
            QCheckBox::indicator:checked {{
                border-color: {ThemeColors.PRIMARY};
                background-color: {ThemeColors.PRIMARY};
            }}
            QCheckBox {{
                font-size: 13px;
                color: {ThemeColors.TEXT_PRIMARY};
            }}
        """


# Global theme manager instance
theme_manager = ThemeManager()
