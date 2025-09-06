#!/usr/bin/env python3
"""Test dynamic virtual controller creation without limits."""

import sys
import os
import asyncio
from unittest.mock import Mock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from input_link.virtual.controller_manager import VirtualControllerManager
from input_link.models import ControllerInputData, ButtonState, ControllerState

async def test_dynamic_controller_creation():
    """Test dynamic controller creation without limits."""
    print("Testing dynamic virtual controller creation...")
    
    # Create manager without limits
    manager = VirtualControllerManager(
        max_controllers=None,  # No limit
        auto_create=True
    )
    
    await manager.start()
    
    try:
        # Test creating controllers 1-8 dynamically
        print(f"Initial controller count: {len(manager.controller_numbers)}")
        
        for controller_num in range(1, 9):
            print(f"\nTesting controller {controller_num}...")
            
            # Create mock input data
            input_data = ControllerInputData(
                controller_number=controller_num,
                controller_id=f"TestController{controller_num}",
                buttons=ButtonState(),
                axes=ControllerState()
            )
            
            # This should auto-create the controller
            success = await manager.update_controller_state(input_data)
            print(f"Controller {controller_num} auto-creation: {'SUCCESS' if success else 'FAILED'}")
            
            # Check if controller exists
            active = manager.is_controller_active(controller_num)
            print(f"Controller {controller_num} active: {active}")
            
            print(f"Current controller numbers: {manager.controller_numbers}")
            print(f"Active controller count: {manager.active_controller_count}")
        
        # Test creating controller with large number (e.g., 15)
        print(f"\nTesting high controller number (15)...")
        input_data = ControllerInputData(
            controller_number=15,
            controller_id="TestController15",
            buttons=ButtonState(),
            axes=ControllerState()
        )
        
        success = await manager.update_controller_state(input_data)
        print(f"Controller 15 auto-creation: {'SUCCESS' if success else 'FAILED'}")
        
        # Final status
        print(f"\n=== FINAL STATUS ===")
        print(f"Total controllers created: {len(manager.controller_numbers)}")
        print(f"Controller numbers: {sorted(manager.controller_numbers)}")
        print(f"Active controllers: {manager.active_controller_count}")
        
        # Get controller info
        controller_info = manager.get_controller_info()
        for info in controller_info:
            print(f"Controller {info['controller_number']}: {info['controller_type']} - Connected: {info['connected']}")
            
    finally:
        await manager.stop()
        print("Manager stopped")

if __name__ == "__main__":
    asyncio.run(test_dynamic_controller_creation())