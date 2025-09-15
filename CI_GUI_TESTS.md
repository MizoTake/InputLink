# CI GUI Tests Status

## Current State

Currently, GUI tests in CI environment (GitHub Actions) are temporarily disabled due to PySide6/Qt dependency issues on headless Linux runners.

### Error Details
```
ImportError: libEGL.so.1: cannot open shared object file: No such file or directory
```

## Temporary Solution

The CI workflow currently:
1. ✅ Runs all unit tests successfully
2. ✅ Runs non-GUI integration tests
3. ⚠️ Skips GUI integration tests to prevent build failures

## Disabled Test Files

The following test files are currently ignored in CI:

- `tests/integration/test_back_to_main.py`
- `tests/integration/test_controller_scanning.py`
- `tests/integration/test_gui.py`
- `tests/integration/test_gui_functions.py`
- `tests/integration/test_gui_interactions.py`
- `tests/integration/test_receiver_scroll_functionality.py`
- `tests/integration/test_receiver_window.py`
- `tests/integration/test_sender_window.py`
- `tests/integration/test_sender_window_scanning.py`
- `tests/integration/test_ui_button_processing.py`
- `tests/integration/test_ui_layout_analysis.py`

## Future Solutions

### Option 1: Docker with Display Support
```yaml
- name: Setup Display
  run: |
    export DISPLAY=:99
    Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
```

### Option 2: Headless Testing Framework
Implement Qt application factories that work in headless mode:
```python
@pytest.fixture
def qt_app():
    if os.environ.get('CI'):
        app = QCoreApplication([])
    else:
        app = QApplication([])
    yield app
    app.quit()
```

### Option 3: Mock GUI Components
Create mock objects for GUI testing in CI:
```python
if os.environ.get('CI'):
    import unittest.mock
    sys.modules['PySide6.QtWidgets'] = unittest.mock.MagicMock()
```

## Running GUI Tests Locally

To run GUI tests locally:
```bash
# All tests including GUI
pytest tests/ -v

# Only GUI tests
pytest tests/integration/ -v -k "gui"
```

## Test Environment Setup

Local development requires:
- PySide6 with display support
- Physical or virtual display
- Audio system (for pygame)

CI environment provides:
- Xvfb virtual display
- System audio libraries
- EGL/OpenGL libraries