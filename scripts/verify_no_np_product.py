#!/usr/bin/env python3
"""
verify_no_np_product.py

目的:
  Tangelo リポジトリ内 (tangelo/ 配下) に `np.product` 呼び出しが残っていないことを検証する。

使い方:
  1. リポジトリルートで実行:
     python verify_no_np_product.py
  2. CI に組み込む場合は失敗時の exit code=1 をトリガにできる。

設計方針:
  - 単純なテキスト検索。バリアント (例: numpy.product) も検出。
  - サードパーティ依存不要。
  - バイナリ/巨大ファイルは拡張子フィルタでスキップ。
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

# 走査対象のトップディレクトリ
TARGET_DIR = Path("tangelo")

# 読み込むテキストファイル拡張子（必要なら追加）
TEXT_EXTENSIONS = {
    ".py", ".pyi", ".txt", ".md", ".rst", ".cfg", ".ini", ".toml",
    ".yml", ".yaml", ".json"
}

SEARCH_TOKENS = [
    "np.product",      # 通常ケース
    "numpy.product",   # 明示的 numpy 参照ケース
]

def is_text_file(path: Path) -> bool:
    if path.suffix in TEXT_EXTENSIONS:
        return True
    # 拡張子不明ファイルは軽量判定（先頭数百バイトに NULL が無いか）
    try:
        with path.open("rb") as f:
            chunk = f.read(512)
        return b"\x00" not in chunk
    except Exception:
        return False

def scan() -> list[tuple[Path, int, str]]:
    findings: list[tuple[Path, int, str]] = []
    if not TARGET_DIR.exists():
        print(f"ERROR: Target directory '{TARGET_DIR}' not found. リポジトリルートで実行してください。", file=sys.stderr)
        sys.exit(2)
    for root, _, files in os.walk(TARGET_DIR):
        for name in files:
            path = Path(root) / name
            if not is_text_file(path):
                continue
            try:
                with path.open("r", encoding="utf-8", errors="replace") as fh:
                    for lineno, line in enumerate(fh, start=1):
                        # トークンのいずれかが行に含まれるか
                        if any(token in line for token in SEARCH_TOKENS):
                            findings.append((path, lineno, line.rstrip()))
            except Exception as e:
                print(f"WARNING: Could not read {path}: {e}", file=sys.stderr)
    return findings

def main() -> int:
    findings = scan()
    if findings:
        print("FAIL: Found deprecated 'np.product' usages:")
        for path, lineno, text in findings:
            print(f"  {path}:{lineno}: {text}")
        print("\n修正してください: 'np.product' → 'np.prod'")
        return 1
    else:
        print("OK: no occurrences of np.product found.")
        return 0

if __name__ == "__main__":
    sys.exit(main())