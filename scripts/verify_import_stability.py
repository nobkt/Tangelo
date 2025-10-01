#!/usr/bin/env python3
"""
verify_import_stability.py

目的:
  Tangelo の代表的モジュール群 (特に operators 周辺) を NumPy 2.0 環境で一括インポートし、
  np.product 由来の AttributeError などが発生しないことを検証する。

検証対象:
  - tangelo 直下: __init__ が存在すれば先に import
  - tangelo/toolboxes/operators/*.py の各モジュール
  - 拡張: 他サブパッケージを追加したい場合は PATH_PATTERNS に追記可能

出力:
  - 成功: 各モジュール OK 行 + 最後に SUCCESS メッセージ, exit code 0
  - 失敗: 失敗モジュール一覧と例外要約, exit code 1

使い方:
  PYTHONPATH=. python scripts/verify_import_stability.py
"""

from __future__ import annotations
import sys
import traceback
from pathlib import Path
import importlib.util
import importlib
import types

# 走査ルート
ROOT = Path(__file__).resolve().parents[1]  # リポジトリルート想定
PKG_ROOT = ROOT / "tangelo"

# 追加で走査したいパターン（必要なら拡張）
PATH_PATTERNS = [
    PKG_ROOT / "toolboxes" / "operators"
]

def discover_modules():
    modules = []

    # ルートパッケージ (tangelo) 自体
    if (PKG_ROOT / "__init__.py").exists():
        modules.append("tangelo")

    for directory in PATH_PATTERNS:
        if not directory.exists():
            continue
        for pyfile in sorted(directory.glob("*.py")):
            if pyfile.name.startswith("_"):
                continue
            rel = pyfile.relative_to(ROOT)
            # パス -> モジュール名変換
            parts = list(rel.with_suffix("").parts)
            mod_name = ".".join(parts)
            modules.append(mod_name)

    return modules

def import_module(name: str):
    try:
        module = importlib.import_module(name)
        return True, module, None
    except Exception as e:
        return False, None, e

def main() -> int:
    if not PKG_ROOT.exists():
        print(f"[ERROR] tangelo パッケージが見つかりません: {PKG_ROOT}")
        return 2

    targets = discover_modules()
    if not targets:
        print("[WARN] 対象モジュールが見つかりませんでした。 (空検証: PASS とみなす)")
        return 0

    failures = []
    for mod_name in targets:
        ok, module, err = import_module(mod_name)
        if ok:
            print(f"[OK] {mod_name}")
        else:
            tb = "".join(traceback.format_exception_only(type(err), err)).strip()
            print(f"[FAIL] {mod_name} -> {tb}")
            failures.append((mod_name, err, tb))

    # 失敗詳細
    if failures:
        print("\n=== FAILURE SUMMARY ===")
        for mod, err, tb in failures:
            print(f"Module: {mod}")
            print(f"Exception: {err!r}")
            # 重要キーワードハイライト
            low = str(err).lower()
            if "np.product" in low or "attributeerror" in low:
                print("  -> POSSIBLE REGRESSION (np.product or AttributeError detected)")
            print("---")
        return 1

    print("SUCCESS: All target modules imported without np.product regressions.")
    return 0

if __name__ == "__main__":
    sys.exit(main())