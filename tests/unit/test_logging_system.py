import logging
from pathlib import Path

import pytest

from input_link.core.logging_system import (
    ContextLogger,
    InputLinkLogger,
    LogLevel,
    get_logger,
    setup_application_logging,
)
from input_link.models import ConfigModel, ReceiverConfig, SenderConfig


def test_get_logger_without_config_no_file_handler(capsys):
    logger = get_logger(name="unit.logger.no_file", config=None, level=LogLevel.INFO)
    # No FileHandler should be present
    assert not any(isinstance(h, logging.FileHandler) for h in logger.logger.handlers)
    logger.info("hello world")
    out, err = capsys.readouterr()
    assert "hello world" in out
    assert "unit.logger.no_file" in out


def test_get_logger_with_config_creates_file(tmp_path, monkeypatch):
    # Redirect home to tmp to avoid touching real user home
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    cfg = ConfigModel(
        sender_config=SenderConfig(receiver_host="127.0.0.1"),
        receiver_config=ReceiverConfig(),
    )
    logger = get_logger(name="unit.logger.file", config=cfg, level=LogLevel.INFO)
    logger.info("file target test")

    log_path = tmp_path / ".input-link" / "logs" / "unit.logger.file.log"
    assert log_path.exists(), f"Expected log file at {log_path}"
    content = log_path.read_text(encoding="utf-8")
    assert "file target test" in content


def test_log_callback_receives_formatted_message():
    calls = []

    def cb(level: str, msg: str):
        calls.append((level, msg))

    logger = InputLinkLogger(name="cb.test", log_callback=cb, level=LogLevel.DEBUG)
    logger.warning("hello {user}", user="Alice")

    assert calls, "callback not invoked"
    level, msg = calls[-1]
    assert level == "warning"
    assert msg == "hello Alice"


def test_message_format_fallback_on_missing_keys():
    calls = []

    def cb(level: str, msg: str):
        calls.append((level, msg))

    logger = InputLinkLogger(name="fmt.test", log_callback=cb)
    # Provide partial kwargs to trigger fallback path
    logger.info("Hello {user} {id}", user="Bob")
    _, msg = calls[-1]
    assert "Context:" in msg
    assert "Bob" in msg


def test_exception_logs_traceback_in_message():
    calls = []

    def cb(level: str, msg: str):
        calls.append((level, msg))

    logger = InputLinkLogger(name="exc.test", log_callback=cb)
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("boom")

    _, msg = calls[-1]
    assert "Traceback:" in msg
    assert "ZeroDivisionError" in msg


def test_context_logger_injects_context_values():
    calls = []

    def cb(level: str, msg: str):
        calls.append((level, msg))

    base = InputLinkLogger(name="ctx.test", log_callback=cb)
    ctx: ContextLogger = base.add_context(session="A")
    ctx.info("Session {session}")

    _, msg = calls[-1]
    assert msg.endswith("Session A") or "Session A" in msg


def test_setup_application_logging_verbose_sets_debug_level():
    logger = setup_application_logging(app_name="sender", config=None, verbose=True)
    assert logger.logger.level == LogLevel.DEBUG.value

