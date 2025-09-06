#!/usr/bin/env python3
"""Simple GUI test to verify PySide6 is working correctly."""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Qt

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Input Link - GUI Test")
        self.setGeometry(100, 100, 400, 300)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add widgets
        label = QLabel("Input Link GUI Test")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        
        button = QPushButton("Click to Test")
        button.clicked.connect(self.on_button_click)
        
        layout.addWidget(label)
        layout.addWidget(button)
        
        print("TestWindow created successfully")
        
    def on_button_click(self):
        print("Button clicked!")
        
def main():
    print("Starting PySide6 GUI test...")
    
    app = QApplication(sys.argv)
    window = TestWindow()
    
    print("Showing window...")
    window.show()
    window.raise_()
    window.activateWindow()
    
    print(f"Window visible: {window.isVisible()}")
    print(f"Window geometry: {window.geometry()}")
    print("GUI test is running. Close the window to exit.")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())