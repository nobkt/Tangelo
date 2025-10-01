#!/usr/bin/env python3
"""
verify_z2_tapering_tests.py

目的:
  z2_tapering 関連テスト (tangelo/toolboxes/operators/tests/test_z2_tapering.py) が
  np.product -> np.prod 置換後に AttributeError 等を起こさず通過するか確認する。

実装方針:
  - pytest を Python API 経由で実行 (外部プラグイン非依存)
  - 成功 / 失敗 / エラー / スキップ件数を自前集計
  - 失敗・エラーの longrepr (トレース) に 'np.product' が含まれていないか確認
  - テストファイルが存在しない場合は SKIP (exit code 0)

終了コード:
  0: テストファイルなし (SKIP) または 全テスト成功 (np.product 再出現なし)
  1: テスト失敗 or エラーあり, もしくは 'np.product' が再出現
  2: 実行内部エラー (pytest 起動不能など)

使い方:
  PYTHONPATH=. python scripts/verify_z2_tapering_tests.py
"""

from __future__ import annotations
import sys
from pathlib import Path
import traceback
import io
import contextlib

TEST_FILE = Path("tangelo/toolboxes/operators/tests/test_z2_tapering.py")

class TestResultCollector:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.errors = []
        self.skipped = []
        self.xfailed = []
        self.xpassed = []
        self.product_mentions = []

    # pytest フック: 各テスト実行後に呼ばれる
    def pytest_runtest_logreport(self, report):
        if report.when != "call":
            return
        # report.outcome: "passed" | "failed"
        if report.outcome == "passed":
            self.passed.append(report.nodeid)
        elif report.outcome == "failed":
            # longrepr 解析
            lr = getattr(report, "longrepr", "")
            lr_text = str(lr)
            if "np.product" in lr_text:
                self.product_mentions.append(report.nodeid)
            # エラーか失敗かは longrepr の型で大きく変わるが、ここでは outcome=failed を一括処理
            # 例外クラス情報が含まれていれば errors 群に寄せてもよいが、簡潔化のため failed へ
            self.failed.append(report.nodeid)

    # skip や xfail を収集したい場合は pytest_report_teststatus を利用
    def pytest_report_teststatus(self, report, config):
        if report.when == "setup" and report.skipped:
            self.skipped.append(report.nodeid)
        if report.when == "call" and getattr(report, "wasxfail", None):
            if report.outcome == "skipped":
                self.xfailed.append(report.nodeid)
            elif report.outcome == "passed":
                self.xpassed.append(report.nodeid)
        return None


def run_pytest(target: Path, collector: TestResultCollector) -> int:
    import pytest
    # 余計な出力を抑えつつ -q 相当で回す
    args = [str(target), "-q", "--maxfail=50"]
    # stdout/stderr キャプチャ（必要なら表示可能）
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        code = pytest.main(args, plugins=[collector])
    # 必要ならデバッグ用:
    # print(buf_out.getvalue())
    # print(buf_err.getvalue(), file=sys.stderr)
    return code


def main() -> int:
    if not TEST_FILE.exists():
        print(f"[SKIP] Test file not found: {TEST_FILE} (tapering tests not present).")
        return 0

    collector = TestResultCollector()
    try:
        exit_code = run_pytest(TEST_FILE, collector)
    except Exception as e:
        print("[ERROR] Failed to invoke pytest.", file=sys.stderr)
        traceback.print_exc()
        return 2

    # サマリ
    total_run = len(collector.passed) + len(collector.failed)
    print(f"[SUMMARY] run={total_run} passed={len(collector.passed)} failed={len(collector.failed)} "
          f"skipped={len(collector.skipped)} xfailed={len(collector.xfailed)} xpassed={len(collector.xpassed)}")

    if collector.product_mentions:
        print("[FAIL] 'np.product' appeared in traceback for tests:")
        for nodeid in collector.product_mentions:
            print(f"  - {nodeid}")

    # 判定:
    # 1) pytest の exit code が 0 であること
    # 2) failed=0 であること
    # 3) np.product 再出現なし
    if exit_code == 0 and not collector.failed and not collector.product_mentions:
        print("[SUCCESS] z2_tapering tests passed (no np.product regressions).")
        return 0
    else:
        print("[FAIL] z2_tapering test suite not clean.")
        if exit_code != 0:
            print(f"  pytest exit code: {exit_code}")
        if collector.failed:
            print("  Failed tests:")
            for nodeid in collector.failed:
                print(f"    - {nodeid}")
        return 1


if __name__ == "__main__":
    sys.exit(main())