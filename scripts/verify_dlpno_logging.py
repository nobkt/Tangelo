#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verification script for tangelo.dlpno.logging_utils.

Checks:
  1. Import side-effect silence.
  2. init_dlpno_logger() returns a logger with expected name & level.
  3. Repeated calls with same name do not duplicate handlers.
  4. json=True attaches a JSON formatter producing parseable JSON.
  5. Log level adjustments are effective.
  6. Separate logger names stay independent.
  7. Summary with pass/fail + optional JSON output.

Exit code:
  0 = all checks passed
  1 = any failure
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json as _json
import logging
import sys
from typing import Any, Dict

SUMMARY: Dict[str, Any] = {
    "module_import": False,
    "side_effect_stdout": "",
    "side_effect_stderr": "",
    "base_logger": {},
    "json_logger": {},
    "handler_duplication": {},
    "level_change": {},
    "independent_loggers": {},
    "overall_pass": False,
    "fail_reasons": [],
}

FAIL = SUMMARY["fail_reasons"]


def fail(msg: str):
    FAIL.append(msg)


def import_module():
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        try:
            mod = importlib.import_module("tangelo.dlpno.logging_utils")
            SUMMARY["module_import"] = True
        except Exception as exc:  # noqa
            fail(f"Import failure: {exc}")
            return None
    SUMMARY["side_effect_stdout"] = buf_out.getvalue()
    SUMMARY["side_effect_stderr"] = buf_err.getvalue()
    if SUMMARY["side_effect_stdout"].strip():
        fail("Unexpected stdout on import.")
    if SUMMARY["side_effect_stderr"].strip():
        fail("Unexpected stderr on import.")
    return mod


def capture_logs(logger: logging.Logger, level: int, emit_func) -> str:
    """Attach a temporary StreamHandler to capture exactly the emitted message(s)."""
    stream = io.StringIO()
    temp = logging.StreamHandler(stream)
    temp.setLevel(level)
    logger.addHandler(temp)
    try:
        emit_func()
    finally:
        logger.removeHandler(temp)
    return stream.getvalue().strip()


def test_basic_logger(mod):
    init_fn = getattr(mod, "init_dlpno_logger", None)
    if init_fn is None:
        fail("init_dlpno_logger not found.")
        return

    logger = init_fn(name="dlpno_test_basic", level=logging.INFO, json=False)
    info_before = {
        "name": logger.name,
        "level": logger.level,
        "handlers": len(logger.handlers),
    }
    if logger.name != "dlpno_test_basic":
        fail("Logger name mismatch.")
    if logger.level != logging.INFO:
        fail("Logger level mismatch (expected INFO).")

    out = capture_logs(logger, logging.INFO, lambda: logger.info("hello-basic"))
    SUMMARY["base_logger"] = {
        "initial": info_before,
        "emitted_line": out,
        "handlers_after_capture": len(logger.handlers),
    }
    if "hello-basic" not in out:
        fail("Did not capture expected basic log line.")


def test_handler_duplication(mod):
    init_fn = mod.init_dlpno_logger
    l1 = init_fn(name="dlpno_test_dup", level=logging.DEBUG)
    h1 = len(l1.handlers)
    l2 = init_fn(name="dlpno_test_dup", level=logging.DEBUG)
    h2 = len(l2.handlers)
    SUMMARY["handler_duplication"] = {
        "first_handlers": h1,
        "second_handlers": h2,
        "same_object": l1 is l2
    }
    if h2 != h1:
        fail("Handler duplication detected (handler count changed).")


def test_json_logger(mod):
    init_fn = mod.init_dlpno_logger
    logger = init_fn(name="dlpno_test_json", level=logging.INFO, json=True)

    # 既存ハンドラ取得
    original_handlers = logger.handlers[:]
    if not original_handlers:
        fail("JSON logger has no handlers.")
        return

    # 1つ目のハンドラのフォーマッタを流用
    json_formatter = original_handlers[0].formatter

    # 既存ハンドラを一時的に外し、StringIO を付与
    for h in original_handlers:
        logger.removeHandler(h)

    stream = io.StringIO()
    temp_handler = logging.StreamHandler(stream)
    temp_handler.setFormatter(json_formatter)
    logger.addHandler(temp_handler)

    logger.info("json-line", extra={"phase": "test"})
    temp_handler.flush()
    raw = stream.getvalue().strip()

    # 復元
    logger.removeHandler(temp_handler)
    for h in original_handlers:
        logger.addHandler(h)

    SUMMARY["json_logger"] = {"raw_output": raw}

    # JSON パース
    try:
        parsed = _json.loads(raw)
    except Exception as exc:  # noqa
        fail(f"JSON logger output not parseable: {exc}")
        return

    required = {"time", "level", "name", "msg"}
    missing = required - set(parsed.keys())
    if missing:
        fail(f"JSON logger output missing keys: {missing}")
    if parsed.get("msg") != "json-line":
        fail("JSON logger 'msg' field mismatch.")


def test_level_change(mod):
    init_fn = mod.init_dlpno_logger
    logger = init_fn(name="dlpno_test_level", level=logging.WARNING)
    info_out = capture_logs(logger, logging.INFO, lambda: logger.info("hidden-info"))
    warn_out = capture_logs(logger, logging.WARNING, lambda: logger.warning("warn-visible"))
    SUMMARY["level_change"] = {
        "info_out_empty": info_out == "",
        "warn_out": warn_out
    }
    if info_out != "":
        fail("INFO message appeared despite WARNING level.")
    if "warn-visible" not in warn_out:
        fail("WARNING message missing at WARNING level.")


def test_independent_loggers(mod):
    init_fn = mod.init_dlpno_logger
    l1 = init_fn(name="dlpno_indep_A", level=logging.INFO)
    l2 = init_fn(name="dlpno_indep_B", level=logging.INFO)
    SUMMARY["independent_loggers"] = {
        "same_object": l1 is l2,
        "l1_handlers": len(l1.handlers),
        "l2_handlers": len(l2.handlers)
    }
    if l1 is l2:
        fail("Distinct logger names returned identical logger object.")


def main():
    parser = argparse.ArgumentParser(description="Verify DLPNO logging utilities.")
    parser.add_argument("--json-out", type=str, default=None, help="Write JSON summary to file.")
    parser.add_argument("--verbose", action="store_true", help="Verbose output.")
    args = parser.parse_args()

    mod = import_module()
    if mod:
        test_basic_logger(mod)
        test_handler_duplication(mod)
        test_json_logger(mod)
        test_level_change(mod)
        test_independent_loggers(mod)

    SUMMARY["overall_pass"] = len(FAIL) == 0

    if args.verbose:
        print("=== DLPNO LOGGING VERIFICATION REPORT ===")
        for k, v in SUMMARY.items():
            if k in {"side_effect_stdout", "side_effect_stderr"} and not v:
                continue
            print(f"{k}: {v}")
        print("=========================================")
    else:
        status = "PASS" if SUMMARY["overall_pass"] else "FAIL"
        print(f"[logging_utils] Verification {status}. Fail reasons: {FAIL}")

    if args.json_out:
        try:
            with open(args.json_out, "w", encoding="utf-8") as f:
                _json.dump(SUMMARY, f, indent=2)
        except Exception as exc:  # noqa
            print(f"Could not write JSON summary: {exc}", file=sys.stderr)

    sys.exit(0 if SUMMARY["overall_pass"] else 1)


if __name__ == "__main__":
    main()