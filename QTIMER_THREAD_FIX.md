# QTimer Thread Context Fix

## Problem Description

After stopping the Sender in the GUI, the controller input preview was not working correctly. The preview polling timer was being created and stopped from the wrong thread context, causing Qt errors:

```
QObject::killTimer: Timers cannot be stopped from another thread
```

## Root Cause

Qt objects (including QTimer) must be created and managed in the thread that has a Qt event loop. The application structure was:

- **Main Thread**: Has Qt event loop (GUI)
- **AsyncWorker Thread**: Has asyncio event loop (for async operations)

The problem occurred because:

1. `_start_preview_polling()` was called from AsyncWorker thread, creating QTimer in wrong context
2. `_do_start_sender()` was stopping the timer from AsyncWorker thread
3. QTimer requires Qt event loop, which only exists in the main thread

## Solution

Moved all QTimer operations to the main GUI thread using Qt's Signal/Slot mechanism:

### Changes Made

#### 1. Added New Signal (`src/input_link/gui/application.py:32`)

```python
class AsyncWorker(QThread):
    # ... existing signals ...
    restart_preview_requested = Signal(list)  # Signal to restart preview in main thread
    stop_preview_requested = Signal()  # Signal to stop preview in main thread
```

#### 2. Modified Timer Start Request (`src/input_link/gui/application.py:164-185`)

Changed from direct method call to signal emission:

```python
def _sender_status_callback(self, status: str):
    # ... existing code ...

    # Restart preview polling when sender stops
    if status == "stopped":
        self.logger.info("Sender stopped, requesting preview restart in main thread")
        if self.sender_app and self.sender_app.controller_manager:
            controllers = self.sender_app.controller_manager.get_connected_controllers()
            # Emit signal to restart preview in main thread (where QTimer works)
            self.restart_preview_requested.emit(controllers)
```

#### 3. Modified Timer Stop Request (`src/input_link/gui/application.py:284-289`)

Changed from direct timer.stop() to signal emission:

```python
def _do_start_sender(self):
    """Actual sender startup logic."""
    # Stop preview polling while sender is running to avoid joystick conflicts
    # Request stop from main thread (where QTimer lives)
    self.stop_preview_requested.emit()
    self.logger.info("Requested preview polling stop (sender starting)")
```

#### 4. Added Main Thread Slots (`src/input_link/gui/application.py:868-888`)

Created slots that run in main thread to handle timer operations:

```python
@Slot(list)
def _on_restart_preview_requested(self, controllers):
    """Handle preview restart request from worker thread.

    This runs in the main GUI thread, where QTimer can function properly.
    """
    self.async_worker._start_preview_polling(controllers)

@Slot()
def _on_stop_preview_requested(self):
    """Handle preview stop request from worker thread.

    This runs in the main GUI thread, where QTimer can be stopped properly.
    """
    if self.async_worker._preview_timer:
        self.async_worker._preview_timer.stop()
```

#### 5. Connected Signals (`src/input_link/gui/application.py:694-695`)

```python
self.async_worker.restart_preview_requested.connect(self._on_restart_preview_requested)
self.async_worker.stop_preview_requested.connect(self._on_stop_preview_requested)
```

## How It Works

### Before (BROKEN):
```
AsyncWorker Thread --> QTimer.start()  ❌ Wrong thread!
AsyncWorker Thread --> QTimer.stop()   ❌ Wrong thread!
```

### After (FIXED):
```
AsyncWorker Thread --> emit start_timer_requested signal
                   --> Main Thread receives signal
                   --> Main Thread creates/starts QTimer ✅

AsyncWorker Thread --> emit stop_timer_requested signal
                   --> Main Thread receives signal
                   --> Main Thread stops QTimer ✅
```

## Testing

### Unit Tests

Existing tests pass:
```bash
python -m pytest tests/unit/test_sender_stop_preview.py -v
# Result: 2 passed
```

### Thread Context Test

Created `test_timer_thread_fix.py` to verify correct thread context:

```bash
python test_timer_thread_fix.py
```

Expected output:
- Timer created in main thread ✅
- Timer ticks successfully ✅
- Timer stopped in main thread ✅
- No Qt thread errors ✅

## Verification Steps for User

1. Start the GUI application
2. Navigate to Sender window
3. Scan for controllers
4. Click "Start Capturing"
5. Verify inputs work on Receiver
6. Click "Stop Capturing"
7. **CRITICAL TEST**: After stop, check if preview shows controller inputs when you press buttons
8. Click "Start Capturing" again
9. Verify no Qt errors in console
10. Verify inputs still work on Receiver

## Expected Behavior

After stopping Sender:
- ✅ Preview panel should continue showing controller
- ✅ Preview should update when buttons are pressed
- ✅ No Qt thread errors in console
- ✅ When restarting Sender, preview stops cleanly
- ✅ Receiver correctly receives inputs after restart

## Files Modified

1. `src/input_link/gui/application.py`:
   - Added `stop_preview_requested` signal
   - Modified `_do_start_sender()` to emit signal
   - Modified `_sender_status_callback()` to emit signal
   - Added `_on_stop_preview_requested()` slot
   - Updated `_on_restart_preview_requested()` implementation
   - Connected new signal in `_setup_worker()`

## Related Context

This fix is part of a larger effort to maintain pygame resources in GUI mode:

1. Added `cleanup_controller_manager` flag to SenderApp
2. Added `cleanup_joysticks` flag to InputCaptureEngine
3. Moved status callback before controller manager cleanup
4. Fixed QTimer thread context (this fix)

All changes ensure controller input preview works correctly after Sender stop/restart cycles.
