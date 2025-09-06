#!/usr/bin/env python3
"""Detailed UI layout analysis for potential overlapping issues."""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from input_link.gui.application import InputLinkApplication

def analyze_ui_layout():
    """Analyze UI layout for potential overlapping and sizing issues."""
    print("Starting detailed UI layout analysis...")
    
    app = InputLinkApplication([])
    
    layout_issues = []
    recommendations = []
    
    print("\n=== WINDOW SIZE ANALYSIS ===")
    
    # Get all window sizes
    main_size = app.main_window.size()
    sender_size = app.sender_window.size()  
    receiver_size = app.receiver_window.size()
    stack_size = app.stacked_widget.size()
    
    print(f"QStackedWidget size: {stack_size.width()} x {stack_size.height()}")
    print(f"MainWindow size: {main_size.width()} x {main_size.height()}")
    print(f"SenderWindow size: {sender_size.width()} x {sender_size.height()}")
    print(f"ReceiverWindow size: {receiver_size.width()} x {receiver_size.height()}")
    
    # Check minimum sizes
    main_min = app.main_window.minimumSize()
    sender_min = app.sender_window.minimumSize() 
    receiver_min = app.receiver_window.minimumSize()
    
    print(f"\nMinimum sizes:")
    print(f"MainWindow min: {main_min.width()} x {main_min.height()}")
    print(f"SenderWindow min: {sender_min.width()} x {sender_min.height()}")
    print(f"ReceiverWindow min: {receiver_min.width()} x {receiver_min.height()}")
    
    print(f"\n=== CONTENT ANALYSIS ===")
    
    # Test each window for content overflow
    windows_to_test = [
        ("MainWindow", app.main_window),
        ("SenderWindow", app.sender_window),
        ("ReceiverWindow", app.receiver_window)
    ]
    
    for window_name, window in windows_to_test:
        print(f"\n--- {window_name} Analysis ---")
        app.stacked_widget.setCurrentWidget(window)
        
        # Get central widget and its layout
        central_widget = window.centralWidget()
        if central_widget:
            central_size = central_widget.size()
            print(f"Central widget size: {central_size.width()} x {central_size.height()}")
            
            # Check layout margins and spacing
            layout = central_widget.layout()
            if layout:
                margins = layout.contentsMargins()
                spacing = layout.spacing()
                print(f"Layout margins: {margins.left()}, {margins.top()}, {margins.right()}, {margins.bottom()}")
                print(f"Layout spacing: {spacing}")
                
                # Calculate total content height needed
                total_height = margins.top() + margins.bottom()
                widget_count = layout.count()
                if widget_count > 0:
                    total_height += spacing * (widget_count - 1)
                    
                print(f"Widget count in layout: {widget_count}")
                print(f"Base layout height needed: {total_height}")
        
        # Test scrollability if content overflows
        window_height = window.size().height()
        if central_widget and central_widget.size().height() > window_height:
            layout_issues.append(f"{window_name}: Content height ({central_widget.size().height()}) exceeds window height ({window_height})")
            recommendations.append(f"{window_name}: Consider adding scroll area or reducing content")
    
    print(f"\n=== RECEIVER WINDOW SPECIFIC ANALYSIS ===")
    
    # Special analysis for ReceiverWindow which has dynamic controllers
    app.stacked_widget.setCurrentWidget(app.receiver_window)
    
    # Count virtual controller cards
    controller_card_count = len(app.receiver_window.virtual_controller_cards)
    print(f"Current virtual controller cards: {controller_card_count}")
    
    # Estimate space needed for different controller counts
    card_height = 75  # Base height per card
    card_spacing = 8  # Spacing between cards
    
    for count in [4, 6, 8, 12, 16]:
        estimated_height = count * (card_height + card_spacing)
        print(f"Space needed for {count} controllers: ~{estimated_height}px")
        
        if estimated_height > 400:  # Reasonable viewport height
            layout_issues.append(f"ReceiverWindow: {count} controllers would need {estimated_height}px (may cause overflow)")
            if count == 8:
                recommendations.append("ReceiverWindow: Consider scroll area for 8+ controllers")
            elif count >= 12:
                recommendations.append(f"ReceiverWindow: Definitely needs scroll area for {count}+ controllers")
    
    print(f"\n=== RESPONSIVE BEHAVIOR ANALYSIS ===")
    
    # Test different window sizes
    test_sizes = [
        (400, 600, "Minimum"),
        (480, 650, "Default"), 
        (520, 700, "Comfortable"),
        (600, 800, "Large")
    ]
    
    for width, height, label in test_sizes:
        print(f"\n--- Testing {label} size ({width}x{height}) ---")
        app.stacked_widget.resize(width, height)
        
        # Check if content fits in each window
        for window_name, window in windows_to_test:
            app.stacked_widget.setCurrentWidget(window)
            
            # Force layout update
            window.updateGeometry()
            app.processEvents()
            
            # Check if window content is properly visible
            central = window.centralWidget()
            if central:
                if central.size().height() > height - 50:  # Account for window decorations
                    layout_issues.append(f"{window_name} at {width}x{height}: Content may be cut off")
    
    print(f"\n=== WIDGET OVERLAP DETECTION ===")
    
    # Check for potential widget overlaps in each window
    for window_name, window in windows_to_test:
        print(f"\n--- Checking {window_name} for overlaps ---")
        app.stacked_widget.setCurrentWidget(window)
        
        central = window.centralWidget()
        if central and central.layout():
            # Check if layout has proper spacing
            layout = central.layout()
            
            # Simple overlap detection based on layout properties
            if layout.spacing() < 5:
                layout_issues.append(f"{window_name}: Layout spacing too small ({layout.spacing()}px)")
            
            # Check margins
            margins = layout.contentsMargins()
            if any(m < 10 for m in [margins.left(), margins.top(), margins.right(), margins.bottom()]):
                recommendations.append(f"{window_name}: Consider increasing layout margins for better visual breathing room")
    
    print(f"\n=== LAYOUT RECOMMENDATIONS ===")
    
    # Window size recommendations
    if receiver_size.height() < 700:
        recommendations.append("ReceiverWindow: Consider minimum height of 700px for better content display")
    
    if sender_size.height() < 650:
        recommendations.append("SenderWindow: Current height seems appropriate for content")
        
    # Content organization recommendations  
    recommendations.append("All windows: Consider grouping related controls for better UX")
    recommendations.append("ReceiverWindow: Implement scroll area for controller cards section")
    
    print(f"\n=== FINAL ANALYSIS RESULTS ===")
    print(f"Layout issues found: {len(layout_issues)}")
    print(f"Recommendations: {len(recommendations)}")
    
    if layout_issues:
        print(f"\n--- ISSUES FOUND ---")
        for i, issue in enumerate(layout_issues, 1):
            print(f"{i}. {issue}")
    else:
        print("\n[PASS] No critical layout issues detected!")
    
    if recommendations:
        print(f"\n--- RECOMMENDATIONS ---")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
    
    # Auto-close
    def close_app():
        print(f"\nClosing layout analysis...")
        app.quit()
    
    timer = QTimer()
    timer.timeout.connect(close_app)
    timer.start(2000)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(analyze_ui_layout())