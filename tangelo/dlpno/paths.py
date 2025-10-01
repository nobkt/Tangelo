# Copyright SandboxAQ 2021-2024.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Path and naming helpers for DLPNO intermediate artifacts.

Design goals:
- Deterministic, collision-free pair identifiers.
- Minimal logic (no filesystem side-effects here).
- Return type is always str for portability across calling layers.
- Formatting stability: zero-pad up to 4 digits; longer indices expand naturally.
"""

from __future__ import annotations

from pathlib import Path

__all__ = [
    "pair_key",
    "pair_cache_dir",
    "run_iteration_dir",
]


def _format_index(idx: int) -> str:
    """Format an orbital (or pair) index with zero padding to at least 4 digits.

    Behavior:
        abs(idx) <= 9999  -> zero-padded to width 4
        abs(idx) >  9999  -> full number (no truncation)
        negative indices  -> prefix '-' retained, padding applied to absolute part

    Examples:
        7      -> '0007'
        12345  -> '12345'
        -2     -> '-0002'
        -12345 -> '-12345'

    Args:
        idx: Orbital index (int).

    Returns:
        str: Formatted index token.
    """
    abs_str = str(abs(idx))
    padded = abs_str.zfill(4) if len(abs_str) < 5 else abs_str
    return f"-{padded}" if idx < 0 else padded


def pair_key(i: int, j: int) -> str:
    """Return a canonical key for an orbital pair (i, j).

    Normalization:
        The ordering is enforced so that the first formatted index corresponds
        to the numerically smaller of (i, j). (i == j) is allowed for now
        (self-pair), and can be restricted in a future validation layer.

    Format:
        'pair_{i_formatted}_{j_formatted}'

    Args:
        i: First orbital index.
        j: Second orbital index.

    Returns:
        str: Canonical pair key (e.g. 'pair_0007_0015').

    Note:
        Negative indices are preserved; they should not appear in typical
        production workflows. If needed, a future validation may reject them.
    """
    a, b = (i, j) if i <= j else (j, i)
    return f"pair_{_format_index(a)}_{_format_index(b)}"


def pair_cache_dir(base: str | Path, i: int, j: int) -> str:
    """Return a directory path (as string) for caching artifacts of pair (i, j).

    Args:
        base: Base directory (string or Path-like). Not created here.
        i: First orbital index.
        j: Second orbital index.

    Returns:
        str: '<base>/pair_xxxx_yyyy'
    """
    return str(Path(base) / pair_key(i, j))


def run_iteration_dir(base: str | Path, iteration: int) -> str:
    """Return the directory path for storing artifacts of a specific iteration.

    Args:
        base: Base directory path or string.
        iteration: Iteration number (must be non-negative).

    Returns:
        str: '<base>/iter_{iteration:03d}'

    Raises:
        ValueError: If iteration is negative.
    """
    if iteration < 0:
        raise ValueError(f"Iteration must be non-negative, got {iteration}")
    return str(Path(base) / f"iter_{iteration:03d}")